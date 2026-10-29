# -*- coding: utf-8 -*-
"""Admin panel. Ruxsat HAR DOIM Telegram yuborgan raqamli ID bo'yicha tekshiriladi (services.is_admin / has_perm).
Foydalanuvchi matnida yozilgan ID hech qachon ishonchli deb hisoblanmaydi."""
import logging
import threading
import time

import services as sv
import tg
import ui
from config import cfg
from ui import esc, ikb, show

log = logging.getLogger("tilakino.admin")
sleep = time.sleep
RATE_DELAY = 0.05          # soniyasiga ~20 xabar (Telegram limiti ~30)
BROADCAST_THREAD = True    # testlarda False

ERR = {"code_format": "Kod faqat raqamlardan (1–12 ta) iborat bo'lishi kerak", "code_taken": "Bu kod band",
       "title": "Nom bo'sh yoki juda uzun", "year": "Yil 1888–2100 oralig'ida bo'lsin", "rating": "Reyting 0–10 oralig'ida",
       "lang": "Til: uz, ru, en, tg (vergul bilan)", "numbers": "To'g'ri raqam kiriting",
       "episode_exists": "Bunday fasl/epizod raqami allaqachon bor", "url": "https:// bilan boshlanuvchi havola kerak",
       "user_not_found": "Foydalanuvchi topilmadi (u botga /start bosgan bo'lishi kerak)",
       "invalid": "Noto'g'ri qiymat", "owner": "Asosiy administratorga bu amal qo'llanmaydi",
       "not_found": "Topilmadi", "no_perms": "Kamida bitta ruxsat kerak", "not_series": "Bu serial emas",
       "field": "Noma'lum maydon", "text": "Matn bo'sh yoki juda uzun", "promo_format": "Promo-kod 3–24 ta lotin harfi/raqamdan iborat bo'lsin", "promo_taken": "Bu promo-kod oldin yaratilgan"}

PERM_OF = {"mov": "catalog", "addm": "catalog", "find": "catalog", "list": "catalog", "mc": "catalog",
           "me": "catalog", "mp": "catalog", "mv": "catalog", "ml": "catalog", "mt": "catalog", "md": "catalog",
           "ep": "catalog", "eps": "catalog", "ec": "catalog", "ee": "catalog", "ev": "catalog", "el": "catalog",
           "et": "catalog", "ed": "catalog",
           "prem": "premium", "pl": "premium", "ppe": "premium", "pg": "premium", "pr": "premium", "px": "premium",
           "pa": "premium", "pxl": "premium", "pp": "premium", "ph": "premium", "pcard": "premium",
           "usr": "users", "us": "users", "uc": "users", "ub": "users",
           "spn": "sponsor", "sub": "sponsor", "spa": "sponsor", "spt": "sponsor", "spd": "sponsor", "spc": "sponsor", "promos": "premium", "promonew": "premium", "promot": "premium",
           "st": "stats", "bc": "broadcast", "bcok": "broadcast",
           "hlp": "owner", "hla": "owner", "hlr": "owner", "au": "owner"}
ACTION_PERM = {"dm": "catalog", "de": "catalog", "pv": "premium", "sd": "sponsor", "hr": "owner"}
STATE_PERM = {"addm": "catalog", "adde": "catalog", "edit": "catalog", "media": "catalog", "find": "catalog",
              "pset": "premium", "pgrant": "premium", "prevoke": "premium", "pexpiry": "premium",
              "cardinfo": "premium", "promocreate": "premium", "usearch": "users", "spadd": "sponsor", "subset": "sponsor", "spcool": "sponsor",
              "bc": "broadcast", "hladd": "owner", "hladd_all": "owner", "hladd_catalog": "owner", "hladd_premium": "owner", "hladd_users": "owner", "hladd_sponsor": "owner", "hladd_stats": "owner", "hladd_broadcast": "owner"}

WIZ_MOVIE = [("title", "🎬 <b>Nomi</b>"),
             ("year", "📅 Chiqqan yili (yoki <code>-</code>)"), ("country", "🌍 Davlat (yoki <code>-</code>)"),
             ("genre", "🎭 Janr (yoki <code>-</code>)"),
             ("language", "🗣 Til: <code>uz</code>, <code>ru</code>, <code>en</code>, <code>tg</code> (vergul bilan, yoki <code>-</code>)"),
             ("description", "📝 Tavsif (yoki <code>-</code>)"), ("rating", "⭐ Reyting 0–10 (yoki <code>-</code>)"),
             ("poster", "🖼 <b>Poster</b> rasmini yuboring (yoki <code>-</code>)")]
WIZ_EP = [("season", "🔢 Fasl raqami (masalan: 1)"), ("number", "🔢 Epizod raqami"),
          ("title", "📝 Epizod nomi (yoki <code>-</code>)"), ("description", "📝 Tavsif (yoki <code>-</code>)")]
FIELD_NAMES = {"title": "nom", "year": "yil", "country": "davlat", "genre": "janr", "language": "til (uz,ru,en,tg)",
               "description": "tavsif", "rating": "reyting (0–10)", "code": "yangi kod", "number": "epizod raqami",
               "season": "fasl raqami"}


# ------------------------------------------------------------------ umumiy
def prompt(chat, text):
    return tg.send_message(chat, text, ikb([[("❌ Bekor qilish", "a:cancel")]]))


def back_row(to="a:home"):
    return [("⬅️ Orqaga", to), ("🏠 Admin", "a:home")]


def panel(chat, msg):
    perms = sv.admin_perms(chat)
    items = [("catalog", "🎬 Kino va seriallar", "a:mov"), ("premium", "💎 Premium", "a:prem"),
             ("users", "👥 Foydalanuvchilar", "a:usr"), ("sponsor", "📢 Homiy xabarlar", "a:spn"),
             ("sponsor", "🔒 Majburiy obuna", "a:sub"), ("stats", "📊 Statistika", "a:st"), ("broadcast", "📣 Xabar yuborish", "a:bc")]
    btns = [(label, cb) for perm, label, cb in items if perm in perms]
    if sv.is_owner(chat):
        btns += [("🛡 Yordamchi adminlar", "a:hlp"), ("🧾 Audit jurnali", "a:au")]
    rows = [btns[i:i + 2] for i in range(0, len(btns), 2)]
    rows.append([("🏠 Bosh menyu", "menu")])
    show(chat, msg, "🛠 <b>Admin panel</b>", ikb(rows))


# ------------------------------------------------------------------ callback
def callback(ctx, parts):
    uid = ctx.uid
    cmd = parts[1] if len(parts) > 1 else "home"
    args = parts[2:]
    need = ACTION_PERM.get(args[0]) if cmd == "do" and args else PERM_OF.get(cmd)
    if need == "owner":
        if not sv.is_owner(uid):
            return ctx.ans("⛔️ Faqat asosiy administrator", True)
    elif need and not sv.has_perm(uid, need):
        return ctx.ans("⛔️ Bu bo'limga ruxsatingiz yo'q", True)
    fn = HANDLERS.get(cmd)
    if not fn:
        return ctx.ans()
    try:
        fn(ctx, args)
    except ValueError as e:
        ctx.ans(ERR.get(str(e), "Noto'g'ri qiymat"), True)


def cb_home(ctx, a):
    ctx.ans()
    sv.clear_state(ctx.uid)
    panel(ctx.chat, ctx.msg)


def cb_cancel(ctx, a):
    ctx.ans("Bekor qilindi")
    sv.clear_state(ctx.uid)
    try:
        tg.delete_message(ctx.chat, ctx.msg["message_id"])
    except tg.TgError:
        pass
    panel(ctx.chat, None)


# ------------------------------------------------------------------ kino boshqaruvi
def cb_mov(ctx, a):
    ctx.ans()
    show(ctx.chat, ctx.msg, "🎬 <b>Kino va seriallar</b>", ikb([
        [("➕ Kino qo'shish", "a:addm:movie"), ("➕ Serial qo'shish", "a:addm:series")],
        [("🔍 Kod/nom bo'yicha topish", "a:find"), ("📋 Barcha yozuvlar", "a:list:0")],
        back_row()]))


def cb_list(ctx, a):
    ctx.ans()
    page = int(a[0])
    items, total = sv.list_catalog(None, page, ui.PER_PAGE, published_only=False)
    rows = [[(("🙈 " if not m["published"] else "") + f"{m['code']} · {m['title']}", f"a:mc:{m['id']}")] for m in items]
    rows.append(ui.pager("a:list", page, total))
    rows.append(back_row("a:mov"))
    show(ctx.chat, ctx.msg, f"📋 <b>Yozuvlar</b> ({total})", ikb(rows))


def cb_find(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "find")
    prompt(ctx.chat, "🔍 Kino kodi yoki nomini yuboring:")


def movie_card_text(m):
    vs = db_variants(m["id"], None)
    lines = [f"{'📺' if m['kind'] == 'series' else '🎬'} <b>{esc(m['title'])}</b> — <code>{esc(m['code'])}</code>",
             f"Holat: {'✅ nashr etilgan' if m['published'] else '🙈 yashirin'}  |  👁 {m['views']}",
             f"📅 {m['year'] or '—'} | 🌍 {esc(m['country'] or '—')} | 🎭 {esc(m['genre'] or '—')}",
             f"🗣 {m['language'] or '—'} | ⭐ {m['rating'] if m['rating'] is not None else '—'}",
             f"🖼 Poster: {'bor' if m['poster_file_id'] else 'yo‘q'}"]
    if m["kind"] == "movie":
        lines.append("📀 Video: " + (", ".join(vs) if vs else "yo‘q"))
    else:
        lines.append(f"📺 Epizodlar: {len(sv.list_episodes(m['id'], published_only=False))}")
    if m["description"]:
        lines.append("\n" + esc(m["description"][:400]))
    return "\n".join(lines)


def db_variants(movie_id, episode_id):
    out = []
    for v in sv.list_variants(movie_id=movie_id, episode_id=episode_id):
        kind = []
        if v["file_id"]:
            kind.append("fayl")
        if v["external_url"]:
            kind.append("havola")
        out.append(f"{v['quality']}({'+'.join(kind)})")
    return out


def movie_card(chat, msg, mid):
    m = sv.get_movie(mid)
    if not m:
        return show(chat, msg, "Topilmadi", ikb([back_row("a:mov")]))
    rows = [[("✏️ Nom", f"a:me:{mid}:title"), ("✏️ Yil", f"a:me:{mid}:year"), ("✏️ Davlat", f"a:me:{mid}:country")],
            [("✏️ Janr", f"a:me:{mid}:genre"), ("✏️ Til", f"a:me:{mid}:language"), ("✏️ Tavsif", f"a:me:{mid}:description")],
            [("✏️ Reyting", f"a:me:{mid}:rating"), ("🔢 Kod", f"a:me:{mid}:code"), ("🖼 Poster", f"a:mp:{mid}")]]
    if m["kind"] == "movie":
        rows.append([("📀 Medium video", f"a:mv:{mid}:medium"), ("💎 High video", f"a:mv:{mid}:high")])
        rows.append([("🔗 Medium havola", f"a:ml:{mid}:medium"), ("🔗 High havola", f"a:ml:{mid}:high")])
    else:
        rows.append([("➕ Epizod", f"a:ep:{mid}"), ("📺 Epizodlar", f"a:eps:{mid}:0")])
    rows.append([("🙈 Yashirish" if m["published"] else "✅ Nashr etish", f"a:mt:{mid}"), ("🗑 O'chirish", f"a:md:{mid}")])
    rows.append(back_row("a:list:0"))
    show(chat, msg, movie_card_text(m), ikb(rows))


def cb_mc(ctx, a):
    ctx.ans()
    movie_card(ctx.chat, ctx.msg, int(a[0]))


def cb_addm(ctx, a):
    if a[0] not in ("movie", "series"):
        raise ValueError("invalid")
    ctx.ans()
    sv.set_state(ctx.uid, "addm", {"kind": a[0], "i": 0, "v": {}})
    prompt(ctx.chat, WIZ_MOVIE[0][1])


def cb_me(ctx, a):
    mid, field = int(a[0]), a[1]
    if field not in sv.EDITABLE or field == "poster_file_id" or not sv.get_movie(mid):
        raise ValueError("field")
    ctx.ans()
    sv.set_state(ctx.uid, "edit", {"t": "movie", "id": mid, "f": field})
    prompt(ctx.chat, f"✏️ Yangi qiymat ({FIELD_NAMES.get(field, field)}). Bo'shatish uchun <code>-</code>:")


def cb_media(ctx, a):
    """mp: poster, mv/ml: kino video/havola, ev/el: epizod video/havola."""
    kind = ctx.data.split(":")[1]
    pid = int(a[0])
    q = a[1] if len(a) > 1 else None
    if kind in ("mv", "ml", "ev", "el") and q not in sv.QUALITIES:
        raise ValueError("invalid")
    if kind in ("mp", "mv", "ml") and not sv.get_movie(pid):
        raise ValueError("not_found")
    if kind in ("ev", "el") and not sv.get_episode(pid):
        raise ValueError("not_found")
    ctx.ans()
    sv.set_state(ctx.uid, "media", {"t": kind, "id": pid, "q": q})
    msg = {"mp": "🖼 Poster rasmini yuboring:",
           "mv": f"📀 <b>{q}</b> sifatli videoni (video yoki fayl) yuboring. Izoh yozsangiz u sifat nomi sifatida saqlanadi. "
                 "Faqat o'zingizga tegishli/ruxsat berilgan kontentni yuklang.",
           "ev": f"📀 <b>{q}</b> sifatli epizod videosini yuboring:",
           "ml": f"🔗 <b>{q}</b> sifat uchun ruxsat etilgan tashqi havolani (https://...) yuboring:",
           "el": f"🔗 <b>{q}</b> sifat uchun ruxsat etilgan tashqi havolani (https://...) yuboring:"}[kind]
    prompt(ctx.chat, msg)


def cb_mt(ctx, a):
    m = sv.get_movie(int(a[0]))
    if not m:
        raise ValueError("not_found")
    sv.set_published(m["id"], not m["published"])
    sv.audit(ctx.uid, "movie_publish" if not m["published"] else "movie_unpublish", f"{m['id']}:{m['code']}")
    ctx.ans("✅")
    movie_card(ctx.chat, ctx.msg, m["id"])


def confirm_screen(ctx, text, action, arg, back):
    ctx.ans()
    show(ctx.chat, ctx.msg, f"⚠️ {text}\n\nBu amalni qaytarib bo'lmaydi.",
         ikb([[("✅ Tasdiqlash", f"a:do:{action}:{arg}"), ("❌ Bekor qilish", back)]]))


def cb_md(ctx, a):
    m = sv.get_movie(int(a[0]))
    if not m:
        raise ValueError("not_found")
    confirm_screen(ctx, f"<b>{esc(m['title'])}</b> ({esc(m['code'])}) va unga bog'liq barcha epizod, video, "
                        "sevimli va tarix yozuvlari o'chiriladi.", "dm", m["id"], f"a:mc:{m['id']}")


# ------------------------------------------------------------------ epizodlar
def cb_ep(ctx, a):
    sid = int(a[0])
    m = sv.get_movie(sid)
    if not m or m["kind"] != "series":
        raise ValueError("not_series")
    ctx.ans()
    sv.set_state(ctx.uid, "adde", {"sid": sid, "i": 0, "v": {}})
    prompt(ctx.chat, WIZ_EP[0][1])


def cb_eps(ctx, a):
    ctx.ans()
    sid, page = int(a[0]), int(a[1])
    eps = sv.list_episodes(sid, published_only=False)
    per = ui.PER_PAGE
    rows = [[(("🙈 " if not e["published"] else "") + f"S{e['season']}E{e['number']}" +
              (f" · {e['title']}" if e["title"] else ""), f"a:ec:{e['id']}")] for e in eps[page * per:(page + 1) * per]]
    rows.append(ui.pager(f"a:eps:{sid}", page, len(eps), per))
    rows.append([("➕ Epizod", f"a:ep:{sid}")])
    rows.append(back_row(f"a:mc:{sid}"))
    show(ctx.chat, ctx.msg, f"📺 <b>Epizodlar</b> ({len(eps)})", ikb(rows))


def episode_card(chat, msg, eid):
    e = sv.get_episode(eid)
    if not e:
        return show(chat, msg, "Topilmadi", ikb([back_row("a:mov")]))
    vs = db_variants(None, eid)
    text = (f"📺 S{e['season']}E{e['number']} — <b>{esc(e['title'] or '—')}</b>\n"
            f"Holat: {'✅ nashr etilgan' if e['published'] else '🙈 yashirin'} | 👁 {e['views']}\n"
            f"📀 Video: {', '.join(vs) if vs else 'yo‘q'}")
    if e["description"]:
        text += "\n\n" + esc(e["description"][:400])
    rows = [[("✏️ Nom", f"a:ee:{eid}:title"), ("✏️ Tavsif", f"a:ee:{eid}:description")],
            [("🔢 Epizod raqami (tartib)", f"a:ee:{eid}:number"), ("🔢 Fasl", f"a:ee:{eid}:season")],
            [("📀 Medium video", f"a:ev:{eid}:medium"), ("💎 High video", f"a:ev:{eid}:high")],
            [("🔗 Medium havola", f"a:el:{eid}:medium"), ("🔗 High havola", f"a:el:{eid}:high")],
            [("🙈 Yashirish" if e["published"] else "✅ Nashr etish", f"a:et:{eid}"), ("🗑 O'chirish", f"a:ed:{eid}")],
            back_row(f"a:eps:{e['series_id']}:0")]
    show(chat, msg, text, ikb(rows))


def cb_ec(ctx, a):
    ctx.ans()
    episode_card(ctx.chat, ctx.msg, int(a[0]))


def cb_ee(ctx, a):
    eid, field = int(a[0]), a[1]
    if field not in ("title", "description", "number", "season") or not sv.get_episode(eid):
        raise ValueError("field")
    ctx.ans()
    sv.set_state(ctx.uid, "edit", {"t": "ep", "id": eid, "f": field})
    prompt(ctx.chat, f"✏️ Yangi qiymat ({FIELD_NAMES.get(field, field)}):")


def cb_et(ctx, a):
    e = sv.get_episode(int(a[0]))
    if not e:
        raise ValueError("not_found")
    sv.set_episode_published(e["id"], not e["published"])
    sv.audit(ctx.uid, "episode_toggle", f"{e['id']}")
    ctx.ans("✅")
    episode_card(ctx.chat, ctx.msg, e["id"])


def cb_ed(ctx, a):
    e = sv.get_episode(int(a[0]))
    if not e:
        raise ValueError("not_found")
    confirm_screen(ctx, f"S{e['season']}E{e['number']} epizodi o'chiriladi.", "de", e["id"], f"a:ec:{e['id']}")


# ------------------------------------------------------------------ tasdiqlanadigan (halokatli) amallar
def cb_do(ctx, a):
    action, arg = a[0], int(a[1])
    if action == "dm":
        m = sv.get_movie(arg)
        if not sv.delete_movie(arg):
            raise ValueError("not_found")
        sv.audit(ctx.uid, "movie_delete", f"{arg}:{m['code']}:{m['title']}")
        ctx.ans("🗑 O'chirildi")
        return cb_mov(ctx, [])
    if action == "de":
        e = sv.get_episode(arg)
        if not e or not sv.delete_episode(arg):
            raise ValueError("not_found")
        sv.audit(ctx.uid, "episode_delete", f"{arg}")
        ctx.ans("🗑 O'chirildi")
        return cb_eps(ctx, [str(e["series_id"]), "0"])
    if action == "pv":
        sv.revoke_premium(arg)
        sv.audit(ctx.uid, "premium_revoke", str(arg))
        ctx.ans("✅ Premium bekor qilindi")
        return user_card(ctx.chat, ctx.msg, arg)
    if action == "sd":
        sv.delete_sponsor(arg)
        sv.audit(ctx.uid, "sponsor_delete", str(arg))
        ctx.ans("🗑")
        return cb_spn(ctx, [])
    if action == "hr":
        if not sv.remove_helper(ctx.uid, arg):
            raise ValueError("not_found")
        ctx.ans("✅ Olib tashlandi")
        return cb_hlp(ctx, [])
    ctx.ans()


# ------------------------------------------------------------------ Premium
def cb_prem(ctx, a):
    ctx.ans()
    show(ctx.chat, ctx.msg, "💎 <b>Premium boshqaruvi</b>", ikb([
        [("💰 Narx va muddat", "a:pl"), ("💳 Karta ma'lumoti", "a:pcard")],
        [("🎁 Premium berish", "a:pg"), ("🚫 Premiumni bekor qilish", "a:pr")],
        [("📅 Muddatni belgilash", "a:px")],
        [("🎟 Promo-kodlar", "a:promos")],
        [("✅ Faol obunalar", "a:pa"), ("⌛️ Muddati o'tgan", "a:pxl")],
        [("⏳ Kutilayotgan to'lovlar", "a:pp"), ("🧾 To'lovlar tarixi", "a:ph")],
        back_row()]))


def cb_pl(ctx, a):
    ctx.ans()
    plans = sv.get_plans()
    lines = ["💰 <b>Tariflar</b>", ""] + [f"• {p['label']}: {p['days']} kun — {sv.money(p['price'])} so'm" for p in plans.values()]
    rows = [[(f"✏️ {p['label']} narx", f"a:ppe:{k}:price"), (f"✏️ {p['label']} kun", f"a:ppe:{k}:days")]
            for k, p in plans.items()]
    rows.append(back_row("a:prem"))
    show(ctx.chat, ctx.msg, "\n".join(lines), ikb(rows))


def cb_ppe(ctx, a):
    if a[0] not in sv.get_plans() or a[1] not in ("price", "days"):
        raise ValueError("invalid")
    ctx.ans()
    sv.set_state(ctx.uid, "pset", {"key": a[0], "f": a[1]})
    prompt(ctx.chat, "✏️ Yangi " + ("narx (so'm)" if a[1] == "price" else "muddat (kun)") + " raqamini yuboring:")


def cb_pg(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "pgrant")
    prompt(ctx.chat, "🎁 Format: <code>ID KUN</code> (masalan: <code>123456789 30</code>)")


def cb_pr(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "prevoke")
    prompt(ctx.chat, "🚫 Premium bekor qilinadigan foydalanuvchi ID sini yuboring:")


def cb_px(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "pexpiry")
    prompt(ctx.chat, "📅 Format: <code>ID YYYY-MM-DD</code> (masalan: <code>123456789 2026-12-31</code>). "
                     "O'tgan sana kiritilsa Premium tugatiladi.")


def user_lines(users):
    return [f"• <code>{u['id']}</code> {esc(u['first_name'] or '')} — {sv.fmt_date(u['premium_until'])}" for u in users]


def cb_pa(ctx, a):
    ctx.ans()
    us = sv.list_premium(True)
    show(ctx.chat, ctx.msg, "✅ <b>Faol Premium</b> (tugash sanasi bo'yicha)\n\n" + ("\n".join(user_lines(us)) or "Yo'q"),
         ikb([back_row("a:prem")]))


def cb_pxl(ctx, a):
    ctx.ans()
    us = sv.list_premium(False)
    show(ctx.chat, ctx.msg, "⌛️ <b>Muddati o'tgan Premium</b>\n\n" + ("\n".join(user_lines(us)) or "Yo'q"),
         ikb([back_row("a:prem")]))


def cb_pp(ctx, a):
    ctx.ans()
    pend = sv.list_payments("pending", limit=10)
    if not pend:
        return show(ctx.chat, ctx.msg, "⏳ Kutilayotgan to'lovlar yo'q.", ikb([back_row("a:prem")]))
    show(ctx.chat, ctx.msg, f"⏳ Kutilayotgan to'lovlar: {len(pend)} (quyida alohida yuboriladi)", ikb([back_row("a:prem")]))
    for p in pend:
        cap = (f"💳 <b>#{esc(p['reference'])}</b> — <code>{p['user_id']}</code>\n{p['days']} kun — {sv.money(p['amount'])} so'm\n"
               f"🕒 {sv.fmt_dt(p['created_at'])}" + ("" if p["proof_file_id"] else "\n⚠️ Chek hali yuborilmagan"))
        kb = ikb([[("✅ Tasdiqlash", f"pay:ok:{p['id']}"), ("❌ Rad etish", f"pay:no:{p['id']}")]])
        try:
            if p["proof_file_id"]:
                try:
                    tg.send_photo(ctx.chat, p["proof_file_id"], cap, kb)
                except tg.TgError:
                    tg.send_document(ctx.chat, p["proof_file_id"], cap, kb)
            else:
                tg.send_message(ctx.chat, cap, kb)
        except tg.TgError as e:
            log.warning("to'lov ko'rsatilmadi: %s", e.description)


def cb_ph(ctx, a):
    ctx.ans()
    icon = {"pending": "⏳", "approved": "✅", "rejected": "❌", "expired": "⌛️"}
    ps = sv.list_payments(limit=15)
    lines = [f"{icon.get(p['status'], '•')} {esc(p['reference'])} · <code>{p['user_id']}</code> · {sv.money(p['amount'])} · "
             f"{p['status']} · {sv.fmt_date(p['created_at'])}" for p in ps]
    show(ctx.chat, ctx.msg, "🧾 <b>So'nggi to'lovlar</b>\n\n" + ("\n".join(lines) or "Yo'q"), ikb([back_row("a:prem")]))


def cb_pcard(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "cardinfo")
    cur = sv.get_setting("card_info")
    prompt(ctx.chat, "💳 To'lov rekvizitlarini yuboring (karta raqami, egasi). O'chirish uchun <code>-</code>.\n\n"
                     f"Hozirgi: {esc(cur) if cur else '—'}")


# ------------------------------------------------------------------ foydalanuvchilar
def cb_usr(ctx, a):
    ctx.ans()
    show(ctx.chat, ctx.msg,
         "👥 <b>Foydalanuvchilar</b>\n\nID orqali foydalanuvchi kartasini oching. Kartada username, ID, qo‘shilgan sana, oxirgi faollik, blok holati va Premium muddati ko‘rinadi.",
         ikb([[("🔎 Telegram ID bo‘yicha", "a:us")], back_row()]))


def cb_us(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "usearch")
    prompt(ctx.chat, "🔎 Foydalanuvchining raqamli Telegram ID sini yuboring:")


def user_card(chat, msg, uid):
    u = sv.get_user(uid)
    if not u:
        return show(chat, msg, "Foydalanuvchi topilmadi", ikb([back_row("a:usr")]))
    hist = sv.list_history(uid, 5)
    subs = sv.list_subscriptions(uid, 3)
    pays = sv.list_payments(uid=uid, limit=3)
    lines = [f"👤 <b>{esc(u['first_name'] or '—')}</b> (@{esc(u['username'] or '—')})", f"🆔 <code>{uid}</code>",
             f"📅 Qo'shilgan: {sv.fmt_date(u['joined_at'])} | oxirgi faollik: {sv.fmt_dt(u['last_seen'])}",
             f"🌐 {u['lang']} | 🚫 bloklangan: {'ha' if u['blocked'] else 'yo‘q'} | bot bloklangan: {'ha' if u['bot_blocked'] else 'yo‘q'}",
             f"💎 Premium: {sv.fmt_dt(u['premium_until']) if sv.is_premium(u) else 'yo‘q'} | 👥 takliflar: {u['ref_count']}"]
    if subs:
        lines.append("\n<b>Obunalar:</b>")
        lines += [f"• {s['days']} kun → {sv.fmt_date(s['expires_at'])} ({esc(s['source'] or '')})" for s in subs]
    if pays:
        lines.append("\n<b>To'lovlar:</b>")
        lines += [f"• {esc(p['reference'])} {sv.money(p['amount'])} — {p['status']}" for p in pays]
    if hist:
        lines.append("\n<b>Tomosha tarixi:</b>")
        lines += [f"• {esc(h['title'])}" + (f" S{h['season']}E{h['number']}" if h["season"] else "") for h in hist]
    rows = [[("✅ Blokdan chiqarish" if u["blocked"] else "⛔️ Bloklash", f"a:ub:{uid}")]]
    if sv.is_premium(u):
        rows.append([("🚫 Premiumni bekor qilish", f"a:do:pv:{uid}")])
    rows.append(back_row("a:usr"))
    show(chat, msg, "\n".join(lines), ikb(rows))


def cb_uc(ctx, a):
    ctx.ans()
    user_card(ctx.chat, ctx.msg, int(a[0]))


def cb_ub(ctx, a):
    uid = int(a[0])
    u = sv.get_user(uid)
    if not u:
        raise ValueError("user_not_found")
    sv.set_blocked(uid, not u["blocked"])
    sv.audit(ctx.uid, "user_block" if not u["blocked"] else "user_unblock", str(uid))
    ctx.ans("✅")
    user_card(ctx.chat, ctx.msg, uid)



def cb_sub(ctx, a):
    ctx.ans()
    channel = (sv.get_setting("mandatory_channel") or "").strip()
    state = "YOQILGAN" if channel else "O'CHIRILGAN"
    show(ctx.chat, ctx.msg,
         "🔒 <b>Majburiy obuna</b>\nHolati: <b>" + state + "</b>\nKanal: <code>" + esc(channel or "sozlanmagan") + "</code>\n\n"
         "Kanalni ulash uchun «Kanalni sozlash»ni bosing va kanal username'ini yuboring (masalan <code>@TilaKino</code>). "
         "O'chirish uchun «O'chirish»ni bosing. Bot kanal administrator bo'lishi shart.",
         ikb([[("✏️ Kanalni sozlash", "a:subset")],
              ([("⛔️ O'chirish", "a:suboff")] if channel else []),
              back_row()]))

def cb_subset(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "subset")
    prompt(ctx.chat, "📢 Kanal username'ini yuboring, masalan <code>@TilaKino</code>. Bot shu kanalga administrator qilib qo'shilgan bo'lishi kerak.")

def cb_suboff(ctx, a):
    sv.set_setting("mandatory_channel", "")
    sv.audit(ctx.uid, "mandatory_channel_off", "")
    ctx.ans("Majburiy obuna o'chirildi")
    cb_sub(ctx, [])

def st_subset(m, uid, data, text):
    channel = (text or "").strip()
    if channel.startswith("https://t.me/"):
        channel = "@" + channel.split("https://t.me/",1)[1].split("/",1)[0]
    if not channel.startswith("@") or len(channel) < 6 or not channel[1:].replace("_","").isalnum():
        raise ValueError("invalid")
    try:
        info = tg.call("getChat", chat_id=channel)
        bot = tg.call("getMe")
        member = tg.call("getChatMember", chat_id=channel, user_id=bot["id"])
        if member.get("status") not in ("administrator", "creator"):
            raise ValueError("invalid")
    except Exception:
        raise ValueError("invalid")
    sv.set_setting("mandatory_channel", channel)
    sv.audit(uid, "mandatory_channel_set", channel)
    sv.clear_state(uid)
    tg.send_message(uid, "✅ Majburiy obuna saqlandi: <code>" + esc(channel) + "</code>")
    panel(uid, None)


# ------------------------------------------------------------------ homiy xabarlar
def cb_promos(ctx, a):
    ctx.ans()
    items = sv.list_promo_codes()
    lines = ["🎟 <b>Promo-kodlar</b>", "Yaratish: Premium kunlari va foydalanish limitini belgilang.", ""]
    rows = []
    for p in items:
        lines.append(f"{'🟢' if p['enabled'] else '⚪️'} <code>{esc(p['code'])}</code> — {p['premium_days']} kun · {p['used_count']}/{p['max_uses']}")
        rows.append([(("⏸ O'chirish" if p["enabled"] else "▶️ Yoqish"), f"a:promot:{p['id']}")])
    rows.append([("➕ Promo-kod yaratish", "a:promonew")])
    rows.append(back_row("a:home"))
    show(ctx.chat, ctx.msg, "\n".join(lines), ikb(rows))


def cb_promonew(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "promocreate")
    prompt(ctx.chat, "🎟 Format: <code>KUNLAR LIMIT KOD</code>\nMasalan: <code>7 100 AUTO</code> — bot kodni o'zi yaratadi. Yoki <code>30 1 TILA30</code>.")


def cb_promot(ctx, a):
    if not a or not a[0].isdigit():
        return ctx.ans("Noto'g'ri promo-kod", True)
    sv.toggle_promo_code(int(a[0]))
    sv.audit(ctx.uid, "promo_toggle", a[0])
    cb_promos(ctx, [])


def cb_spn(ctx, a):
    ctx.ans()
    sp = sv.list_sponsors()
    lines = ["📢 <b>Homiy xabarlar</b>", "Faqat oddiy foydalanuvchilarga ko'rsatiladi (Premium'ga — hech qachon). "
             f"Oraliq: {sv.get_int_setting('sponsor_cooldown_min')} daqiqa. Majburiy obuna YO'Q.", ""]
    rows = []
    for s in sp:
        lines.append(f"{'🟢' if s['enabled'] else '⚪️'} #{s['id']} {esc(s['text'][:60])}")
        rows.append([(f"{'⏸' if s['enabled'] else '▶️'} #{s['id']}", f"a:spt:{s['id']}"), (f"🗑 #{s['id']}", f"a:spd:{s['id']}")])
    rows.append([("➕ Qo'shish", "a:spa"), ("⏱ Oraliq", "a:spc")])
    rows.append(back_row())
    show(ctx.chat, ctx.msg, "\n".join(lines), ikb(rows))


def cb_spa(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "spadd")
    prompt(ctx.chat, "📢 Homiy matnini yuboring. Ixtiyoriy: 2-qatorga https:// havola yozing.")


def cb_spc(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "spcool")
    prompt(ctx.chat, "⏱ Bir foydalanuvchiga homiy xabarlari orasidagi oraliq (daqiqa):")


def cb_spt(ctx, a):
    sv.toggle_sponsor(int(a[0]))
    sv.audit(ctx.uid, "sponsor_toggle", a[0])
    cb_spn(ctx, [])


def cb_spd(ctx, a):
    confirm_screen(ctx, f"Homiy #{int(a[0])} o'chiriladi.", "sd", int(a[0]), "a:spn")


# ------------------------------------------------------------------ statistika
def cb_st(ctx, a):
    ctx.ans()
    s = sv.stats()
    lines = ["📊 <b>Statistika</b>", "",
             f"👥 Foydalanuvchilar: <b>{s['users']}</b>  (faol 24s: {s['active24']}, 7k: {s['active7']})",
             f"💎 Faol Premium: <b>{s['premium_active']}</b> | muddati o'tgan: {s['premium_expired']}",
             f"🎬 Yozuvlar: {s['movies']} | 👁 Jami ko'rishlar: <b>{s['views']}</b>",
             f"💰 Tasdiqlangan tushum: <b>{sv.money(s['revenue'])} so'm</b>",
             f"⏳ Kutilayotgan to'lovlar: {s['pending']} | ❌ rad etilgan: {s['rejected']}", "",
             "<b>Yangi foydalanuvchilar (7 kun):</b>"]
    lines += [f"• {d}: {n}" for d, n in s["new_by_day"]] or ["—"]
    lines.append("\n<b>Mashhur:</b>")
    lines += [f"• {esc(p['title'])} ({p['code']}) — {p['views']}" for p in s["popular"]] or ["—"]
    show(ctx.chat, ctx.msg, "\n".join(lines), ikb([back_row()]))


# ------------------------------------------------------------------ broadcast
def cb_bc(ctx, a):
    ctx.ans()
    sv.set_state(ctx.uid, "bc")
    prompt(ctx.chat, f"📣 Yuboriladigan xabarni jo'nating (matn/rasm/video). Qabul qiluvchilar: "
                     f"<b>{len(sv.eligible_user_ids())}</b>. Avval ko'rib chiqasiz, so'ng tasdiqlaysiz.")


def cb_bcok(ctx, a):
    bid = int(a[0])
    b = sv.get_broadcast(bid)
    if not b or b["admin_id"] != ctx.uid:
        raise ValueError("not_found")
    if not sv.start_broadcast(bid):
        return ctx.ans("Bu xabar allaqachon yuborilgan/yuborilmoqda", True)
    sv.audit(ctx.uid, "broadcast_start", f"#{bid}")
    ctx.ans("🚀 Boshlandi")
    try:
        tg.edit_text(ctx.chat, ctx.msg["message_id"], "📣 Yuborish boshlandi. Tugagach hisobot keladi.")
    except tg.TgError:
        pass
    if BROADCAST_THREAD:
        threading.Thread(target=run_broadcast, args=(bid, ctx.chat), daemon=True).start()
    else:
        run_broadcast(bid, ctx.chat)


def run_broadcast(bid, admin_chat):
    b = sv.get_broadcast(bid)
    ids = sv.eligible_user_ids()
    sent = failed = skipped = 0
    for uid in ids:
        for attempt in (1, 2):
            try:
                tg.copy_message(uid, b["src_chat"], b["src_msg"])
                sent += 1
            except tg.TgError as e:
                if e.code == 429 and attempt == 1:
                    sleep(min(max(e.retry_after, 1), 60))
                    continue
                if e.code == 403:
                    sv.mark_bot_blocked(uid)
                    skipped += 1
                else:
                    failed += 1
                    log.warning("broadcast xatosi uid=%s: %s", uid, e.description)
            break
        sleep(RATE_DELAY)
    sv.finish_broadcast(bid, len(ids), sent, failed, skipped)
    ui.notify(admin_chat, f"📣 <b>Yuborish tugadi</b>\n✅ Yetkazildi: {sent}\n⏭ O'tkazib yuborildi (bot bloklangan): {skipped}\n❌ Xato: {failed}")


# ------------------------------------------------------------------ yordamchi adminlar va audit
def cb_hlp(ctx, a):
    ctx.ans()
    hs = [h for h in sv.list_admins() if not sv.is_owner(h["user_id"])]
    lines = ["🛡 <b>Yordamchi adminlar</b>", f"Asosiy admin: <code>{cfg.admin_id}</code>",
             "Ruxsatlar: " + ", ".join(sv.PERMS), ""]
    rows = []
    for h in hs:
        lines.append(f"• <code>{h['user_id']}</code> — {h['perms']}")
        rows.append([(f"🗑 {h['user_id']}", f"a:hlr:{h['user_id']}")])
    rows.append([("➕ Yordamchi qo'shish", "a:hla")])
    rows.append(back_row())
    show(ctx.chat, ctx.msg, "\n".join(lines), ikb(rows))


def cb_hla(ctx, a):
    ctx.ans()
    rows = [
        [("🛡 To‘liq huquq", "a:hlrole:all")],
        [("🎬 Katalog", "a:hlrole:catalog"), ("💎 Premium", "a:hlrole:premium")],
        [("👥 Foydalanuvchilar", "a:hlrole:users"), ("📢 Homiy", "a:hlrole:sponsor")],
        [("📊 Statistika", "a:hlrole:stats"), ("📣 Xabar tarqatish", "a:hlrole:broadcast")],
        [("↩️ Orqaga", "a:hlp")]
    ]
    show(ctx.chat, ctx.msg, "➕ <b>Yordamchi admin qo‘shish</b>\nAvval ruxsat turini tanlang:", ikb(rows))


def cb_hlrole(ctx, a):
    ctx.ans()
    if not a or a[0] not in (["all"] + list(sv.PERMS)):
        return ctx.ans("Ruxsat turi noto‘g‘ri", True)
    role = a[0]
    sv.set_state(ctx.uid, "hladd_" + role)
    prompt(ctx.chat, f"🆔 Tanlangan ruxsat: <b>{esc(role)}</b>\nYordamchi adminning raqamli Telegram ID sini yuboring:")


def cb_hlr(ctx, a):
    confirm_screen(ctx, f"Yordamchi admin <code>{int(a[0])}</code> huquqlari olib tashlanadi.", "hr", int(a[0]), "a:hlp")


def cb_au(ctx, a):
    ctx.ans()
    rows = sv.recent_audit(20)
    lines = [f"{sv.fmt_dt(r['at'])} · <code>{r['admin_id']}</code> · {esc(r['action'])} · {esc(r['details'] or '')}" for r in rows]
    show(ctx.chat, ctx.msg, "🧾 <b>Audit jurnali</b>\n\n" + ("\n".join(lines) or "Bo'sh"), ikb([back_row()]))


HANDLERS = {"home": cb_home, "cancel": cb_cancel, "mov": cb_mov, "list": cb_list, "find": cb_find, "mc": cb_mc,
            "addm": cb_addm, "me": cb_me, "mp": cb_media, "mv": cb_media, "ml": cb_media, "ev": cb_media,
            "el": cb_media, "mt": cb_mt, "md": cb_md, "ep": cb_ep, "eps": cb_eps, "ec": cb_ec, "ee": cb_ee,
            "et": cb_et, "ed": cb_ed, "do": cb_do, "prem": cb_prem, "pl": cb_pl, "ppe": cb_ppe, "pg": cb_pg,
            "pr": cb_pr, "px": cb_px, "pa": cb_pa, "pxl": cb_pxl, "pp": cb_pp, "ph": cb_ph, "pcard": cb_pcard,
            "usr": cb_usr, "us": cb_us, "uc": cb_uc, "ub": cb_ub, "spn": cb_spn, "sub": cb_sub, "subset": cb_subset, "suboff": cb_suboff, "spa": cb_spa, "spc": cb_spc,
            "spt": cb_spt, "spd": cb_spd, "st": cb_st, "bc": cb_bc, "bcok": cb_bcok, "hlp": cb_hlp,
            "hla": cb_hla, "hlrole": cb_hlrole, "hlr": cb_hlr, "au": cb_au, "promos": cb_promos, "promonew": cb_promonew, "promot": cb_promot}


# ------------------------------------------------------------------ matnli/fayl qadamlari
def handle_state(m, uid, lg, state, data, text):
    """Admin holatlari. True = xabar ishlandi."""
    need = STATE_PERM.get(state)
    if need is None:
        sv.clear_state(uid)
        return False
    ok = sv.is_owner(uid) if need == "owner" else sv.has_perm(uid, need)
    if not ok:
        sv.clear_state(uid)
        tg.send_message(uid, "⛔️ Sizda ruxsat yo'q.")
        return True
    try:
        STATE_FN[state](m, uid, data, text)
    except ValueError as e:
        tg.send_message(uid, "⚠️ " + ERR.get(str(e), "Noto'g'ri qiymat") + "\nQaytadan yuboring yoki /cancel.")
    return True


def _poster_id(m):
    return m["photo"][-1]["file_id"] if m.get("photo") else None


def st_addm(m, uid, data, text):
    i = data["i"]
    field = WIZ_MOVIE[i][0]
    if field == "poster":
        val = _poster_id(m) or (None if text == "-" else "")
        if val == "":
            raise ValueError("invalid")
        data["v"]["poster_file_id"] = val
    else:
        if not text:
            raise ValueError("invalid")
        sv.validate_field(field, text)  # darhol tekshiruv
        if field == "code" and sv.get_movie_by_code(text, published_only=False):
            raise ValueError("code_taken")
        data["v"][field] = text
    i += 1
    if i < len(WIZ_MOVIE):
        data["i"] = i
        sv.set_state(uid, "addm", data)
        return prompt(uid, WIZ_MOVIE[i][1])
    # Kodni bot o'zi yaratadi; admin har safar qo'lda raqam tanlamaydi.
    data["v"]["code"] = sv.generate_movie_code()
    movie = sv.create_movie({**data["v"], "kind": data["kind"]})
    sv.clear_state(uid)
    sv.audit(uid, f"{data['kind']}_create", f"{movie['id']}:{movie['code']}:{movie['title']}")
    tg.send_message(uid, "✅ Qo'shildi! Endi video/epizodlarni biriktiring:")
    movie_card(uid, None, movie["id"])


def st_adde(m, uid, data, text):
    i = data["i"]
    if not text:
        raise ValueError("invalid")
    data["v"][WIZ_EP[i][0]] = text
    i += 1
    if i < len(WIZ_EP):
        data["i"] = i
        sv.set_state(uid, "adde", data)
        return prompt(uid, WIZ_EP[i][1])
    v = data["v"]
    clean = lambda s: None if s in (None, "-") else s
    e = sv.create_episode(data["sid"], v["season"], v["number"], clean(v.get("title")), clean(v.get("description")))
    sv.clear_state(uid)
    sv.audit(uid, "episode_create", f"{e['id']} series={data['sid']} S{e['season']}E{e['number']}")
    tg.send_message(uid, "✅ Epizod qo'shildi! Video biriktiring:")
    episode_card(uid, None, e["id"])


def st_edit(m, uid, data, text):
    if not text:
        raise ValueError("invalid")
    if data["t"] == "movie":
        sv.update_movie(data["id"], data["f"], text)
        sv.audit(uid, "movie_edit", f"{data['id']}:{data['f']}")
        sv.clear_state(uid)
        movie_card(uid, None, data["id"])
    else:
        sv.update_episode(data["id"], data["f"], text)
        sv.audit(uid, "episode_edit", f"{data['id']}:{data['f']}")
        sv.clear_state(uid)
        episode_card(uid, None, data["id"])


def st_media(m, uid, data, text):
    t, pid, q = data["t"], data["id"], data.get("q")
    if t == "mp":
        fid = _poster_id(m)
        if not fid:
            raise ValueError("invalid")
        sv.update_movie(pid, "poster_file_id", fid)
        card = lambda: movie_card(uid, None, pid)
    elif t in ("mv", "ev"):
        if m.get("video"):
            fid, ft = m["video"]["file_id"], "video"
        elif m.get("document"):
            fid, ft = m["document"]["file_id"], "document"
        else:
            raise ValueError("invalid")
        kw = {"movie_id": pid} if t == "mv" else {"episode_id": pid}
        sv.set_variant(q, file_id=fid, ftype=ft, label=(m.get("caption") or None), **kw)
        card = (lambda: movie_card(uid, None, pid)) if t == "mv" else (lambda: episode_card(uid, None, pid))
    else:  # ml / el
        if not text:
            raise ValueError("invalid")
        kw = {"movie_id": pid} if t == "ml" else {"episode_id": pid}
        sv.set_variant(q, external_url=text, **kw)
        card = (lambda: movie_card(uid, None, pid)) if t == "ml" else (lambda: episode_card(uid, None, pid))
    sv.audit(uid, "media_set", f"{t}:{pid}:{q}")
    sv.clear_state(uid)
    tg.send_message(uid, "✅ Saqlandi.")
    card()


def st_find(m, uid, data, text):
    if not text:
        raise ValueError("invalid")
    items = sv.admin_find(text)
    sv.clear_state(uid)
    if not items:
        return tg.send_message(uid, "Hech narsa topilmadi.", ikb([back_row("a:mov")]))
    if len(items) == 1:
        return movie_card(uid, None, items[0]["id"])
    rows = [[(f"{x['code']} · {x['title']}", f"a:mc:{x['id']}")] for x in items]
    rows.append(back_row("a:mov"))
    tg.send_message(uid, "🔍 Natijalar:", ikb(rows))


def st_pset(m, uid, data, text):
    plan = sv.update_plan(data["key"], data["f"], text)
    sv.audit(uid, "plan_update", f"{data['key']}:{data['f']}={text}")
    sv.clear_state(uid)
    tg.send_message(uid, f"✅ Saqlandi: {plan['label']} — {plan['days']} kun, {sv.money(plan['price'])} so'm",
                    ikb([back_row("a:pl")]))


def _two(text):
    p = (text or "").split()
    if len(p) != 2 or not p[0].lstrip("-").isdigit():
        raise ValueError("invalid")
    return int(p[0]), p[1]


def st_pgrant(m, uid, data, text):
    target, days = _two(text)
    if not days.isdigit():
        raise ValueError("invalid")
    if not sv.get_user(target):
        raise ValueError("user_not_found")
    end = sv.grant_premium(target, int(days), "manual")
    sv.audit(uid, "premium_grant", f"{target}:+{days}")
    sv.clear_state(uid)
    tg.send_message(uid, f"✅ {target} ga +{days} kun berildi. Tugash: {sv.fmt_dt(end)}", ikb([back_row("a:prem")]))
    u = sv.get_user(target)
    from i18n import t
    ui.notify(target, t(u["lang"], "pay_approved", date=sv.fmt_date(end)))


def st_prevoke(m, uid, data, text):
    if not (text or "").lstrip("-").isdigit() or not sv.get_user(int(text)):
        raise ValueError("user_not_found")
    sv.clear_state(uid)
    target = int(text)
    tg.send_message(uid, f"⚠️ <code>{target}</code> Premiumi bekor qilinsinmi?",
                    ikb([[("✅ Tasdiqlash", f"a:do:pv:{target}"), ("❌ Bekor qilish", "a:prem")]]))


def st_pexpiry(m, uid, data, text):
    target, date = _two(text)
    try:
        ts = sv.parse_local_date(date)
    except ValueError:
        raise ValueError("invalid")
    sv.set_premium_expiry(target, ts)
    sv.audit(uid, "premium_set_expiry", f"{target}:{date}")
    sv.clear_state(uid)
    tg.send_message(uid, f"✅ {target}: Premium tugash vaqti {sv.fmt_dt(ts)}", ikb([back_row("a:prem")]))


def st_cardinfo(m, uid, data, text):
    if not text:
        raise ValueError("invalid")
    sv.set_setting("card_info", "" if text == "-" else text[:500])
    sv.audit(uid, "card_info_update", "")
    sv.clear_state(uid)
    tg.send_message(uid, "✅ Saqlandi.", ikb([back_row("a:prem")]))


def st_usearch(m, uid, data, text):
    if not (text or "").isdigit():
        raise ValueError("invalid")
    sv.clear_state(uid)
    user_card(uid, None, int(text))


def st_promocreate(m, uid, data, text):
    p = (text or "").split()
    if len(p) != 3 or not p[0].isdigit() or not p[1].isdigit():
        raise ValueError("invalid")
    result = sv.create_promo_code(p[2], int(p[0]), int(p[1]), uid)
    sv.audit(uid, "promo_create", f"{result['code']}:{result['premium_days']}:{result['max_uses']}")
    sv.clear_state(uid)
    tg.send_message(uid, f"✅ Promo-kod: <code>{esc(result['code'])}</code>\n💎 Premium: {result['premium_days']} kun\n🔢 Limit: {result['max_uses']} marta", ikb([[("🎟 Promo-kodlar", "a:promos")]]))


def st_spadd(m, uid, data, text):
    lines = (text or "").split("\n")
    sid = sv.add_sponsor(lines[0], lines[1].strip() if len(lines) > 1 and lines[1].strip() else None)
    sv.audit(uid, "sponsor_add", str(sid))
    sv.clear_state(uid)
    tg.send_message(uid, "✅ Qo'shildi.", ikb([[("📢 Homiylar", "a:spn")]]))


def st_spcool(m, uid, data, text):
    if not (text or "").isdigit() or not 0 <= int(text) <= 1440:
        raise ValueError("invalid")
    sv.set_setting("sponsor_cooldown_min", text)
    sv.audit(uid, "sponsor_cooldown", text)
    sv.clear_state(uid)
    tg.send_message(uid, "✅ Saqlandi.", ikb([[("📢 Homiylar", "a:spn")]]))


def st_bc(m, uid, data, text):
    bid = sv.create_broadcast(uid, m["chat"]["id"], m["message_id"])
    sv.clear_state(uid)
    n = len(sv.eligible_user_ids())
    tg.send_message(uid, "👆 Shunday ko'rinishda yuboriladi (ko'rib chiqing):")
    try:
        tg.copy_message(uid, m["chat"]["id"], m["message_id"])
    except tg.TgError:
        pass
    tg.send_message(uid, f"📣 Qabul qiluvchilar: <b>{n}</b>. Yuborilsinmi?",
                    ikb([[("✅ Yuborish", f"a:bcok:{bid}"), ("❌ Bekor qilish", "a:cancel")]]))


def st_hladd(m, uid, data, text):
    p = (text or "").strip()
    if not p.lstrip("-").isdigit():
        raise ValueError("invalid")
    role = data.get("role", "all") if isinstance(data, dict) else "all"
    perms = list(sv.PERMS) if role == "all" else [role]
    try:
        perms = sv.add_helper(uid, int(p), perms)
    except PermissionError:
        raise ValueError("owner")
    sv.clear_state(uid)
    tg.send_message(uid, f"✅ Yordamchi qo‘shildi: <code>{int(p)}</code> — {', '.join(perms)}", ikb([[("🛡 Adminlar", "a:hlp")]]))



def _st_hlrole(role):
    def _handler(m, uid, data, text):
        try:
            perms = list(sv.PERMS) if role == "all" else [role]
            raw = (text or "").strip()
            if not raw.lstrip("-").isdigit():
                raise ValueError("invalid")
            try:
                perms = sv.add_helper(uid, int(raw), perms)
            except PermissionError:
                raise ValueError("owner")
            sv.clear_state(uid)
            tg.send_message(uid, f"✅ Yordamchi qo‘shildi: <code>{int(raw)}</code> — {', '.join(perms)}",
                            ikb([[("🛡 Adminlar", "a:hlp")]]))
        except ValueError:
            raise
    return _handler

STATE_FN = {"addm": st_addm, "adde": st_adde, "edit": st_edit, "media": st_media, "find": st_find, "pset": st_pset,
            "pgrant": st_pgrant, "prevoke": st_prevoke, "pexpiry": st_pexpiry, "cardinfo": st_cardinfo,
            "usearch": st_usearch, "hladd_all": _st_hlrole("all"), "hladd_catalog": _st_hlrole("catalog"), "hladd_premium": _st_hlrole("premium"), "hladd_users": _st_hlrole("users"), "hladd_sponsor": _st_hlrole("sponsor"), "hladd_stats": _st_hlrole("stats"), "hladd_broadcast": _st_hlrole("broadcast"), "promocreate": st_promocreate, "spadd": st_spadd, "subset": st_subset, "spcool": st_spcool, "bc": st_bc, "hladd": st_hladd}
