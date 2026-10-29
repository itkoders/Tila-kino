# -*- coding: utf-8 -*-
"""Foydalanuvchi tomoni: /start, menyu, katalog, qidiruv, tomosha, sevimlilar, Premium, profil."""
import logging

import admin
import services as sv
import tg
import ui
from config import cfg
from i18n import LANGS, menu_label_map, t
from ui import esc, ikb, nav_row, pager, send, show

log = logging.getLogger("tilakino.handlers")
MENU_LABELS = menu_label_map()
USER_STATES = ("search", "code", "proof", "promo")
STATUS_ICON = {"pending": "⏳", "approved": "✅", "rejected": "❌", "expired": "⌛️"}
_bot_username = {"v": None}


def bot_username():
    if cfg.bot_username:
        return cfg.bot_username
    if _bot_username["v"] is None:
        try:
            _bot_username["v"] = tg.call("getMe").get("username", "")
        except tg.TgError:
            return ""
    return _bot_username["v"]


class Ctx:
    """Callback so'rovi konteksti: callback_query'ga aniq bir marta javob beradi."""

    def __init__(self, c):
        self.cb_id = c["id"]
        self.frm = c["from"]
        self.uid = self.frm["id"]
        self.msg = c.get("message")
        self.chat = self.msg["chat"]["id"] if self.msg else self.uid
        self.data = c.get("data") or ""
        self.u = None
        self.lg = "uz"
        self.answered = False

    def ans(self, text=None, alert=False):
        if self.answered:
            return
        self.answered = True
        try:
            tg.answer_callback(self.cb_id, text, alert)
        except tg.TgError:
            pass


# ------------------------------------------------------------------ kirish nuqtasi
def handle_update(upd):
    if "message" in upd:
        on_message(upd["message"])
    elif "callback_query" in upd:
        on_callback(upd["callback_query"])



def mandatory_channel():
    return (sv.get_setting("mandatory_channel") or "").strip()

def subscription_ok(uid):
    channel = mandatory_channel()
    if not channel or sv.is_admin(uid):
        return True
    try:
        member = tg.call("getChatMember", chat_id=channel, user_id=uid)
        return member.get("status") in ("creator", "administrator", "member", "restricted") and not member.get("is_member") is False
    except Exception as e:
        log.warning("Majburiy obuna tekshirilmadi: %s", type(e).__name__)
        return False

def show_subscription_gate(uid):
    channel = mandatory_channel()
    if not channel:
        return False
    target = channel if channel.startswith("@") else "@" + channel.lstrip("@")
    url = "https://t.me/" + target.lstrip("@")
    kb = ikb([ [("📢 Kanalga obuna bo‘lish", url)], [("✅ Obunani tekshirish", "subcheck")] ])
    send(uid, "🔒 <b>TilaKino’dan foydalanish uchun kanalimizga obuna bo‘ling.</b>\n\nObuna bo‘lgach, «Obunani tekshirish» tugmasini bosing.", kb)
    return True


def on_message(m):
    chat = m.get("chat") or {}
    frm = m.get("from")
    if chat.get("type") != "private" or not frm or frm.get("is_bot"):
        return
    uid = frm["id"]
    try:
        u, created = sv.upsert_user(frm)
        lg = u["lang"]
        if u["blocked"]:
            send(uid, t(lg, "blocked"))
            return
        text = (m.get("text") or "").strip()
        if not sv.is_admin(uid) and not subscription_ok(uid):
            show_subscription_gate(uid)
            return
        if text.startswith("/"):
            return on_command(m, u, created, text)
        if text in MENU_LABELS:
            sv.clear_state(uid)
            return on_menu(uid, u, MENU_LABELS[text])
        state, data = sv.get_state(uid)
        if state and state not in ("q",):
            if state in USER_STATES:
                return user_state(m, u, state, data, text)
            if sv.is_admin(uid):
                if admin.handle_state(m, uid, lg, state, data, text):
                    return
            else:
                sv.clear_state(uid)
        if text:
            return free_text(uid, u, text)
        send(uid, t(lg, "unknown"), main_menu_for(lg))
    except tg.TgError as e:
        log.warning("Telegram xatosi (message): %s", e.description)
        if e.blocked:
            sv.mark_bot_blocked(uid)
    except Exception:
        log.exception("on_message xatosi")
        try:
            tg.send_message(uid, "⚠️ Xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")
        except tg.TgError:
            pass


def main_menu_for(lg):
    return ui.main_menu(lg)


def on_command(m, u, created, text):
    uid, lg = u["id"], u["lang"]
    cmd, _, payload = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    payload = payload.strip()
    if cmd == "/start":
        sv.clear_state(uid)
        if created:
            welcome_new(u, payload)
        if payload.startswith("m_") and sv.get_movie_by_code(payload[2:]):
            return start_screen(uid, u, then_movie=payload[2:])
        return start_screen(uid, u)
    if cmd in ("/menu", "/help"):
        sv.clear_state(uid)
        return start_screen(uid, u, animate=False)
    if cmd == "/cancel":
        sv.clear_state(uid)
        return send(uid, t(lg, "cancelled"), main_menu_for(lg))
    if cmd == "/setwelcome":
        if not sv.is_admin(uid):
            return send(uid, "⛔️ Sizda ruxsat yo'q.")
        animation = m.get("animation")
        document = m.get("document") or {}
        if not animation and document.get("mime_type") == "image/gif":
            animation = document
        if not animation:
            return send(uid, "🎞 TILAKINO kirish GIF'ini caption sifatida /setwelcome yozib yuboring.\n"
                             "Masalan: GIF tanlang → caption: /setwelcome")
        sv.set_setting("welcome_gif_file_id", animation["file_id"])
        return send(uid, "✅ TILAKINO kirish GIF'i saqlandi. Keyingi /start da ishlatiladi.")
    if cmd == "/promo":
        if not payload:
            return send(uid, "🎟 Promo-kodni ishlatish: <code>/promo KOD</code>")
        try:
            result = sv.redeem_promo_code(uid, payload)
        except ValueError as e:
            if str(e) == "promo_used":
                return send(uid, "⚠️ Bu promo-koddan oldin foydalangansiz.")
            return send(uid, "❌ Promo-kod noto'g'ri yoki limiti to'lgan.")
        sv.audit(uid, "promo_redeem", f"{result['code']}:{uid}")
        return send(uid, f"🎉 Promo-kod qabul qilindi!\n💎 Premium: +{result['days']} kun\n📅 Tugash: {sv.fmt_dt(result['expires_at'])}", main_menu_for(lg))
    if cmd == "/admin":
        if not sv.is_admin(uid):
            return send(uid, "⛔️ Sizda ruxsat yo'q.")
        sv.clear_state(uid)
        return admin.panel(uid, None)
    send(uid, t(lg, "unknown"), main_menu_for(lg))


def welcome_new(u, payload):
    """Yangi foydalanuvchi: sinov muddati (sozlansa) va taklif bonusi."""
    uid = u["id"]
    trial = sv.get_int_setting("trial_days")
    if trial > 0:
        sv.grant_premium(uid, trial, "trial")
    if payload.isdigit() and sv.apply_referral(uid, int(payload)):
        ref = int(payload)
        ref_u = sv.get_user(ref)
        ui.notify(ref, t(ref_u["lang"] if ref_u else "uz", "ref_bonus", days=sv.get_int_setting("ref_bonus_days")))


def start_screen(uid, u, then_movie=None, animate=True):
    u = sv.get_user(uid)
    lg = u["lang"]
    if animate:
        ui.typing_intro(uid)
    status = (t(lg, "status_premium", date=sv.fmt_date(u["premium_until"]))
              if sv.is_premium(u) else t(lg, "status_free"))
    send(uid, t(lg, "welcome", name=esc(u["first_name"] or "👋"), status=status), main_menu_for(lg))
    if then_movie:
        m = sv.get_movie_by_code(then_movie)
        if m:
            show_movie(uid, None, u, m["id"])


# ------------------------------------------------------------------ menyu
def on_menu(uid, u, key):
    lg = u["lang"]
    if key == "menu_movies":
        maybe_sponsor(uid, u)
        return show_list(uid, None, lg, "movie", 0)
    if key == "menu_series":
        maybe_sponsor(uid, u)
        return show_list(uid, None, lg, "series", 0)
    if key == "menu_search":
        sv.set_state(uid, "search")
        return send(uid, t(lg, "search_prompt"), ikb([[(t(lg, "btn_cancel"), "cancel")]]))
    if key == "menu_code":
        sv.set_state(uid, "code")
        return send(uid, t(lg, "code_prompt"), ikb([[(t(lg, "btn_cancel"), "cancel")]]))
    if key == "menu_favs":
        return show_favs(uid, None, lg, 0)
    if key == "menu_premium":
        return show_premium(uid, None, u)
    if key == "menu_profile":
        return show_profile(uid, u)
    if key == "menu_sub":
        return show_sub(uid, u)
    if key == "menu_promo":
        sv.set_state(uid, "promo")
        return send(uid, t(lg, "promo_prompt"), ikb([[(t(lg, "btn_cancel"), "cancel")]]))


def maybe_sponsor(uid, u):
    s = sv.pick_sponsor(u)
    if s:
        kb = ikb([[("🔗", s["url"])]]) if s["url"] else None
        send(uid, t(u["lang"], "sponsor", text=esc(s["text"])), kb)


def free_text(uid, u, text):
    lg = u["lang"]
    if text.isdigit():
        m = sv.get_movie_by_code(text)
        if m:
            maybe_sponsor(uid, u)
            return show_movie(uid, None, u, m["id"])
    return run_search(uid, None, lg, text)


def user_state(m, u, state, data, text):
    uid, lg = u["id"], u["lang"]
    if state == "proof":
        fid = None
        if m.get("photo"):
            fid = m["photo"][-1]["file_id"]
        elif m.get("document"):
            fid = m["document"]["file_id"]
        if not fid:
            return send(uid, t(lg, "pay_need_proof"))
        return submit_proof(uid, u, data.get("pid"), fid, m)
    if not text:
        return send(uid, t(lg, "invalid"))
    sv.clear_state(uid)
    if state == "promo":
        try:
            result = sv.redeem_promo_code(uid, text)
        except ValueError as e:
            if str(e) == "promo_used":
                return send(uid, t(lg, "promo_used"), main_menu_for(lg))
            return send(uid, t(lg, "promo_invalid"), main_menu_for(lg))
        sv.audit(uid, "promo_redeem", f"{result['code']}:{uid}")
        return send(uid, t(lg, "promo_success", code=esc(result["code"]), days=result["days"], expires=sv.fmt_dt(result["expires_at"])), main_menu_for(lg))
    if state == "code":
        if not text.isdigit():
            return send(uid, t(lg, "invalid"))
        mv = sv.get_movie_by_code(text)
        if not mv:
            return send(uid, t(lg, "nothing_found"), main_menu_for(lg))
        maybe_sponsor(uid, u)
        return show_movie(uid, None, u, mv["id"])
    return run_search(uid, None, lg, text)


# ------------------------------------------------------------------ katalog
def item_label(m):
    icon = "📺" if m["kind"] == "series" else "🎬"
    return f"{icon} {m['title']}" + (f" ({m['year']})" if m["year"] else "")


def show_list(chat, msg, lg, kind, page):
    items, total = sv.list_catalog(kind, page, ui.PER_PAGE)
    title = t(lg, "movies_title" if kind == "movie" else "series_title")
    if not items and page == 0:
        return show(chat, msg, f"{title}\n\n{t(lg, 'catalog_empty')}", ikb([nav_row(lg)]))
    rows = [[(item_label(m), f"m:{m['id']}")] for m in items]
    rows.append(pager("lm" if kind == "movie" else "ls", page, total))
    rows.append(nav_row(lg))
    show(chat, msg, title, ikb(rows))


def run_search(chat, msg, lg, text, page=0):
    items, total = sv.search_catalog(text, page, ui.PER_PAGE)
    sv.set_state(chat, "q", {"q": text})
    if not items:
        return show(chat, msg, t(lg, "nothing_found"), ikb([nav_row(lg)]))
    rows = [[(item_label(m), f"m:{m['id']}")] for m in items]
    rows.append(pager("sr", page, total))
    rows.append(nav_row(lg))
    show(chat, msg, t(lg, "results_title", q=esc(text[:60])), ikb(rows))


def show_favs(chat, msg, lg, page):
    items, total = sv.list_favorites(chat, page, ui.PER_PAGE)
    if not items:
        return show(chat, msg, f"{t(lg, 'favs_title')}\n\n{t(lg, 'favs_empty')}", ikb([nav_row(lg)]))
    rows = [[(item_label(m), f"m:{m['id']}")] for m in items]
    rows.append(pager("favs", page, total))
    rows.append(nav_row(lg))
    show(chat, msg, t(lg, "favs_title"), ikb(rows))


def movie_text(m):
    icon = "📺" if m["kind"] == "series" else "🎬"
    head = [f"{icon} <b>{esc(m['title'])}</b>" + (f" ({m['year']})" if m["year"] else ""),
            f"🔢 <code>{esc(m['code'])}</code>"]
    meta = []
    if m["country"]:
        meta.append(f"🌍 {esc(m['country'])}")
    if m["genre"]:
        meta.append(f"🎭 {esc(m['genre'])}")
    if m["language"]:
        meta.append(f"🗣 {esc(m['language'].upper().replace(',', ', '))}")
    if m["rating"] is not None:
        meta.append(f"⭐ {m['rating']:g}")
    meta.append(f"👁 {m['views']}")
    if m["kind"] == "movie":
        qs = [v["quality"] for v in sv.list_variants(movie_id=m["id"])]
        if qs:
            head.append("📀 " + " · ".join("Medium" if q == "medium" else "High 💎" for q in qs))
    else:
        head.append(f"📺 {len(sv.list_episodes(m['id']))}")
    text = "\n".join(head + [" | ".join(meta)])
    if m["description"]:
        room = 1000 - len(text) - 2
        if room > 20:
            d = m["description"]
            text += "\n\n" + esc(d if len(d) <= room else d[:room - 1] + "…")
    return text


def movie_kb(lg, uid, m):
    rows = []
    first = []
    if m["kind"] == "series":
        if sv.list_episodes(m["id"]):
            first.append(("📺 " + t(lg, "episodes"), f"e:{m['id']}:0:0"))
    elif sv.list_variants(movie_id=m["id"]):
        first.append((t(lg, "btn_watch"), f"w:{m['id']}"))
    first.append((t(lg, "fav_del") if sv.is_favorite(uid, m["id"]) else t(lg, "fav_add"), f"fav:{m['id']}"))
    rows.append(first)
    if cfg.base_url and sv.has_web_source(m):
        rows.append([("🌐 " + t(lg, "btn_web"), f"{cfg.base_url}/movie/{m['code']}")])
    rows.append(nav_row(lg, "lm:0" if m["kind"] == "movie" else "ls:0"))
    return ikb(rows)


def show_movie(chat, msg, u, mid):
    lg = u["lang"]
    m = sv.get_movie(mid)
    if not m or not m["published"]:
        return show(chat, msg, t(lg, "nothing_found"), ikb([nav_row(lg)]))
    show(chat, msg, movie_text(m), movie_kb(lg, u["id"], m), photo=m["poster_file_id"])


# ------------------------------------------------------------------ epizodlar
def show_episodes(ctx, sid, season, page):
    lg = ctx.lg
    m = sv.get_movie(sid)
    seasons = sv.list_seasons(sid)
    if not m or not m["published"] or not seasons:
        return show(ctx.chat, ctx.msg, t(lg, "nothing_found"), ikb([nav_row(lg)]))
    if season not in seasons:
        season = seasons[0]
    eps = sv.list_episodes(sid, season)
    per = ui.PER_PAGE
    chunk = eps[page * per:(page + 1) * per]
    rows = []
    if len(seasons) > 1:
        rows.append([(("• " if s == season else "") + t(lg, "season", n=s), f"e:{sid}:{s}:0") for s in seasons[:5]])
    for e in chunk:
        label = f"S{e['season']}E{e['number']}" + (f" · {e['title']}" if e["title"] else "")
        rows.append([(label, f"ep:{e['id']}")])
    rows.append(pager(f"e:{sid}:{season}", page, len(eps), per))
    rows.append(nav_row(ctx.lg, f"m:{sid}"))
    show(ctx.chat, ctx.msg, f"📺 <b>{esc(m['title'])}</b> — {t(lg, 'season', n=season)}", ikb(rows))


def ep_title(e):
    return t("uz", "ep_line", s=e["season"], n=e["number"]) + (f" — {e['title']}" if e["title"] else "")


def show_episode(ctx, eid):
    lg = ctx.lg
    e = sv.get_episode(eid)
    m = sv.get_movie(e["series_id"]) if e else None
    if not e or not e["published"] or not m or not m["published"]:
        return show(ctx.chat, ctx.msg, t(lg, "nothing_found"), ikb([nav_row(lg)]))
    prev_id, next_id = sv.episode_neighbors(eid)
    text = f"📺 <b>{esc(m['title'])}</b>\nS{e['season']}E{e['number']}" + (f" — <b>{esc(e['title'])}</b>" if e["title"] else "")
    if e["description"]:
        text += "\n\n" + esc(e["description"][:900])
    rows = []
    if sv.list_variants(episode_id=eid):
        rows.append([(t(lg, "btn_watch"), f"we:{eid}")])
    else:
        text += "\n\n" + t(lg, "no_video")
    nav = []
    if prev_id:
        nav.append((t(lg, "ep_prev"), f"ep:{prev_id}"))
    if next_id:
        nav.append((t(lg, "ep_next"), f"ep:{next_id}"))
    rows.append(nav)
    rows.append([("📺 " + t(lg, "episodes"), f"e:{m['id']}:{e['season']}:0")])
    rows.append(nav_row(lg))
    show(ctx.chat, ctx.msg, text, ikb(rows))


# ------------------------------------------------------------------ tomosha
def play_flow(ctx, movie, ep, variants):
    lg = ctx.lg
    if not variants:
        return send(ctx.chat, t(lg, "no_video"))
    res = sv.resolve_variant(variants, sv.is_premium(sv.get_user(ctx.uid)))
    if res["variant"]:
        return deliver(ctx, res["variant"], movie, ep)
    if res["alternative"]:
        alt = res["alternative"]
        return send(ctx.chat, t(lg, "quality_missing"),
                    ikb([[(t(lg, "btn_play_alt", q="Medium"), f"wv:{alt['id']}")]]))
    if res["premium_required"]:
        return send(ctx.chat, t(lg, "premium_only"), ikb([[("💎 Premium", "prem")]]))
    send(ctx.chat, t(lg, "no_video"))


def deliver(ctx, v, movie, ep):
    lg = ctx.lg
    ui.loading(ctx.chat, t(lg, "loading"))
    try:
        tg.chat_action(ctx.chat, "upload_video")
    except tg.TgError:
        pass
    cap = f"🎬 <b>{esc(movie['title'])}</b>" + (f"\n{ep_title(ep)}" if ep else "")
    kb = None
    if ep:
        p, n = sv.episode_neighbors(ep["id"])
        kb = ikb([[(t(lg, "ep_prev"), f"ep:{p}") if p else ("", ""), (t(lg, "ep_next"), f"ep:{n}") if n else ("", "")],
                  [("📺 " + t(lg, "episodes"), f"e:{movie['id']}:{ep['season']}:0")]])
    protect = sv.get_setting("protect_content") == "1"
    try:
        if v["file_id"]:
            if v["ftype"] == "document":
                tg.send_document(ctx.chat, v["file_id"], cap, kb, protect)
            else:
                tg.send_video(ctx.chat, v["file_id"], cap, kb, protect)
        elif v["external_url"]:
            tg.send_message(ctx.chat, cap + "\n\n" + t(lg, "link_msg"), ikb([[(t(lg, "ext_btn"), v["external_url"])]]))
        else:
            return send(ctx.chat, t(lg, "no_video"))
    except tg.TgError as e:
        log.warning("video yuborilmadi: %s", e.description)
        return send(ctx.chat, "⚠️ Videoni yuborib bo'lmadi. Admin fayl ID sini yangilashi kerak bo'lishi mumkin.")
    sv.record_view(ctx.uid, movie["id"], ep["id"] if ep else None)


def cb_watch_movie(ctx, parts):
    m = sv.get_movie(int(parts[1]))
    if not m or not m["published"] or m["kind"] != "movie":
        return ctx.ans(t(ctx.lg, "nothing_found"), True)
    ctx.ans()
    play_flow(ctx, m, None, sv.list_variants(movie_id=m["id"]))


def cb_watch_episode(ctx, parts):
    e = sv.get_episode(int(parts[1]))
    m = sv.get_movie(e["series_id"]) if e else None
    if not e or not e["published"] or not m or not m["published"]:
        return ctx.ans(t(ctx.lg, "nothing_found"), True)
    ctx.ans()
    play_flow(ctx, m, e, sv.list_variants(episode_id=e["id"]))


def cb_watch_variant(ctx, parts):
    v = sv.get_variant(int(parts[1]))
    if not v:
        return ctx.ans(t(ctx.lg, "nothing_found"), True)
    ep = sv.get_episode(v["episode_id"]) if v["episode_id"] else None
    m = sv.get_movie(v["movie_id"] if v["movie_id"] else ep["series_id"])
    if not m or not m["published"] or (ep and not ep["published"]):
        return ctx.ans(t(ctx.lg, "nothing_found"), True)
    if v["quality"] == "high" and not sv.is_premium(sv.get_user(ctx.uid)):
        return ctx.ans(t(ctx.lg, "premium_only"), True)
    ctx.ans()
    deliver(ctx, v, m, ep)


# ------------------------------------------------------------------ profil, Premium
def show_profile(uid, u):
    lg = u["lang"]
    status = (t(lg, "status_premium", date=sv.fmt_date(u["premium_until"]))
              if sv.is_premium(u) else t(lg, "status_free"))
    un = bot_username()
    link = f"https://t.me/{un}?start={uid}" if un else "—"
    text = t(lg, "profile", id=uid, name=esc(u["first_name"] or "—"), lang=LANGS.get(lg, lg),
             status=status, refs=u["ref_count"], link=link)
    rows = [[(name, f"lang:{code}") for code, name in list(LANGS.items())[:2]],
            [(name, f"lang:{code}") for code, name in list(LANGS.items())[2:]], nav_row(lg)]
    send(uid, text, ikb(rows))


def show_sub(uid, u):
    lg = u["lang"]
    lines = [t(lg, "sub_title"), ""]
    if sv.is_premium(u):
        lines.append(t(lg, "status_premium", date=sv.fmt_dt(u["premium_until"])))
    else:
        lines.append(t(lg, "status_free"))
        if u["premium_until"]:
            lines.append(f"⌛️ {sv.fmt_date(u['premium_until'])}")
    subs = sv.list_subscriptions(uid, 5)
    lines.append(f"\n💎 <b>Premium</b>")
    lines += [f"• {s['days']} • {sv.fmt_date(s['starts_at'])} → {sv.fmt_date(s['expires_at'])} ({esc(s['source'] or '')})"
              for s in subs] or [t(lg, "sub_none")]
    pays = sv.list_payments(uid=uid, limit=5)
    if pays:
        lines.append(f"\n💳 <b>{t(lg, 'pay_hist')}</b>")
        lines += [f"{STATUS_ICON.get(p['status'], '•')} {esc(p['reference'])} — {sv.money(p['amount'])} so'm — {p['status']}"
                  for p in pays]
    lines.append(f"\n🕘 <b>{t(lg, 'watch_hist')}</b>")
    hist = sv.list_history(uid, 10)
    lines += [f"• {esc(h['title'])}" + (f" S{h['season']}E{h['number']}" if h["season"] else "") +
              f" — {sv.fmt_dt(h['watched_at'])}" for h in hist] or [t(lg, "hist_empty")]
    send(uid, "\n".join(lines), ikb([nav_row(lg)]))


def show_premium(chat, msg, u):
    lg = u["lang"]
    status = (t(lg, "status_premium", date=sv.fmt_date(u["premium_until"]))
              if sv.is_premium(u) else t(lg, "status_free"))
    rows = [[(t(lg, "plan_btn", label=p["label"], price=sv.money(p["price"])), f"buy:{k}")]
            for k, p in sv.get_plans().items()]
    rows.append(nav_row(lg))
    show(chat, msg, t(lg, "premium_title", status=status), ikb(rows))


def cb_buy(ctx, parts):
    plans = sv.get_plans()
    plan = plans.get(parts[1])
    if not plan:
        return ctx.ans(t(ctx.lg, "invalid"), True)
    ctx.ans()
    card = sv.get_setting("card_info").strip()
    if not card:
        return send(ctx.chat, t(ctx.lg, "pay_no_card"), ikb([nav_row(ctx.lg)]))
    p = sv.create_payment(ctx.uid, parts[1])
    sv.set_state(ctx.uid, "proof", {"pid": p["id"]})
    send(ctx.chat, t(ctx.lg, "pay_instr", ref=p["reference"], label=plan["label"], price=sv.money(p["amount"]),
                     card=esc(card)), ikb([[(t(ctx.lg, "btn_cancel"), "cancel")]]))


def submit_proof(uid, u, pid, fid, m):
    lg = u["lang"]
    p = sv.get_payment(pid) if pid else None
    if not p or p["user_id"] != uid or p["status"] != "pending":
        sv.clear_state(uid)
        return send(uid, t(lg, "pay_expired"), main_menu_for(lg))
    sv.attach_proof(pid, uid, fid)
    sv.clear_state(uid)
    cap = (f"💳 <b>To'lov #{esc(p['reference'])}</b>\n👤 <a href=\"tg://user?id={uid}\">{esc(u['first_name'] or str(uid))}</a>"
           f" (<code>{uid}</code>)\n📦 {p['days']} kun — {sv.money(p['amount'])} so'm")
    kb = ikb([[("✅ Tasdiqlash", f"pay:ok:{pid}"), ("❌ Rad etish", f"pay:no:{pid}")]])
    for r in sv.list_admins() + [{"user_id": cfg.admin_id}]:
        aid = r["user_id"]
        if aid != cfg.admin_id and not sv.has_perm(aid, "premium"):
            continue
        try:
            if m.get("photo"):
                tg.send_photo(aid, fid, cap, kb)
            else:
                tg.send_document(aid, fid, cap, kb)
        except tg.TgError as e:
            log.warning("adminga chek yuborilmadi: %s", e.description)
    send(uid, t(lg, "pay_proof_ok"), main_menu_for(lg))


def cb_pay_decide(ctx, parts):
    """Admin to'lovni tasdiqlaydi/rad etadi (atomik; ikki marta ishlamaydi)."""
    if not sv.has_perm(ctx.uid, "premium"):
        return ctx.ans("⛔️ Ruxsat yo'q", True)
    approve = parts[1] == "ok"
    pid = int(parts[2])
    changed, p = sv.decide_payment(pid, approve, ctx.uid)
    if not p:
        return ctx.ans("Topilmadi", True)
    if not changed:
        return ctx.ans(f"Allaqachon ko'rib chiqilgan: {p['status']}", True)
    sv.audit(ctx.uid, "payment_" + p["status"], f"#{p['id']} user={p['user_id']} {p['amount']}")
    ctx.ans("✅" if approve else "❌")
    notify_payment(p)
    note = f"{'✅ Tasdiqlandi' if approve else '❌ Rad etildi'} (#{esc(p['reference'])})"
    try:
        tg.edit_caption(ctx.chat, ctx.msg["message_id"], note)
    except tg.TgError:
        try:
            tg.edit_text(ctx.chat, ctx.msg["message_id"], note)
        except tg.TgError:
            pass


def notify_payment(p):
    u = sv.get_user(p["user_id"])
    if not u:
        return
    lg = u["lang"]
    if p["status"] == "approved":
        ui.notify(u["id"], t(lg, "pay_approved", date=sv.fmt_date(u["premium_until"])))
    elif p["status"] == "rejected":
        ui.notify(u["id"], t(lg, "pay_rejected"))
    elif p["status"] == "expired":
        ui.notify(u["id"], t(lg, "pay_expired"))


def send_reminder(uid, lang, kind, until):
    ui.notify(uid, t(lang, kind, date=sv.fmt_date(until)))


# ------------------------------------------------------------------ callback marshruti
def cb_noop(ctx, parts):
    ctx.ans()


def cb_menu(ctx, parts):
    ctx.ans()
    sv.clear_state(ctx.uid)
    start_screen(ctx.uid, ctx.u, animate=False)


def cb_cancel(ctx, parts):
    ctx.ans(t(ctx.lg, "cancelled"))
    sv.clear_state(ctx.uid)
    try:
        tg.delete_message(ctx.chat, ctx.msg["message_id"])
    except tg.TgError:
        pass


def cb_list(ctx, parts):
    ctx.ans()
    show_list(ctx.chat, ctx.msg, ctx.lg, "movie" if parts[0] == "lm" else "series", int(parts[1]))


def cb_movie(ctx, parts):
    ctx.ans()
    show_movie(ctx.chat, ctx.msg, ctx.u, int(parts[1]))


def cb_fav(ctx, parts):
    mid = int(parts[1])
    m = sv.get_movie(mid)
    if not m or not m["published"]:
        return ctx.ans(t(ctx.lg, "nothing_found"), True)
    now_fav = sv.toggle_favorite(ctx.uid, mid)
    ctx.ans(t(ctx.lg, "fav_added" if now_fav else "fav_removed"))
    try:
        tg.edit_markup(ctx.chat, ctx.msg["message_id"], movie_kb(ctx.lg, ctx.uid, m))
    except tg.TgError:
        pass


def cb_favs(ctx, parts):
    ctx.ans()
    show_favs(ctx.chat, ctx.msg, ctx.lg, int(parts[1]))


def cb_search_page(ctx, parts):
    ctx.ans()
    _, data = sv.get_state(ctx.uid)
    q = data.get("q")
    if not q:
        return show(ctx.chat, ctx.msg, t(ctx.lg, "nothing_found"), ikb([nav_row(ctx.lg)]))
    run_search(ctx.chat, ctx.msg, ctx.lg, q, int(parts[1]))


def cb_episodes(ctx, parts):
    ctx.ans()
    show_episodes(ctx, int(parts[1]), int(parts[2]), int(parts[3]))


def cb_episode(ctx, parts):
    ctx.ans()
    show_episode(ctx, int(parts[1]))


def cb_premium(ctx, parts):
    ctx.ans()
    show_premium(ctx.chat, None, ctx.u)


def cb_lang(ctx, parts):
    if parts[1] not in LANGS:
        return ctx.ans(t(ctx.lg, "invalid"), True)
    sv.set_lang(ctx.uid, parts[1])
    ctx.ans(t(parts[1], "lang_set"))
    start_screen(ctx.uid, ctx.u, animate=False)


def cb_admin(ctx, parts):
    if not sv.is_admin(ctx.uid):
        return ctx.ans("⛔️ Sizda ruxsat yo'q.", True)
    admin.callback(ctx, parts)


ROUTES = {"noop": cb_noop, "menu": cb_menu, "cancel": cb_cancel, "lm": cb_list, "ls": cb_list, "m": cb_movie,
          "w": cb_watch_movie, "we": cb_watch_episode, "wv": cb_watch_variant, "fav": cb_fav, "favs": cb_favs,
          "sr": cb_search_page, "e": cb_episodes, "ep": cb_episode, "prem": cb_premium, "buy": cb_buy,
          "lang": cb_lang, "pay": cb_pay_decide, "a": cb_admin}


def on_callback(c):
    ctx = Ctx(c)
    try:
        if not ctx.msg:
            return ctx.ans()
        u, _ = sv.upsert_user(ctx.frm)
        ctx.u, ctx.lg = u, u["lang"]
        if u["blocked"]:
            return ctx.ans(t(ctx.lg, "blocked"), True)
        parts = ctx.data.split(":")
        if parts[0] == "subcheck":
            if subscription_ok(ctx.uid):
                ctx.ans("✅ Obuna tasdiqlandi")
                return start_screen(ctx.uid, u, animate=False)
            ctx.ans("❌ Avval kanalga obuna bo‘ling", True)
            show_subscription_gate(ctx.uid)
            return
        if not sv.is_admin(ctx.uid) and not subscription_ok(ctx.uid):
            ctx.ans("🔒 Avval kanalga obuna bo‘ling", True)
            show_subscription_gate(ctx.uid)
            return
        fn = ROUTES.get(parts[0])
        if not fn:
            return ctx.ans()
        try:
            fn(ctx, parts)
        except (ValueError, IndexError):
            log.info("noto'g'ri callback: %s", ctx.data[:40])
            ctx.ans(t(ctx.lg, "invalid"), True)
    except tg.TgError as e:
        log.warning("Telegram xatosi (callback): %s", e.description)
    except Exception:
        log.exception("on_callback xatosi")
        ctx.ans("⚠️ Xatolik", True)
    finally:
        ctx.ans()
