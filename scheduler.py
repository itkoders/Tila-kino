# -*- coding: utf-8 -*-
"""Davriy ishlar: Premium muddati tugashi, eslatmalar, muddati o'tgan to'lovlar, eski update'larni tozalash.
Render bepul rejasida servis uxlab qoladi - /cron/tick manzilini tashqi pinger (cron-job.org, UptimeRobot)
bilan har 10 daqiqada chaqirish tavsiya etiladi."""
import logging
import threading
import time

import services

log = logging.getLogger("tilakino.scheduler")
_started = False


def tick(notify=None):
    res = {"expired_subs": services.expire_subscriptions(),
           "expired_payments": services.expire_payments(), "reminders": 0}
    for uid, lang, kind, until in services.claim_reminders():
        res["reminders"] += 1
        if notify:
            try:
                notify(uid, lang, kind, until)
            except Exception:
                log.exception("eslatma yuborilmadi uid=%s", uid)
    services.cleanup_updates()
    return res


def start(notify, interval=600):
    global _started
    if _started:
        return
    _started = True

    def loop():
        while True:
            try:
                tick(notify)
            except Exception:
                log.exception("scheduler xatosi")
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True, name="tilakino-scheduler").start()
