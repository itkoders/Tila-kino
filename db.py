# -*- coding: utf-8 -*-
"""Yengil DB qatlami: SQLite (dev/test) va PostgreSQL (production, psycopg2).
SQL '?' belgili yoziladi, PostgreSQL uchun avtomatik '%s' ga o'giriladi.
Vaqt: UTC epoch (butun son). Foydalanuvchiga ko'rsatishda Asia/Tashkent."""
import contextlib
import sqlite3
import threading

from config import cfg

IS_PG = False
_url = None
_lock = threading.Lock()

SCHEMA_VERSION = 1

_DDL = [
    """CREATE TABLE IF NOT EXISTS users(
        id BIGINT PRIMARY KEY, first_name TEXT, username TEXT, lang TEXT DEFAULT 'uz',
        joined_at BIGINT, last_seen BIGINT, blocked INTEGER DEFAULT 0, bot_blocked INTEGER DEFAULT 0,
        premium_until BIGINT DEFAULT 0, remind3_for BIGINT DEFAULT 0, remind0_for BIGINT DEFAULT 0,
        referrer_id BIGINT, ref_count INTEGER DEFAULT 0, last_sponsor_at BIGINT DEFAULT 0, created_at BIGINT)""",
    """CREATE TABLE IF NOT EXISTS movies(
        id {PK}, code TEXT NOT NULL UNIQUE, kind TEXT NOT NULL DEFAULT 'movie', title TEXT NOT NULL,
        poster_file_id TEXT, year INTEGER, country TEXT, genre TEXT, language TEXT, description TEXT,
        rating REAL, published INTEGER DEFAULT 1, views INTEGER DEFAULT 0, created_at BIGINT)""",
    """CREATE TABLE IF NOT EXISTS episodes(
        id {PK}, series_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
        season INTEGER NOT NULL DEFAULT 1, number INTEGER NOT NULL, title TEXT, description TEXT,
        published INTEGER DEFAULT 1, views INTEGER DEFAULT 0, created_at BIGINT,
        UNIQUE(series_id, season, number))""",
    """CREATE TABLE IF NOT EXISTS video_variants(
        id {PK}, movie_id INTEGER REFERENCES movies(id) ON DELETE CASCADE,
        episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
        quality TEXT NOT NULL, label TEXT, file_id TEXT, ftype TEXT, external_url TEXT, created_at BIGINT,
        UNIQUE(movie_id, quality), UNIQUE(episode_id, quality))""",
    """CREATE TABLE IF NOT EXISTS favorites(
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
        created_at BIGINT, PRIMARY KEY(user_id, movie_id))""",
    """CREATE TABLE IF NOT EXISTS history(
        id {PK}, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
        episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE, watched_at BIGINT)""",
    """CREATE TABLE IF NOT EXISTS payments(
        id {PK}, user_id BIGINT NOT NULL REFERENCES users(id), plan_key TEXT, days INTEGER, amount INTEGER,
        status TEXT NOT NULL DEFAULT 'pending', reference TEXT NOT NULL UNIQUE, proof_file_id TEXT,
        provider TEXT, provider_txn TEXT UNIQUE, created_at BIGINT, decided_at BIGINT, decided_by BIGINT)""",
    """CREATE TABLE IF NOT EXISTS subscriptions(
        id {PK}, user_id BIGINT NOT NULL REFERENCES users(id), days INTEGER, starts_at BIGINT,
        expires_at BIGINT, source TEXT, payment_id INTEGER UNIQUE REFERENCES payments(id), active INTEGER DEFAULT 1)""",
    """CREATE TABLE IF NOT EXISTS admins(
        user_id BIGINT PRIMARY KEY, role TEXT, perms TEXT, added_by BIGINT, added_at BIGINT)""",
    "CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)",
    """CREATE TABLE IF NOT EXISTS sponsors(
        id {PK}, text TEXT NOT NULL, url TEXT, enabled INTEGER DEFAULT 1, created_at BIGINT)""",
    """CREATE TABLE IF NOT EXISTS broadcasts(
        id {PK}, admin_id BIGINT, src_chat BIGINT, src_msg BIGINT, status TEXT DEFAULT 'draft',
        total INTEGER DEFAULT 0, sent INTEGER DEFAULT 0, failed INTEGER DEFAULT 0, skipped INTEGER DEFAULT 0,
        created_at BIGINT)""",
    """CREATE TABLE IF NOT EXISTS audit_log(
        id {PK}, admin_id BIGINT, action TEXT, details TEXT, at BIGINT)""",
    "CREATE TABLE IF NOT EXISTS user_state(user_id BIGINT PRIMARY KEY, state TEXT, data TEXT)",
    "CREATE TABLE IF NOT EXISTS processed_updates(update_id BIGINT PRIMARY KEY, at BIGINT)",
    "CREATE INDEX IF NOT EXISTS ix_movies_title ON movies(title)",
    "CREATE INDEX IF NOT EXISTS ix_movies_kind_created ON movies(kind, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_episodes_series ON episodes(series_id)",
    "CREATE INDEX IF NOT EXISTS ix_history_user ON history(user_id, watched_at)",
    "CREATE INDEX IF NOT EXISTS ix_payments_user ON payments(user_id)",
    "CREATE INDEX IF NOT EXISTS ix_payments_status ON payments(status)",
    "CREATE INDEX IF NOT EXISTS ix_users_premium ON users(premium_until)",
]


def init(url=None):
    """DB manzilini o'rnatadi (test uchun qayta chaqirish mumkin)."""
    global IS_PG, _url
    url = url or cfg.database_url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    IS_PG = url.startswith("postgresql")
    _url = url


def _connect():
    if IS_PG:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(
            _url,
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=15,
        )

    path = _url.replace("sqlite:///", "", 1) if _url.startswith("sqlite:///") else _url
    if not path:
        raise RuntimeError("DATABASE_URL SQLite manzili bo'sh")
    # SQLite papkasi mavjud bo'lmasa, ulanishdan oldin yaratish.
    # :memory: va URI rejimlari fayl papkasini talab qilmaydi.
    if path != ":memory:" and not path.startswith("file:"):
        import os
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)

    con = sqlite3.connect(path, timeout=30, check_same_thread=False, uri=path.startswith("file:"))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=30000")
    # WAL diskka yozishni talab qiladi; xato bo'lsa DB ulanishini yiqitmaymiz.
    if path != ":memory:" and not path.startswith("file::memory:"):
        try:
            con.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
    return con


class Tx:
    def __init__(self, conn):
        self.conn = conn

    def _s(self, sql):
        return sql.replace("?", "%s") if IS_PG else sql

    def _run(self, sql, args):
        cur = self.conn.cursor()
        cur.execute(self._s(sql), tuple(args))
        return cur

    def q(self, sql, args=()):
        cur = self._run(sql, args)
        return [dict(r) for r in cur.fetchall()]

    def one(self, sql, args=()):
        rows = self.q(sql, args)
        return rows[0] if rows else None

    def exec(self, sql, args=()):
        return self._run(sql, args).rowcount

    def insert(self, sql, args=()):
        cur = self._run(sql + " RETURNING id", args)
        return cur.fetchone()["id"]


@contextlib.contextmanager
def tx():
    conn = _connect()
    try:
        yield Tx(conn)
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def q(sql, args=()):
    with tx() as t:
        return t.q(sql, args)


def one(sql, args=()):
    with tx() as t:
        return t.one(sql, args)


def execute(sql, args=()):
    with tx() as t:
        return t.exec(sql, args)


def _table_columns(t, table):
    """Mavjud jadval ustunlarini SQLite/PostgreSQL uchun bir xil qaytaradi."""
    if IS_PG:
        rows = t.q(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema=current_schema() AND table_name=?",
            (table,),
        )
        return {r["column_name"] for r in rows}
    return {r["name"] for r in t.q("PRAGMA table_info(" + table + ")")}


# Eski deploylarda CREATE TABLE IF NOT EXISTS jadvalni yangilamaydi.
# Shu xarita mavjud jadvallarga keyingi kod kutadigan ustunlarni xavfsiz qo'shadi.
_MIGRATION_COLUMNS = {
    "users": {
        "id": "BIGINT", "first_name": "TEXT", "username": "TEXT",
        "lang": "TEXT DEFAULT 'uz'", "joined_at": "BIGINT", "last_seen": "BIGINT",
        "blocked": "INTEGER DEFAULT 0", "bot_blocked": "INTEGER DEFAULT 0",
        "premium_until": "BIGINT DEFAULT 0", "remind3_for": "BIGINT DEFAULT 0",
        "remind0_for": "BIGINT DEFAULT 0", "referrer_id": "BIGINT",
        "ref_count": "INTEGER DEFAULT 0", "last_sponsor_at": "BIGINT DEFAULT 0",
        "created_at": "BIGINT",
    },
    "movies": {
        "code": "TEXT", "kind": "TEXT DEFAULT 'movie'", "title": "TEXT",
        "poster_file_id": "TEXT", "year": "INTEGER", "country": "TEXT",
        "genre": "TEXT", "language": "TEXT", "description": "TEXT",
        "rating": "REAL", "published": "INTEGER DEFAULT 1", "views": "INTEGER DEFAULT 0",
        "created_at": "BIGINT",
    },
    "episodes": {
        "series_id": "INTEGER", "season": "INTEGER DEFAULT 1", "number": "INTEGER DEFAULT 1",
        "title": "TEXT", "description": "TEXT", "published": "INTEGER DEFAULT 1",
        "views": "INTEGER DEFAULT 0", "created_at": "BIGINT",
    },
    "video_variants": {
        "movie_id": "INTEGER", "episode_id": "INTEGER", "quality": "TEXT DEFAULT 'medium'",
        "label": "TEXT", "file_id": "TEXT", "ftype": "TEXT", "external_url": "TEXT",
        "created_at": "BIGINT",
    },
    "favorites": {"user_id": "BIGINT", "movie_id": "INTEGER", "created_at": "BIGINT"},
    "history": {
        "user_id": "BIGINT", "movie_id": "INTEGER", "episode_id": "INTEGER", "watched_at": "BIGINT",
    },
    "payments": {
        "user_id": "BIGINT", "plan_key": "TEXT", "days": "INTEGER", "amount": "INTEGER",
        "status": "TEXT DEFAULT 'pending'", "reference": "TEXT", "proof_file_id": "TEXT",
        "provider": "TEXT", "provider_txn": "TEXT", "created_at": "BIGINT",
        "decided_at": "BIGINT", "decided_by": "BIGINT",
    },
    "subscriptions": {
        "user_id": "BIGINT", "days": "INTEGER", "starts_at": "BIGINT", "expires_at": "BIGINT",
        "source": "TEXT", "payment_id": "INTEGER", "active": "INTEGER DEFAULT 1",
    },
    "admins": {"user_id": "BIGINT", "role": "TEXT", "perms": "TEXT", "added_by": "BIGINT", "added_at": "BIGINT"},
    "settings": {"key": "TEXT", "value": "TEXT"},
    "sponsors": {"text": "TEXT", "url": "TEXT", "enabled": "INTEGER DEFAULT 1", "created_at": "BIGINT"},
    "broadcasts": {
        "admin_id": "BIGINT", "src_chat": "BIGINT", "src_msg": "BIGINT",
        "status": "TEXT DEFAULT 'draft'", "total": "INTEGER DEFAULT 0",
        "sent": "INTEGER DEFAULT 0", "failed": "INTEGER DEFAULT 0",
        "skipped": "INTEGER DEFAULT 0", "created_at": "BIGINT",
    },
    "audit_log": {"admin_id": "BIGINT", "action": "TEXT", "details": "TEXT", "at": "BIGINT"},
    "user_state": {"user_id": "BIGINT", "state": "TEXT", "data": "TEXT"},
    "processed_updates": {"update_id": "BIGINT", "at": "BIGINT"},
}


def _migrate_existing_schema():
    """Eski sxemalarni yo'qotishsiz kengaytiradi; jadvallar yoki yozuvlarni o'chirmaydi."""
    with tx() as t:
        # Eski users sxemasida telegram_id ishlatilgan bo'lishi mumkin.
        cols = _table_columns(t, "users")
        if "telegram_id" in cols and "id" not in cols:
            if IS_PG:
                t.exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS id BIGINT")
            else:
                t.exec("ALTER TABLE users ADD COLUMN id BIGINT")
            cols.add("id")
        if "telegram_id" in cols and "id" in cols:
            t.exec("UPDATE users SET id=telegram_id WHERE id IS NULL")
        if "created_at" in cols and "joined_at" not in cols:
            if IS_PG:
                t.exec("ALTER TABLE users ADD COLUMN IF NOT EXISTS joined_at BIGINT")
            else:
                t.exec("ALTER TABLE users ADD COLUMN joined_at BIGINT")
            t.exec("UPDATE users SET joined_at=created_at WHERE joined_at IS NULL")

        for table, columns in _MIGRATION_COLUMNS.items():
            existing = _table_columns(t, table)
            for column, definition in columns.items():
                if column in existing:
                    continue
                if IS_PG:
                    t.exec(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}")
                else:
                    t.exec(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            # Eski ma'lumotlardan mavjud vaqt ustunlarini to'ldirish.
            existing = _table_columns(t, table)
            if table == "users":
                if "created_at" in existing and "joined_at" in existing:
                    t.exec("UPDATE users SET joined_at=COALESCE(joined_at, created_at)")
                if "joined_at" in existing and "created_at" in existing:
                    t.exec("UPDATE users SET created_at=COALESCE(created_at, joined_at)")
            elif "created_at" in existing:
                source = "watched_at" if table == "history" else ("at" if table == "audit_log" else None)
                if source and source in existing:
                    t.exec(f"UPDATE {table} SET created_at=COALESCE(created_at, {source})")
        if not IS_PG:
            t.exec("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_id_compat ON users(id)")


def init_schema():
    """Jadvallarni yaratadi va eski deploy sxemasini migratsiya qiladi."""
    pk = "SERIAL PRIMARY KEY" if IS_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with _lock:
        with tx() as t:
            for stmt in _DDL:
                t.exec(stmt.replace("{PK}", pk))
            t.exec(
                "INSERT INTO settings(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO NOTHING",
                (str(SCHEMA_VERSION),),
            )
        _migrate_existing_schema()


def drop_all_for_tests():
    for name in ("history", "favorites", "video_variants", "episodes", "subscriptions", "payments",
                 "movies", "users", "admins", "settings", "sponsors", "broadcasts", "audit_log",
                 "user_state", "processed_updates"):
        execute("DROP TABLE IF EXISTS " + name)
