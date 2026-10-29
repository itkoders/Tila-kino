# -*- coding: utf-8 -*-
"""Biznes mantiq: katalog, Premium, to'lovlar, adminlar, statistika. Telegramdan mustaqil."""
import json
import random
import re
import secrets
from datetime import datetime, timedelta, timezone
import time

import db
from config import cfg

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(cfg.tz)
except Exception:  # tzdata yo'q bo'lsa: Toshkent doimiy UTC+5 (yozgi vaqt yo'q)
    TZ = timezone(timedelta(hours=5))

PERMS = ["catalog", "premium", "users", "sponsor", "stats", "broadcast"]
QUALITIES = ("medium", "high")
LANG_CODES = ("uz", "ru", "en", "tg")
DEFAULT_PLANS = {
    "1m": {"days": 30, "price": 10000, "label": "1 oy"},
    "2m": {"days": 60, "price": 20000, "label": "2 oy"},
    "6m": {"days": 180, "price": 40000, "label": "6 oy"},
    "1y": {"days": 365, "price": 60000, "label": "1 yil"},
}
DEFAULTS = {"ref_bonus_days": "3", "trial_days": "0", "protect_content": "0",
            "sponsor_cooldown_min": "10", "card_info": "", "payment_ttl_hours": "24"}


def now():
    return int(time.time())


def local_dt(ts):
    return datetime.fromtimestamp(ts, TZ)


def fmt_dt(ts):
    return local_dt(ts).strftime("%Y-%m-%d %H:%M") if ts else "—"


def fmt_date(ts):
    return local_dt(ts).strftime("%Y-%m-%d") if ts else "—"


def money(n):
    return f"{int(n):,}".replace(",", " ")


def is_unique_error(e):
    s = str(e).lower()
    return "unique" in s or "duplicate" in s


# ------------------------------------------------------------------ sozlamalar
def get_setting(key):
    r = db.one("SELECT value FROM settings WHERE key=?", (key,))
    return r["value"] if r else DEFAULTS.get(key, "")


def set_setting(key, value):
    db.execute("INSERT INTO settings(key,value) VALUES(?,?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))


def get_plans():
    plans = {k: dict(v) for k, v in DEFAULT_PLANS.items()}
    try:
        stored = json.loads(get_setting("plans") or "{}")
    except ValueError:
        stored = {}
    for k, v in stored.items():
        if k in plans:
            plans[k].update(v)
    return plans


def update_plan(key, field, value):
    plans = get_plans()
    if key not in plans or field not in ("price", "days"):
        raise ValueError("invalid")
    try:
        v = int(str(value).replace(" ", ""))
    except ValueError:
        raise ValueError("invalid")
    if v <= 0 or v > 10_000_000:
        raise ValueError("invalid")
    plans[key][field] = v
    set_setting("plans", json.dumps(plans))
    return plans[key]


def get_int_setting(key):
    try:
        return int(get_setting(key) or 0)
    except ValueError:
        return int(DEFAULTS.get(key, 0) or 0)


# ------------------------------------------------------------------ adminlar
def is_owner(uid):
    return uid == cfg.admin_id


def is_admin(uid):
    if is_owner(uid):
        return True
    return db.one("SELECT 1 AS x FROM admins WHERE user_id=?", (uid,)) is not None


def has_perm(uid, perm):
    if is_owner(uid):
        return True
    r = db.one("SELECT perms FROM admins WHERE user_id=?", (uid,))
    return bool(r) and perm in (r["perms"] or "").split(",")


def admin_perms(uid):
    if is_owner(uid):
        return list(PERMS)
    r = db.one("SELECT perms FROM admins WHERE user_id=?", (uid,))
    return [p for p in (r["perms"] if r else "").split(",") if p]


def add_helper(by, uid, perms):
    if not is_owner(by):
        raise PermissionError("owner_only")
    if is_owner(uid):
        raise ValueError("owner")
    perms = [p for p in perms if p in PERMS]
    if not perms:
        raise ValueError("no_perms")
    db.execute("INSERT INTO admins(user_id,role,perms,added_by,added_at) VALUES(?,?,?,?,?) "
               "ON CONFLICT(user_id) DO UPDATE SET perms=excluded.perms",
               (uid, "helper", ",".join(perms), by, now()))
    audit(by, "helper_add", f"{uid}:{','.join(perms)}")
    return perms


def remove_helper(by, uid):
    if not is_owner(by):
        raise PermissionError("owner_only")
    if is_owner(uid):
        raise ValueError("owner")
    n = db.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    if n:
        audit(by, "helper_remove", str(uid))
    return n > 0


def list_admins():
    return db.q("SELECT * FROM admins ORDER BY added_at")


def audit(admin_id, action, details=""):
    db.execute("INSERT INTO audit_log(admin_id,action,details,at) VALUES(?,?,?,?)",
               (admin_id, action, str(details)[:500], now()))


def recent_audit(limit=20):
    return db.q("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))


# ------------------------------------------------------------------ foydalanuvchilar
def guess_lang(code):
    code = (code or "").lower()[:2]
    return code if code in LANG_CODES else "uz"


def upsert_user(tgu):
    uid = tgu["id"]
    name = (tgu.get("first_name") or "")[:100]
    uname = tgu.get("username")
    n = now()
    with db.tx() as t:
        u = t.one("SELECT * FROM users WHERE id=?", (uid,))
        if u:
            t.exec("UPDATE users SET first_name=?, username=?, last_seen=? WHERE id=?", (name, uname, n, uid))
            u.update(first_name=name, username=uname, last_seen=n)
            return u, False
        ins = t.exec("INSERT INTO users(id,first_name,username,lang,joined_at,last_seen,created_at) VALUES(?,?,?,?,?,?,?) "
                     "ON CONFLICT(id) DO NOTHING",
                     (uid, name, uname, guess_lang(tgu.get("language_code")), n, n, n))
        return t.one("SELECT * FROM users WHERE id=?", (uid,)), ins == 1


def get_user(uid):
    return db.one("SELECT * FROM users WHERE id=?", (uid,))


def set_lang(uid, lang):
    if lang in LANG_CODES:
        db.execute("UPDATE users SET lang=? WHERE id=?", (lang, uid))


def set_blocked(uid, flag):
    if is_owner(uid):
        raise ValueError("owner")
    return db.execute("UPDATE users SET blocked=? WHERE id=?", (1 if flag else 0, uid)) > 0


def mark_bot_blocked(uid, flag=True):
    db.execute("UPDATE users SET bot_blocked=? WHERE id=?", (1 if flag else 0, uid))


def is_premium(u):
    return bool(u) and (u.get("premium_until") or 0) > now()


def apply_referral(new_uid, ref_uid):
    """Yangi foydalanuvchi uchun taklif bonusi (kino_bot.py'dagi referal tizimi saqlangan)."""
    if not ref_uid or ref_uid == new_uid:
        return False
    days = get_int_setting("ref_bonus_days")
    with db.tx() as t:
        if not t.one("SELECT 1 AS x FROM users WHERE id=?", (ref_uid,)):
            return False
        n = t.exec("UPDATE users SET referrer_id=? WHERE id=? AND referrer_id IS NULL", (ref_uid, new_uid))
        if n != 1:
            return False
        t.exec("UPDATE users SET ref_count=ref_count+1 WHERE id=?", (ref_uid,))
        if days > 0:
            _grant(t, ref_uid, days, "referral", None)
    return True


# ------------------------------------------------------------------ Premium
def _grant(t, uid, days, source, payment_id):
    u = t.one("SELECT premium_until FROM users WHERE id=?", (uid,))
    if not u:
        raise ValueError("user_not_found")
    n = now()
    base = max(u["premium_until"] or 0, n)
    end = base + int(days) * 86400
    t.exec("INSERT INTO subscriptions(user_id,days,starts_at,expires_at,source,payment_id,active) "
           "VALUES(?,?,?,?,?,?,1)", (uid, int(days), n, end, source, payment_id))
    t.exec("UPDATE users SET premium_until=? WHERE id=?", (end, uid))
    return end


def grant_premium(uid, days, source="manual"):
    days = int(days)
    if days <= 0 or days > 3650:
        raise ValueError("invalid")
    with db.tx() as t:
        return _grant(t, uid, days, source, None)


def revoke_premium(uid):
    n = now()
    with db.tx() as t:
        t.exec("UPDATE users SET premium_until=? WHERE id=?", (n, uid))
        t.exec("UPDATE subscriptions SET active=0 WHERE user_id=? AND active=1", (uid,))


def set_premium_expiry(uid, ts):
    n = now()
    with db.tx() as t:
        if not t.one("SELECT 1 AS x FROM users WHERE id=?", (uid,)):
            raise ValueError("user_not_found")
        t.exec("UPDATE users SET premium_until=? WHERE id=?", (int(ts), uid))
        if ts > n:
            t.exec("INSERT INTO subscriptions(user_id,days,starts_at,expires_at,source,active) "
                   "VALUES(?,?,?,?,?,1)", (uid, max(0, (int(ts) - n) // 86400), n, int(ts), "manual_expiry"))
        else:
            t.exec("UPDATE subscriptions SET active=0 WHERE user_id=? AND active=1", (uid,))


def parse_local_date(s):
    """'YYYY-MM-DD' -> shu kun oxiri (23:59, Toshkent) epoch."""
    d = datetime.strptime(s.strip(), "%Y-%m-%d")
    return int(d.replace(hour=23, minute=59, tzinfo=TZ).timestamp())


def list_premium(active=True, limit=30):
    n = now()
    if active:
        return db.q("SELECT * FROM users WHERE premium_until>? ORDER BY premium_until LIMIT ?", (n, limit))
    return db.q("SELECT * FROM users WHERE premium_until>0 AND premium_until<=? "
                "ORDER BY premium_until DESC LIMIT ?", (n, limit))


def list_subscriptions(uid, limit=5):
    return db.q("SELECT * FROM subscriptions WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))


def expire_subscriptions():
    return db.execute("UPDATE subscriptions SET active=0 WHERE active=1 AND expires_at<=?", (now(),))


def claim_reminders():
    """Yuboriladigan eslatmalar ro'yxati [(uid, lang, 'remind3'|'remind0', premium_until)].
    Har bir (foydalanuvchi, tugash vaqti) uchun eslatma bir martadan ortiq berilmaydi."""
    n = now()
    today = local_dt(n).date()
    out = []
    with db.tx() as t:
        rows = t.q("SELECT id,lang,premium_until FROM users WHERE premium_until>? AND premium_until<=? "
                   "AND blocked=0 AND bot_blocked=0", (n - 86400, n + 4 * 86400))
        for r in rows:
            diff = (local_dt(r["premium_until"]).date() - today).days
            if 1 <= diff <= 3:
                kind, col = "remind3", "remind3_for"
            elif diff == 0:
                kind, col = "remind0", "remind0_for"
            else:
                continue
            ok = t.exec(f"UPDATE users SET {col}=premium_until WHERE id=? AND {col}<>premium_until", (r["id"],))
            if ok == 1:
                out.append((r["id"], r["lang"], kind, r["premium_until"]))
    return out


# ------------------------------------------------------------------ to'lovlar
PAY_FINAL = ("approved", "rejected", "expired")


def create_payment(uid, plan_key):
    plan = get_plans().get(plan_key)
    if not plan:
        raise ValueError("invalid_plan")
    ttl = get_int_setting("payment_ttl_hours") * 3600
    with db.tx() as t:
        p = t.one("SELECT * FROM payments WHERE user_id=? AND plan_key=? AND status='pending' AND created_at>? "
                  "ORDER BY id DESC LIMIT 1", (uid, plan_key, now() - ttl))
        if p:
            return p
        for _ in range(5):
            ref = "TK-" + secrets.token_hex(3).upper()
            if not t.one("SELECT 1 AS x FROM payments WHERE reference=?", (ref,)):
                break
        pid = t.insert("INSERT INTO payments(user_id,plan_key,days,amount,status,reference,provider,created_at) "
                       "VALUES(?,?,?,?,?,?,?,?)",
                       (uid, plan_key, plan["days"], plan["price"], "pending", ref, "manual", now()))
        return t.one("SELECT * FROM payments WHERE id=?", (pid,))


def get_payment(pid):
    return db.one("SELECT * FROM payments WHERE id=?", (pid,))


def attach_proof(pid, uid, file_id):
    return db.execute("UPDATE payments SET proof_file_id=? WHERE id=? AND user_id=? AND status='pending'",
                      (file_id, pid, uid)) == 1


def decide_payment(pid, approve, admin_id=None, provider="manual", txn=None):
    """Atomik holat o'tishi: faqat 'pending' -> 'approved'/'rejected'. Takror chaqirish hech narsani o'zgartirmaydi."""
    new = "approved" if approve else "rejected"
    with db.tx() as t:
        n = t.exec("UPDATE payments SET status=?, decided_at=?, decided_by=?, provider=?, provider_txn=? "
                   "WHERE id=? AND status='pending'", (new, now(), admin_id, provider, txn, pid))
        p = t.one("SELECT * FROM payments WHERE id=?", (pid,))
        if n != 1:
            return False, p
        if approve:
            _grant(t, p["user_id"], p["days"], provider, pid)
            p = t.one("SELECT * FROM payments WHERE id=?", (pid,))
        return True, p


def auto_confirm(reference, amount, txn):
    """Avtomatik provayder callbacki. Qaytaradi: (holat, payment)."""
    if not txn:
        return "bad_request", None
    dup = db.one("SELECT * FROM payments WHERE provider_txn=?", (txn,))
    if dup:
        return "duplicate", dup
    p = db.one("SELECT * FROM payments WHERE reference=?", (reference,))
    if not p:
        return "not_found", None
    if p["status"] != "pending":
        return "not_pending", p
    try:
        if int(amount) != int(p["amount"]):
            return "amount_mismatch", p
    except (TypeError, ValueError):
        return "bad_request", p
    ok, p = decide_payment(p["id"], True, None, "generic", txn)
    return ("approved" if ok else "not_pending"), p


def expire_payments():
    ttl = get_int_setting("payment_ttl_hours") * 3600
    return db.execute("UPDATE payments SET status='expired', decided_at=? WHERE status='pending' AND created_at<?",
                      (now(), now() - ttl))


def list_payments(status=None, uid=None, limit=15):
    sql, args = "SELECT * FROM payments WHERE 1=1", []
    if status:
        sql += " AND status=?"
        args.append(status)
    if uid:
        sql += " AND user_id=?"
        args.append(uid)
    return db.q(sql + " ORDER BY id DESC LIMIT ?", (*args, limit))


# ------------------------------------------------------------------ katalog
def _like(s):
    return "%" + s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def norm_langs(value):
    parts = [p.strip().lower() for p in re.split(r"[,\s/]+", value or "") if p.strip()]
    bad = [p for p in parts if p not in LANG_CODES]
    if bad or not parts:
        raise ValueError("lang")
    return ",".join(dict.fromkeys(parts))


def _clean(field, value):
    v = (value or "").strip() if isinstance(value, str) else value
    if field == "code":
        if not re.fullmatch(r"\d{1,12}", v or ""):
            raise ValueError("code_format")
        return v
    if field == "title":
        if not v or len(v) > 200:
            raise ValueError("title")
        return v
    if v in (None, "", "-"):
        return None
    if field == "year":
        if not re.fullmatch(r"\d{4}", str(v)) or not 1888 <= int(v) <= 2100:
            raise ValueError("year")
        return int(v)
    if field == "rating":
        try:
            r = float(str(v).replace(",", "."))
        except ValueError:
            raise ValueError("rating")
        if not 0 <= r <= 10:
            raise ValueError("rating")
        return r
    if field == "language":
        return norm_langs(v)
    if field in ("country", "genre"):
        return v[:100]
    if field == "description":
        return v[:3000]
    if field == "poster_file_id":
        return v
    raise ValueError("field")


validate_field = _clean


def admin_find(text, limit=10):
    """Admin qidiruvi: kod yoki nom bo'yicha (nashr etilmaganlar ham)."""
    text = (text or "").strip()
    return db.q("SELECT * FROM movies WHERE code=? OR LOWER(title) LIKE ? ESCAPE '\\' "
                "ORDER BY created_at DESC, id DESC LIMIT ?", (text, _like(text.lower()), limit))


def create_movie(data):
    kind = data.get("kind", "movie")
    if kind not in ("movie", "series"):
        raise ValueError("kind")
    vals = {f: _clean(f, data.get(f)) for f in ("code", "title", "year", "country", "genre",
                                                "language", "description", "rating", "poster_file_id")}
    try:
        with db.tx() as t:
            mid = t.insert("INSERT INTO movies(code,kind,title,poster_file_id,year,country,genre,language,"
                           "description,rating,published,views,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,1,0,?)",
                           (vals["code"], kind, vals["title"], vals["poster_file_id"], vals["year"],
                            vals["country"], vals["genre"], vals["language"], vals["description"],
                            vals["rating"], now()))
            return t.one("SELECT * FROM movies WHERE id=?", (mid,))
    except Exception as e:
        if is_unique_error(e):
            raise ValueError("code_taken")
        raise


EDITABLE = ("title", "year", "country", "genre", "language", "description", "rating", "code", "poster_file_id")


def update_movie(mid, field, value):
    if field not in EDITABLE:
        raise ValueError("field")
    v = _clean(field, value)
    try:
        n = db.execute(f"UPDATE movies SET {field}=? WHERE id=?", (v, mid))
    except Exception as e:
        if is_unique_error(e):
            raise ValueError("code_taken")
        raise
    if not n:
        raise ValueError("not_found")
    return get_movie(mid)


def get_movie(mid):
    return db.one("SELECT * FROM movies WHERE id=?", (mid,))


def generate_movie_code():
    """Katalog uchun band bo'lmagan 4 xonali raqamli kod yaratadi."""
    for _ in range(100):
        code = str(secrets.randbelow(9000) + 1000)
        if not get_movie_by_code(code, published_only=False):
            return code
    # Katalogda 4 xonali kodlar juda ko'p bo'lib qolsa, uzunroq kodga o'tadi.
    for _ in range(100):
        code = str(secrets.randbelow(900000) + 100000)
        if not get_movie_by_code(code, published_only=False):
            return code
    raise RuntimeError("Bo'sh kino kodi topilmadi")


def get_movie_by_code(code, published_only=True):
    sql = "SELECT * FROM movies WHERE code=?" + (" AND published=1" if published_only else "")
    return db.one(sql, (code,))


def set_published(mid, flag):
    return db.execute("UPDATE movies SET published=? WHERE id=?", (1 if flag else 0, mid)) > 0


def delete_movie(mid):
    return db.execute("DELETE FROM movies WHERE id=?", (mid,)) > 0


def list_catalog(kind=None, page=0, per=8, published_only=True):
    where, args = "WHERE 1=1", []
    if published_only:
        where += " AND published=1"
    if kind:
        where += " AND kind=?"
        args.append(kind)
    total = db.one(f"SELECT COUNT(*) AS c FROM movies {where}", args)["c"]
    items = db.q(f"SELECT * FROM movies {where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                 (*args, per, page * per))
    return items, total


def search_catalog(text, page=0, per=8):
    text = (text or "").strip()
    if not text:
        return [], 0
    like = _like(text.lower())
    cond = ["LOWER(m.title) LIKE ? ESCAPE '\\'",
            "m.id IN (SELECT e.series_id FROM episodes e WHERE e.published=1 AND "
            "(LOWER(e.title) LIKE ? ESCAPE '\\' OR LOWER(e.description) LIKE ? ESCAPE '\\'))"]
    args = [like, like, like]
    if text.isdigit():
        cond.append("m.code=?")
        args.append(text)
    mm = re.fullmatch(r"[sS](\d+)[eE](\d+)", text)
    if mm:
        cond.append("m.id IN (SELECT series_id FROM episodes WHERE season=? AND number=? AND published=1)")
        args += [int(mm.group(1)), int(mm.group(2))]
    where = "WHERE m.published=1 AND (" + " OR ".join(cond) + ")"
    total = db.one(f"SELECT COUNT(*) AS c FROM movies m {where}", args)["c"]
    items = db.q(f"SELECT m.* FROM movies m {where} ORDER BY m.created_at DESC, m.id DESC LIMIT ? OFFSET ?",
                 (*args, per, page * per))
    return items, total


# ------------------------------------------------------------------ epizodlar
def create_episode(series_id, season, number, title=None, description=None):
    m = get_movie(series_id)
    if not m or m["kind"] != "series":
        raise ValueError("not_series")
    try:
        season, number = int(season), int(number)
    except (TypeError, ValueError):
        raise ValueError("numbers")
    if season < 1 or number < 1 or season > 999 or number > 9999:
        raise ValueError("numbers")
    try:
        with db.tx() as t:
            eid = t.insert("INSERT INTO episodes(series_id,season,number,title,description,published,views,created_at)"
                           " VALUES(?,?,?,?,?,1,0,?)",
                           (series_id, season, number, (title or None), (description or None), now()))
            return t.one("SELECT * FROM episodes WHERE id=?", (eid,))
    except Exception as e:
        if is_unique_error(e):
            raise ValueError("episode_exists")
        raise


def get_episode(eid):
    return db.one("SELECT * FROM episodes WHERE id=?", (eid,))


def list_episodes(series_id, season=None, published_only=True):
    sql, args = "SELECT * FROM episodes WHERE series_id=?", [series_id]
    if published_only:
        sql += " AND published=1"
    if season is not None:
        sql += " AND season=?"
        args.append(season)
    return db.q(sql + " ORDER BY season, number", args)


def list_seasons(series_id, published_only=True):
    sql = "SELECT DISTINCT season FROM episodes WHERE series_id=?" + (" AND published=1" if published_only else "")
    return [r["season"] for r in db.q(sql + " ORDER BY season", (series_id,))]


def update_episode(eid, field, value):
    if field in ("season", "number"):
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError("numbers")
        if v < 1 or v > 9999:
            raise ValueError("numbers")
    elif field in ("title", "description"):
        v = (value or "").strip() or None
        if v == "-":
            v = None
    else:
        raise ValueError("field")
    try:
        n = db.execute(f"UPDATE episodes SET {field}=? WHERE id=?", (v, eid))
    except Exception as e:
        if is_unique_error(e):
            raise ValueError("episode_exists")
        raise
    if not n:
        raise ValueError("not_found")
    return get_episode(eid)


def set_episode_published(eid, flag):
    return db.execute("UPDATE episodes SET published=? WHERE id=?", (1 if flag else 0, eid)) > 0


def delete_episode(eid):
    return db.execute("DELETE FROM episodes WHERE id=?", (eid,)) > 0


def episode_neighbors(eid):
    ep = get_episode(eid)
    if not ep:
        return None, None
    eps = list_episodes(ep["series_id"])
    ids = [e["id"] for e in eps]
    if eid not in ids:
        return None, None
    i = ids.index(eid)
    return (ids[i - 1] if i > 0 else None), (ids[i + 1] if i + 1 < len(ids) else None)


# ------------------------------------------------------------------ video variantlari
def set_variant(quality, movie_id=None, episode_id=None, file_id=None, ftype=None, external_url=None, label=None):
    if quality not in QUALITIES or bool(movie_id) == bool(episode_id):
        raise ValueError("invalid")
    if external_url is not None and not re.match(r"https://[^\s]+$", external_url):
        raise ValueError("url")
    col, pid = ("movie_id", movie_id) if movie_id else ("episode_id", episode_id)
    with db.tx() as t:
        cur = t.one(f"SELECT * FROM video_variants WHERE {col}=? AND quality=?", (pid, quality))
        if cur:
            sets, args = [], []
            for f, v in (("file_id", file_id), ("ftype", ftype), ("external_url", external_url), ("label", label)):
                if v is not None:
                    sets.append(f"{f}=?")
                    args.append(v)
            if sets:
                t.exec(f"UPDATE video_variants SET {', '.join(sets)} WHERE id=?", (*args, cur["id"]))
            vid = cur["id"]
        else:
            vid = t.insert(f"INSERT INTO video_variants({col},quality,label,file_id,ftype,external_url,created_at)"
                           " VALUES(?,?,?,?,?,?,?)", (pid, quality, label, file_id, ftype, external_url, now()))
        return t.one("SELECT * FROM video_variants WHERE id=?", (vid,))


def list_variants(movie_id=None, episode_id=None):
    col, pid = ("movie_id", movie_id) if movie_id else ("episode_id", episode_id)
    rows = db.q(f"SELECT * FROM video_variants WHERE {col}=? ORDER BY quality", (pid,))
    return [r for r in rows if r["file_id"] or r["external_url"]]


def get_variant(vid):
    return db.one("SELECT * FROM video_variants WHERE id=?", (vid,))


def resolve_variant(variants, premium):
    """Oddiy foydalanuvchi -> 'medium', Premium -> 'high'. Yo'q bo'lsa tushuntirish uchun alternativ qaytariladi."""
    by = {v["quality"]: v for v in variants}
    want = "high" if premium else "medium"
    if want in by:
        return {"variant": by[want], "wanted": want, "alternative": None, "premium_required": False}
    if premium:
        return {"variant": None, "wanted": want, "alternative": by.get("medium"), "premium_required": False}
    return {"variant": None, "wanted": want, "alternative": None, "premium_required": "high" in by}


def web_variant(movie_id=None, episode_id=None):
    """Saytda ochiq ko'rsatish uchun faqat 'medium' sifatdagi tashqi havola (Premium sifati ochilmaydi)."""
    for v in list_variants(movie_id, episode_id):
        if v["quality"] == "medium" and v["external_url"]:
            return v
    return None


def has_web_source(movie):
    if movie["kind"] == "movie":
        return web_variant(movie_id=movie["id"]) is not None
    return any(web_variant(episode_id=e["id"]) for e in list_episodes(movie["id"]))


# ------------------------------------------------------------------ sevimlilar va tarix
def toggle_favorite(uid, mid):
    with db.tx() as t:
        if t.exec("DELETE FROM favorites WHERE user_id=? AND movie_id=?", (uid, mid)):
            return False
        t.exec("INSERT INTO favorites(user_id,movie_id,created_at) VALUES(?,?,?) ON CONFLICT DO NOTHING",
               (uid, mid, now()))
        return True


def is_favorite(uid, mid):
    return db.one("SELECT 1 AS x FROM favorites WHERE user_id=? AND movie_id=?", (uid, mid)) is not None


def list_favorites(uid, page=0, per=8):
    total = db.one("SELECT COUNT(*) AS c FROM favorites f JOIN movies m ON m.id=f.movie_id "
                   "WHERE f.user_id=? AND m.published=1", (uid,))["c"]
    items = db.q("SELECT m.* FROM favorites f JOIN movies m ON m.id=f.movie_id WHERE f.user_id=? AND m.published=1 "
                 "ORDER BY f.created_at DESC LIMIT ? OFFSET ?", (uid, per, page * per))
    return items, total


def record_view(uid, mid, eid=None):
    with db.tx() as t:
        t.exec("INSERT INTO history(user_id,movie_id,episode_id,watched_at) VALUES(?,?,?,?)", (uid, mid, eid, now()))
        t.exec("UPDATE movies SET views=views+1 WHERE id=?", (mid,))
        if eid:
            t.exec("UPDATE episodes SET views=views+1 WHERE id=?", (eid,))


def list_history(uid, limit=10):
    return db.q("SELECT h.watched_at, m.id AS movie_id, m.title, m.code, m.kind, e.season, e.number "
                "FROM history h JOIN movies m ON m.id=h.movie_id LEFT JOIN episodes e ON e.id=h.episode_id "
                "WHERE h.user_id=? ORDER BY h.id DESC LIMIT ?", (uid, limit))


# ------------------------------------------------------------------ sponsor
def add_sponsor(text, url=None):
    text = (text or "").strip()
    if not text or len(text) > 1000:
        raise ValueError("text")
    if url and not re.match(r"https?://\S+$", url):
        raise ValueError("url")
    with db.tx() as t:
        return t.insert("INSERT INTO sponsors(text,url,enabled,created_at) VALUES(?,?,1,?)",
                        (text, url or None, now()))


def list_sponsors():
    return db.q("SELECT * FROM sponsors ORDER BY id")


def toggle_sponsor(sid):
    db.execute("UPDATE sponsors SET enabled=1-enabled WHERE id=?", (sid,))


def delete_sponsor(sid):
    return db.execute("DELETE FROM sponsors WHERE id=?", (sid,)) > 0


def pick_sponsor(u):
    """Premium foydalanuvchiga reklama berilmaydi; oddiylarga cooldown bilan bittadan."""
    if is_premium(u):
        return None
    cd = get_int_setting("sponsor_cooldown_min") * 60
    if (u.get("last_sponsor_at") or 0) + cd > now():
        return None
    rows = db.q("SELECT * FROM sponsors WHERE enabled=1")
    if not rows:
        return None
    db.execute("UPDATE users SET last_sponsor_at=? WHERE id=?", (now(), u["id"]))
    return random.choice(rows)


# ------------------------------------------------------------------ statistika
def stats():
    n = now()
    one = db.one
    s = {
        "users": one("SELECT COUNT(*) AS c FROM users")["c"],
        "active24": one("SELECT COUNT(*) AS c FROM users WHERE last_seen>?", (n - 86400,))["c"],
        "active7": one("SELECT COUNT(*) AS c FROM users WHERE last_seen>?", (n - 7 * 86400,))["c"],
        "premium_active": one("SELECT COUNT(*) AS c FROM users WHERE premium_until>?", (n,))["c"],
        "premium_expired": one("SELECT COUNT(*) AS c FROM users WHERE premium_until>0 AND premium_until<=?", (n,))["c"],
        "views": one("SELECT COALESCE(SUM(views),0) AS c FROM movies")["c"],
        "revenue": one("SELECT COALESCE(SUM(amount),0) AS c FROM payments WHERE status='approved'")["c"],
        "pending": one("SELECT COUNT(*) AS c FROM payments WHERE status='pending'")["c"],
        "rejected": one("SELECT COUNT(*) AS c FROM payments WHERE status='rejected'")["c"],
        "movies": one("SELECT COUNT(*) AS c FROM movies")["c"],
    }
    s["popular"] = db.q("SELECT code,title,views FROM movies ORDER BY views DESC, id DESC LIMIT 5")
    days = {}
    for r in db.q("SELECT joined_at FROM users WHERE joined_at>?", (n - 7 * 86400,)):
        d = fmt_date(r["joined_at"])
        days[d] = days.get(d, 0) + 1
    s["new_by_day"] = sorted(days.items(), reverse=True)
    return s


# ------------------------------------------------------------------ broadcast
def create_broadcast(admin_id, src_chat, src_msg):
    with db.tx() as t:
        return t.insert("INSERT INTO broadcasts(admin_id,src_chat,src_msg,status,created_at) VALUES(?,?,?,?,?)",
                        (admin_id, src_chat, src_msg, "draft", now()))


def get_broadcast(bid):
    return db.one("SELECT * FROM broadcasts WHERE id=?", (bid,))


def start_broadcast(bid):
    """draft -> sending (atomik; ikki marta yuborilmaydi)."""
    return db.execute("UPDATE broadcasts SET status='sending' WHERE id=? AND status='draft'", (bid,)) == 1


def finish_broadcast(bid, total, sent, failed, skipped):
    db.execute("UPDATE broadcasts SET status='done', total=?, sent=?, failed=?, skipped=? WHERE id=?",
               (total, sent, failed, skipped, bid))


def eligible_user_ids():
    return [r["id"] for r in db.q("SELECT id FROM users WHERE blocked=0 AND bot_blocked=0 ORDER BY id")]


# ------------------------------------------------------------------ holat va update dedup
def get_state(uid):
    r = db.one("SELECT state,data FROM user_state WHERE user_id=?", (uid,))
    if not r:
        return None, {}
    try:
        return r["state"], json.loads(r["data"] or "{}")
    except ValueError:
        return r["state"], {}


def set_state(uid, state, data=None):
    db.execute("INSERT INTO user_state(user_id,state,data) VALUES(?,?,?) "
               "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, data=excluded.data",
               (uid, state, json.dumps(data or {})))


def clear_state(uid):
    db.execute("DELETE FROM user_state WHERE user_id=?", (uid,))


def claim_update(update_id):
    """True = birinchi marta ko'rilmoqda; False = takroriy update (Telegram qayta yuborgan)."""
    return db.execute("INSERT INTO processed_updates(update_id,at) VALUES(?,?) ON CONFLICT DO NOTHING",
                      (update_id, now())) == 1


def release_update(update_id):
    """Ishlov berishdan oldin xato chiqqan update'ni qayta urinish uchun bo'shatadi."""
    return db.execute("DELETE FROM processed_updates WHERE update_id=?", (update_id,)) > 0


def cleanup_updates(older_than=3 * 86400):
    return db.execute("DELETE FROM processed_updates WHERE at<?", (now() - older_than,))
