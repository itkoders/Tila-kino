# -*- coding: utf-8 -*-
"""Telegram interfeys yordamchilari: tugmalar, xabarni joyida yangilash, animatsiyalar."""
import html
import logging
import time

import services as sv
import tg
from config import cfg
from i18n import MENU_KEYS, t

log = logging.getLogger("tilakino.ui")
esc = html.escape
sleep = time.sleep  # testlarda almashtiriladi

PER_PAGE = 8
SPINNER = ["▱▱▱▱▱", "▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]


def _btn(text, data):
    if data.startswith("http"):
        return {"text": text, "url": data}
    return {"text": text, "callback_data": data[:64]}


def ikb(rows):
    """rows: [[(matn, callback_data yoki https://url), ...], ...]"""
    out = [[_btn(a, b) for a, b in row if a] for row in rows]
    return {"inline_keyboard": [r for r in out if r]}


def main_menu(lg):
    ks = [t(lg, k) for k in MENU_KEYS]
    rows = [ks[0:2], ks[2:4], ks[4:6], ks[6:7], ks[7:8]]
    return {"keyboard": [[{"text": x} for x in r] for r in rows], "resize_keyboard": True}


def pager(prefix, page, total, per=PER_PAGE):
    pages = max(1, -(-total // per))
    row = []
    if page > 0:
        row.append(("◀️", f"{prefix}:{page - 1}"))
    row.append((f"{page + 1}/{pages}", "noop"))
    if page + 1 < pages:
        row.append(("▶️", f"{prefix}:{page + 1}"))
    return row


def nav_row(lg, back=None):
    row = []
    if back:
        row.append((t(lg, "btn_back"), back))
    row.append((t(lg, "btn_menu"), "menu"))
    return row


def send(chat_id, text, kb=None, photo=None):
    if photo:
        try:
            return tg.send_photo(chat_id, photo, caption=text[:1024], reply_markup=kb)
        except tg.TgError as e:
            if e.blocked:
                raise
            log.warning("poster yuborilmadi: %s", e.description)
    return tg.send_message(chat_id, text, reply_markup=kb)


def show(chat_id, msg, text, kb=None, photo=None):
    """Mavjud xabarni joyida yangilaydi (silliq o'tish); iloji bo'lmasa o'chirib qayta yuboradi."""
    if msg is not None and not photo and "text" in msg and "photo" not in msg:
        try:
            return tg.edit_text(chat_id, msg["message_id"], text, kb)
        except tg.TgError as e:
            if "not modified" in e.description.lower():
                return None
    if msg is not None:
        try:
            tg.delete_message(chat_id, msg["message_id"])
        except tg.TgError:
            pass
    return send(chat_id, text, kb, photo)


def notify(uid, text, kb=None):
    """Xavfsiz xabar yuborish. Foydalanuvchi botni bloklagan bo'lsa belgilaydi."""
    try:
        tg.send_message(uid, text, reply_markup=kb)
        return True
    except tg.TgError as e:
        if e.blocked:
            sv.mark_bot_blocked(uid)
        else:
            log.warning("xabar yuborilmadi uid=%s: %s", uid, e.description)
        return False


def animate(chat_id, frames, remove=True):
    """Bitta xabarni bir necha kadr bilan tahrirlab animatsiya qiladi (yozib chiqish / progress)."""
    if not cfg.animations or not frames:
        return
    try:
        m = tg.send_message(chat_id, frames[0])
        for f in frames[1:]:
            sleep(cfg.anim_delay)
            tg.edit_text(chat_id, m["message_id"], f)
        if remove:
            sleep(cfg.anim_delay)
            tg.delete_message(chat_id, m["message_id"])
    except tg.TgError as e:
        log.info("animatsiya to'xtadi: %s", e.description)


def loading(chat_id, label):
    animate(chat_id, [f"{label} {s}" for s in SPINNER])


def typing_intro(chat_id, word="TILAKINO"):
    # Ixtiyoriy GIF: Render Environment -> WELCOME_GIF_FILE_ID ga Telegram file_id kiriting.
    if cfg.animations and cfg.welcome_gif_file_id:
        try:
            tg.send_animation(chat_id, cfg.welcome_gif_file_id, caption="🎬 <b>TILAKINO — Kino olami</b> 🍿")
            return
        except tg.TgError as e:
            log.warning("welcome GIF yuborilmadi, matnli animatsiyaga qaytamiz: %s", e.description)
    steps = sorted({max(1, round(len(word) * i / 4)) for i in range(1, 5)})
    animate(chat_id, [f"🎬 <b>{word[:n]}</b>{'▌' if n < len(word) else ' 🍿'}" for n in steps])
