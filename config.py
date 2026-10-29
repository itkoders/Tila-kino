# -*- coding: utf-8 -*-
"""Sozlamalar: barcha sirlar faqat muhit o'zgaruvchilaridan o'qiladi."""
import os
import re

DEFAULT_ADMIN_ID = 6359925487


def _g(name, default=""):
    return (os.environ.get(name) or default).strip()


class Settings:
    def __init__(self):
        self.reload()

    def reload(self):
        self.token = _g("TELEGRAM_BOT_TOKEN")
        self.webhook_secret = _g("WEBHOOK_SECRET")
        self.base_url = _g("RENDER_EXTERNAL_URL").rstrip("/")
        self.bot_username = _g("BOT_USERNAME").lstrip("@")
        self.database_url = _g("DATABASE_URL", "sqlite:///tilakino.db")
        self.cron_secret = _g("CRON_SECRET")
        self.payment_secret = _g("PAYMENT_CALLBACK_SECRET")
        self.animations = _g("ANIMATIONS", "1") not in ("0", "false", "no")
        self.welcome_gif_file_id = _g("WELCOME_GIF_FILE_ID")
        self.anim_delay = float(_g("ANIM_DELAY", "0.35") or 0.35)
        self.scheduler = _g("ENABLE_SCHEDULER", "1") not in ("0", "false", "no")
        self.tz = "Asia/Tashkent"
        raw = _g("ADMIN_ID", str(DEFAULT_ADMIN_ID))
        self._admin_raw = raw
        self.admin_id = int(raw) if raw.lstrip("-").isdigit() else DEFAULT_ADMIN_ID

    def problems(self):
        """Ishga tushishga to'sqinlik qiladigan sozlama kamchiliklari."""
        out = []
        if not self.token:
            out.append("TELEGRAM_BOT_TOKEN o'rnatilmagan")
        if not self.webhook_secret:
            out.append("WEBHOOK_SECRET o'rnatilmagan")
        elif not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", self.webhook_secret):
            out.append("WEBHOOK_SECRET faqat A-Z a-z 0-9 _ - belgilaridan iborat bo'lishi kerak")
        if not self._admin_raw.lstrip("-").isdigit():
            out.append("ADMIN_ID raqam emas, standart qiymat ishlatilmoqda")
        return out

    def warnings(self):
        out = []
        if self.database_url.startswith("sqlite"):
            out.append("SQLite ishlatilmoqda: Render bepul rejasida fayl tizimi vaqtinchalik, "
                       "ma'lumotlar qayta ishga tushganda yo'qoladi. DATABASE_URL (PostgreSQL) bering.")
        if not self.base_url:
            out.append("RENDER_EXTERNAL_URL yo'q: webhook avtomatik o'rnatilmaydi")
        return out


cfg = Settings()
