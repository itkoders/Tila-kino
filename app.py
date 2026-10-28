# -*- coding: utf-8 -*-
"""Flask ilova: Telegram webhook, health, to'lov callbacki, cron va sayt (companion website).
Gunicorn:  gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4"""
import hmac
import logging
import threading

from flask import Flask, Response, abort, jsonify, render_template, request

import db
import handlers
import scheduler
import services as sv
import tg
from config import cfg
from payment_providers import PROVIDERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("tilakino.app")

VIDEO_EXT = (".mp4", ".webm", ".ogg", ".mov")


def fetch_poster(file_id):  # testlarda almashtiriladi
    info = tg.get_file(file_id)
    return tg.download_file(info["file_path"])


def init_database():
    try:
        db.init()
        db.init_schema()
        return True
    except Exception:
        log.exception("DB ishga tushmadi (DATABASE_URL ni tekshiring)")
        return False


def register_webhook():
    """Webhookni haqiqiy Render URL bilan o'rnatadi. Token log'ga tushmaydi."""
    if cfg.problems() or not cfg.base_url:
        log.warning("webhook o'rnatilmadi: sozlama yetarli emas")
        return False
    try:
        tg.set_webhook(f"{cfg.base_url}/webhook", cfg.webhook_secret)
        log.info("webhook o'rnatildi: %s/webhook", cfg.base_url)
        return True
    except tg.TgError as e:
        log.error("webhook o'rnatilmadi: %s", e.description)
        return False


def public_movie(m, with_eps=True):
    d = {"code": m["code"], "kind": m["kind"], "title": m["title"], "year": m["year"], "country": m["country"],
         "genre": m["genre"], "language": m["language"], "description": m["description"], "rating": m["rating"],
         "views": m["views"], "poster": f"/poster/{m['code']}" if m["poster_file_id"] else None, "watch_url": None,
         "episodes": []}
    if m["kind"] == "movie":
        v = sv.web_variant(movie_id=m["id"])
        d["watch_url"] = v["external_url"] if v else None
    elif with_eps:
        for e in sv.list_episodes(m["id"]):
            v = sv.web_variant(episode_id=e["id"])
            d["episodes"].append({"id": e["id"], "season": e["season"], "number": e["number"], "title": e["title"],
                                  "description": e["description"], "watch_url": v["external_url"] if v else None})
    return d


def create_app():
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False
    state = {"db_ok": init_database()}

    @app.after_request
    def headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "same-origin"
        return resp

    # ---------------------------------------------------------------- health
    @app.get("/health")
    @app.get("/healthz")
    def health():
        db_ok = True
        try:
            db.one("SELECT 1 AS x")
        except Exception:
            db_ok = False
        body = {"status": "ok" if db_ok else "db_error", "db": db_ok, "bot_configured": not cfg.problems(),
                "problems": cfg.problems(), "warnings": cfg.warnings()}
        return jsonify(body), (200 if db_ok else 503)

    # ---------------------------------------------------------------- webhook
    @app.post("/webhook")
    def webhook():
        if cfg.problems():
            return jsonify({"error": "bot sozlanmagan", "problems": cfg.problems()}), 503
        got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(got.encode(), cfg.webhook_secret.encode()):
            return jsonify({"error": "forbidden"}), 403
        upd = request.get_json(silent=True)
        if not isinstance(upd, dict) or not isinstance(upd.get("update_id"), int):
            return jsonify({"error": "malformed update"}), 400
        try:
            first = sv.claim_update(upd["update_id"])
        except Exception:
            log.exception("update'ni qayd etib bo'lmadi (DB xatosi)")
            return jsonify({"error": "db error"}), 503  # Telegram keyinroq qayta yuboradi
        if not first:
            return jsonify({"ok": True, "duplicate": True})
        try:
            handlers.handle_update(upd)
        except Exception:
            log.exception("update qayta ishlashda xato")
        return jsonify({"ok": True})

    # ---------------------------------------------------------------- to'lov callbacki
    @app.post("/payments/callback/<name>")
    def payment_callback(name):
        prov = PROVIDERS.get(name)
        if not prov:
            return jsonify({"error": "unknown provider"}), 404
        if not prov.configured():
            return jsonify({"error": "provider sozlanmagan"}), 501
        body = request.get_data()
        if not prov.verify(request.headers, body):
            return jsonify({"error": "bad signature"}), 403
        try:
            reference, amount, txn = prov.parse(body)
        except Exception:
            return jsonify({"error": "malformed"}), 400
        try:
            status, p = sv.auto_confirm(reference, amount, txn)
        except Exception:
            log.exception("to'lov callbackida DB xatosi")
            return jsonify({"error": "db error"}), 503
        if status == "approved":
            handlers.notify_payment(p)
        code = {"approved": 200, "duplicate": 200, "not_found": 404, "not_pending": 409,
                "amount_mismatch": 422, "bad_request": 400}.get(status, 400)
        return jsonify({"status": status}), code

    # ---------------------------------------------------------------- cron
    @app.route("/cron/tick", methods=["GET", "POST"])
    def cron_tick():
        if not cfg.cron_secret:
            return jsonify({"error": "CRON_SECRET sozlanmagan"}), 501
        key = request.headers.get("X-Cron-Key") or request.args.get("key", "")
        if not hmac.compare_digest(key.encode(), cfg.cron_secret.encode()):
            return jsonify({"error": "forbidden"}), 403
        return jsonify(scheduler.tick(handlers.send_reminder))

    # ---------------------------------------------------------------- sayt
    @app.get("/")
    def site_index():
        q = (request.args.get("q") or "").strip()[:80]
        kind = request.args.get("kind") if request.args.get("kind") in ("movie", "series") else None
        if q:
            items, total = sv.search_catalog(q, 0, 48)
            if kind:
                items = [m for m in items if m["kind"] == kind]
        else:
            items, total = sv.list_catalog(kind, 0, 48)
        return render_template("index.html", items=items, q=q, kind=kind, bot=cfg.bot_username)

    @app.get("/movie/<code>")
    def site_movie(code):
        m = sv.get_movie_by_code(code)
        if not m:
            abort(404)
        d = public_movie(m)
        cur = None
        if m["kind"] == "series" and d["episodes"]:
            want = request.args.get("ep", type=int)
            cur = next((e for e in d["episodes"] if e["id"] == want), d["episodes"][0])
        url = d["watch_url"] if m["kind"] == "movie" else (cur["watch_url"] if cur else None)
        is_file = bool(url) and url.lower().split("?")[0].endswith(VIDEO_EXT)
        return render_template("movie.html", m=d, cur=cur, url=url, is_file=is_file, bot=cfg.bot_username)

    @app.get("/api/catalog")
    def api_catalog():
        q = (request.args.get("q") or "").strip()[:80]
        page = max(0, request.args.get("page", 0, type=int))
        kind = request.args.get("kind") if request.args.get("kind") in ("movie", "series") else None
        if q:
            items, total = sv.search_catalog(q, page, 20)
        else:
            items, total = sv.list_catalog(kind, page, 20)
        return jsonify({"total": total, "page": page, "items": [public_movie(m, with_eps=False) for m in items]})

    @app.get("/api/movie/<code>")
    def api_movie(code):
        m = sv.get_movie_by_code(code)
        if not m:
            return jsonify({"error": "not found"}), 404
        return jsonify(public_movie(m))

    @app.get("/poster/<code>")
    def poster(code):
        m = sv.get_movie_by_code(code)
        if not m or not m["poster_file_id"]:
            abort(404)
        try:
            data, ctype = fetch_poster(m["poster_file_id"])
        except Exception:
            abort(404)
        return Response(data, mimetype=ctype, headers={"Cache-Control": "public, max-age=3600"})

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "not found"}), 404
        return render_template("index.html", items=[], q="", kind=None, bot=cfg.bot_username, missing=True), 404

    return app


def boot_background(app):
    """Haqiqiy ishga tushishda: webhook va davriy ishlar (testlarda chaqirilmaydi)."""
    if not cfg.problems():
        threading.Thread(target=register_webhook, daemon=True).start()
        if cfg.scheduler:
            scheduler.start(handlers.send_reminder)


app = create_app()
if __name__ != "__main__":
    import os
    if not os.environ.get("TILAKINO_NO_BOOT"):
        boot_background(app)

if __name__ == "__main__":
    import os
    boot_background(app)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
