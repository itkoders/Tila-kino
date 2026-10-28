
# scheduler.py
"""Premium vazifalari va 24 soatlik kino import rejalashtiruvchisi."""

import logging
import threading
import time

import services

log = logging.getLogger("tilakino.scheduler")
_started = False
_import_lock = threading.Lock()
IMPORT_INTERVAL = 24 * 60 * 60


def run_daily_import():
    """Importni ko'pi bilan har 24 soatda bir marta ishga tushirish."""
    with _import_lock:
        try:
            last = int(services.get_setting("last_movie_import") or "0")
        except (TypeError, ValueError):
            last = 0

        current = int(time.time())
        if current - last < IMPORT_INTERVAL:
            return {"status": "waiting", "next_in_seconds": IMPORT_INTERVAL - (current - last)}

        try:
            import importer

            result = importer.import_candidates(limit=20)
            services.set_setting("last_movie_import", str(int(time.time())))
            log.info("Kunlik kino import natijasi: %s", result)
            return {"status": "ok", **result}
        except Exception:
            log.exception("Kunlik kino importi bajarilmadi")
            return {"status": "error"}


def tick(notify=None):
    res = {
        "expired_subs": services.expire_subscriptions(),
        "expired_payments": services.expire_payments(),
        "reminders": 0,
    }

    for uid, lang, kind, until in services.claim_reminders():
        res["reminders"] += 1
        if notify:
            try:
                notify(uid, lang, kind, until)
            except Exception:
                log.exception("Eslatma yuborilmadi uid=%s", uid)

    services.cleanup_updates()

    # Har 24 soatda yangi kino nomzodlarini tekshirish.
    res["movie_import"] = run_daily_import()
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
                log.exception("Scheduler xatosi")
            time.sleep(interval)

    threading.Thread(
        target=loop,
        daemon=True,
        name="tilakino-scheduler",
    ).start()
    
