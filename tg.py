# -*- coding: utf-8 -*-
"""Telegram Bot API uchun yupqa mijoz (faqat `requests`). Token hech qachon xatolik/log matniga tushmaydi."""
import json
import logging
import time

import requests

from config import cfg

log = logging.getLogger("tilakino.tg")
sleep = time.sleep


class TgError(Exception):
    def __init__(self, code, description, retry_after=0):
        super().__init__(f"{code}: {description}")
        self.code = code
        self.description = description
        self.retry_after = retry_after

    @property
    def blocked(self):
        return self.code == 403


def _post(url, data, timeout=20):  # testlarda almashtiriladi
    return requests.post(url, data=data, timeout=timeout)


def call(method, _retry=True, **params):
    url = f"https://api.telegram.org/bot{cfg.token}/{method}"
    data = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in params.items() if v is not None}
    try:
        r = _post(url, data)
    except requests.RequestException:
        # requests xatosi URL (ya'ni token) ni o'z ichiga oladi, shuning uchun umumiy xabar beramiz
        raise TgError(0, "network error") from None
    try:
        j = r.json()
    except ValueError:
        raise TgError(getattr(r, "status_code", 0), "invalid response") from None
    if not j.get("ok"):
        err = TgError(j.get("error_code", 0), j.get("description", ""), (j.get("parameters") or {}).get("retry_after", 0))
        if err.code == 429 and _retry and 0 < err.retry_after <= 5:
            sleep(err.retry_after)
            return call(method, _retry=False, **params)
        raise err
    return j["result"]


def send_message(chat_id, text, reply_markup=None):
    return call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup,
                disable_web_page_preview=True)


def send_photo(chat_id, photo, caption=None, reply_markup=None):
    return call("sendPhoto", chat_id=chat_id, photo=photo, caption=caption, parse_mode="HTML",
                reply_markup=reply_markup)


def send_animation(chat_id, animation, caption=None, reply_markup=None):
    """Yuborilgan GIF/animatsiyani Telegram chatiga yuboradi."""
    return call("sendAnimation", chat_id=chat_id, animation=animation, caption=caption, parse_mode="HTML",
                reply_markup=reply_markup)

def send_video(chat_id, video, caption=None, reply_markup=None, protect=False):
    return call("sendVideo", chat_id=chat_id, video=video, caption=caption, parse_mode="HTML",
                reply_markup=reply_markup, protect_content=True if protect else None, supports_streaming=True)


def send_document(chat_id, doc, caption=None, reply_markup=None, protect=False):
    return call("sendDocument", chat_id=chat_id, document=doc, caption=caption, parse_mode="HTML",
                reply_markup=reply_markup, protect_content=True if protect else None)


def edit_text(chat_id, message_id, text, reply_markup=None):
    return call("editMessageText", chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML",
                reply_markup=reply_markup, disable_web_page_preview=True)


def edit_caption(chat_id, message_id, caption, reply_markup=None):
    return call("editMessageCaption", chat_id=chat_id, message_id=message_id, caption=caption,
                parse_mode="HTML", reply_markup=reply_markup)


def edit_markup(chat_id, message_id, reply_markup=None):
    return call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id,
                reply_markup=reply_markup or {"inline_keyboard": []})


def delete_message(chat_id, message_id):
    return call("deleteMessage", chat_id=chat_id, message_id=message_id)


def answer_callback(cb_id, text=None, alert=False):
    return call("answerCallbackQuery", callback_query_id=cb_id, text=text, show_alert=True if alert else None)


def chat_action(chat_id, action="typing"):
    return call("sendChatAction", chat_id=chat_id, action=action)


def copy_message(chat_id, from_chat, message_id):
    return call("copyMessage", chat_id=chat_id, from_chat_id=from_chat, message_id=message_id)


def set_webhook(url, secret):
    return call("setWebhook", url=url, secret_token=secret, allowed_updates=["message", "callback_query"],
                drop_pending_updates=False)


def get_file(file_id):
    return call("getFile", file_id=file_id)


def download_file(path):
    r = requests.get(f"https://api.telegram.org/file/bot{cfg.token}/{path}", timeout=20)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "application/octet-stream")
