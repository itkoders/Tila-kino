# -*- coding: utf-8 -*-
"""Interfeys tarjimalari: uz (to'liq), ru / en / tg. Tarjima yo'q kalit uchun o'zbekcha ishlatiladi."""

LANGS = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English", "tg": "🇹🇯 Тоҷикӣ"}

MENU_KEYS = ["menu_movies", "menu_search", "menu_code", "menu_series",
             "menu_favs", "menu_premium", "menu_profile", "menu_sub"]

TEXTS = {
    "uz": {
        "menu_movies": "🎬 Kinolar", "menu_search": "🔎 Kino qidirish", "menu_code": "🔢 Kod orqali topish",
        "menu_series": "📺 Seriallar", "menu_favs": "❤️ Sevimlilar", "menu_premium": "💎 Premium sotib olish",
        "menu_profile": "👤 Mening profilim", "menu_sub": "📊 Obuna muddati va tomosha tarixi",
        "welcome": "Xush kelibsiz, <b>{name}</b>! 🍿\n\nKino kodini yuboring yoki menyudan tanlang.\n{status}",
        "status_premium": "💎 Premium: {date} gacha", "status_free": "🆓 Oddiy tarif",
        "btn_back": "⬅️ Orqaga", "btn_menu": "🏠 Menyu", "btn_cancel": "❌ Bekor qilish",
        "btn_confirm": "✅ Tasdiqlash", "btn_watch": "▶️ Tomosha qilish", "btn_web": "Saytda ko'rish",
        "fav_add": "🤍 Sevimlilarga", "fav_del": "💔 Sevimlilardan olib tashlash",
        "fav_added": "❤️ Sevimlilarga qo'shildi", "fav_removed": "Sevimlilardan olib tashlandi",
        "episodes": "Epizodlar", "season": "{n}-fasl", "ep_prev": "⏮ Oldingi", "ep_next": "Keyingi ⏭",
        "unknown": "🤔 Tushunmadim. Menyudan foydalaning yoki kino kodini yuboring.",
        "invalid": "⚠️ Noto'g'ri kiritish. Qaytadan urinib ko'ring.",
        "blocked": "⛔️ Siz botdan foydalanishdan chetlatilgansiz.",
        "cancelled": "Bekor qilindi.", "search_prompt": "🔎 Kino yoki serial nomini yozing:",
        "code_prompt": "🔢 Kino kodini yuboring (masalan: 1234):",
        "nothing_found": "😕 Hech narsa topilmadi.", "catalog_empty": "Hozircha katalog bo'sh.",
        "movies_title": "🎬 <b>Kinolar</b> (yangilari birinchi)", "series_title": "📺 <b>Seriallar</b>",
        "results_title": "🔎 <b>Natijalar:</b> {q}", "favs_title": "❤️ <b>Sevimlilar</b>",
        "favs_empty": "Sevimlilar ro'yxati bo'sh.", "no_video": "🚫 Bu uchun video hali qo'shilmagan.",
        "premium_only": "💎 Bu kinoning faqat yuqori sifatli versiyasi mavjud — u Premium uchun.",
        "quality_missing": "ℹ️ Yuqori sifat mavjud emas. Mavjud versiyani ko'rishingiz mumkin:",
        "btn_play_alt": "▶️ {q} sifatda ko'rish", "loading": "🎬 Tayyorlanmoqda", "sending": "Yuborilmoqda",
        "premium_title": "💎 <b>Premium</b>\n\n• Yuqori sifatli video\n• Reklamasiz\n• Holat: {status}\n\nMuddatni tanlang:",
        "plan_btn": "{label} — {price} so'm",
        "pay_instr": "💳 <b>To'lov #{ref}</b>\nTarif: {label}\nSumma: <b>{price} so'm</b>\n\n{card}\n\n"
                     "To'lovdan so'ng <b>chek rasmini</b> shu yerga yuboring. Izohga <code>{ref}</code> yozing.\n"
                     "Admin tekshirib tasdiqlaydi.",
        "pay_no_card": "To'lov rekvizitlari hali kiritilmagan. Admin bilan bog'laning.",
        "pay_need_proof": "📸 Iltimos, chek rasmini (yoki faylini) yuboring.",
        "pay_proof_ok": "✅ Chek adminga yuborildi. Qaror haqida xabar beramiz.",
        "pay_approved": "✅ To'lov tasdiqlandi! Premium {date} gacha faol.",
        "pay_rejected": "❌ To'lov rad etildi. Savol bo'lsa admin bilan bog'laning.",
        "pay_expired": "⌛️ To'lov so'rovi muddati tugadi.",
        "profile": "👤 <b>Profil</b>\n\n🆔 ID: <code>{id}</code>\n📛 Ism: {name}\n🌐 Til: {lang}\n"
                   "{status}\n👥 Takliflar: {refs}\n🔗 Taklif havolasi:\n{link}",
        "sub_title": "📊 <b>Obuna va tomosha tarixi</b>", "sub_none": "Obunalar yo'q",
        "pay_hist": "To'lovlar", "watch_hist": "So'nggi ko'rilganlar", "hist_empty": "Hali hech narsa ko'rilmagan",
        "remind3": "⏰ Premium obunangiz 3 kundan keyin ({date}) tugaydi. «💎 Premium sotib olish» orqali uzaytiring.",
        "remind0": "⌛️ Premium obunangiz bugun ({date}) tugaydi.",
        "lang_set": "✅ Til o'zgartirildi.", "ref_bonus": "🎉 Do'stingiz qo'shildi! Sizga +{days} kun Premium berildi.",
        "sponsor": "📢 <b>Homiy:</b>\n{text}", "page": "{p}/{n}", "open_site": "Saytda ochish",
        "link_msg": "🔗 Havola orqali ko'rish:", "ext_btn": "🔗 Ko'rish", "ep_line": "{s}-fasl {n}-epizod",
    },
    "ru": {
        "menu_movies": "🎬 Фильмы", "menu_search": "🔎 Поиск фильма", "menu_code": "🔢 Поиск по коду",
        "menu_series": "📺 Сериалы", "menu_favs": "❤️ Избранное", "menu_premium": "💎 Купить Premium",
        "menu_profile": "👤 Мой профиль", "menu_sub": "📊 Подписка и история просмотров",
        "welcome": "Добро пожаловать, <b>{name}</b>! 🍿\n\nОтправьте код фильма или выберите в меню.\n{status}",
        "status_premium": "💎 Premium до {date}", "status_free": "🆓 Обычный тариф",
        "btn_back": "⬅️ Назад", "btn_menu": "🏠 Меню", "btn_cancel": "❌ Отмена", "btn_confirm": "✅ Подтвердить",
        "btn_watch": "▶️ Смотреть", "btn_web": "Смотреть на сайте",
        "fav_add": "🤍 В избранное", "fav_del": "💔 Убрать из избранного",
        "fav_added": "❤️ Добавлено в избранное", "fav_removed": "Убрано из избранного",
        "episodes": "Эпизоды", "season": "Сезон {n}", "ep_prev": "⏮ Предыдущая", "ep_next": "Следующая ⏭",
        "unknown": "🤔 Не понял. Используйте меню или отправьте код фильма.",
        "invalid": "⚠️ Неверный ввод. Попробуйте ещё раз.", "blocked": "⛔️ Доступ к боту для вас закрыт.",
        "cancelled": "Отменено.", "search_prompt": "🔎 Напишите название фильма или сериала:",
        "code_prompt": "🔢 Отправьте код фильма (например: 1234):", "nothing_found": "😕 Ничего не найдено.",
        "movies_title": "🎬 <b>Фильмы</b> (сначала новые)", "series_title": "📺 <b>Сериалы</b>",
        "favs_title": "❤️ <b>Избранное</b>", "favs_empty": "Список избранного пуст.",
        "no_video": "🚫 Видео ещё не добавлено.", "loading": "🎬 Готовим", "plan_btn": "{label} — {price} сум",
        "pay_approved": "✅ Оплата подтверждена! Premium активен до {date}.",
        "pay_rejected": "❌ Оплата отклонена. Если есть вопросы — свяжитесь с админом.",
        "remind3": "⏰ Ваш Premium закончится через 3 дня ({date}). Продлите в «💎 Купить Premium».",
        "remind0": "⌛️ Ваш Premium заканчивается сегодня ({date}).", "lang_set": "✅ Язык изменён.",
    },
    "en": {
        "menu_movies": "🎬 Movies", "menu_search": "🔎 Search", "menu_code": "🔢 Find by code",
        "menu_series": "📺 Series", "menu_favs": "❤️ Favorites", "menu_premium": "💎 Buy Premium",
        "menu_profile": "👤 My profile", "menu_sub": "📊 Subscription & watch history",
        "welcome": "Welcome, <b>{name}</b>! 🍿\n\nSend a movie code or pick from the menu.\n{status}",
        "status_premium": "💎 Premium until {date}", "status_free": "🆓 Free plan",
        "btn_back": "⬅️ Back", "btn_menu": "🏠 Menu", "btn_cancel": "❌ Cancel", "btn_confirm": "✅ Confirm",
        "btn_watch": "▶️ Watch", "btn_web": "Watch on website",
        "fav_add": "🤍 Add to favorites", "fav_del": "💔 Remove from favorites",
        "fav_added": "❤️ Added to favorites", "fav_removed": "Removed from favorites",
        "episodes": "Episodes", "season": "Season {n}", "ep_prev": "⏮ Previous", "ep_next": "Next ⏭",
        "unknown": "🤔 I didn't get that. Use the menu or send a movie code.",
        "invalid": "⚠️ Invalid input. Please try again.", "blocked": "⛔️ You are blocked from using this bot.",
        "cancelled": "Cancelled.", "search_prompt": "🔎 Type a movie or series title:",
        "code_prompt": "🔢 Send the movie code (e.g. 1234):", "nothing_found": "😕 Nothing found.",
        "movies_title": "🎬 <b>Movies</b> (newest first)", "series_title": "📺 <b>Series</b>",
        "favs_title": "❤️ <b>Favorites</b>", "favs_empty": "Your favorites list is empty.",
        "no_video": "🚫 No video has been added yet.", "loading": "🎬 Preparing", "plan_btn": "{label} — {price} UZS",
        "pay_approved": "✅ Payment approved! Premium active until {date}.",
        "pay_rejected": "❌ Payment rejected. Contact the admin if you have questions.",
        "remind3": "⏰ Your Premium ends in 3 days ({date}). Renew via «💎 Buy Premium».",
        "remind0": "⌛️ Your Premium ends today ({date}).", "lang_set": "✅ Language changed.",
    },
    "tg": {
        "menu_movies": "🎬 Филмҳо", "menu_search": "🔎 Ҷустуҷӯи филм", "menu_code": "🔢 Ҷустуҷӯ бо код",
        "menu_series": "📺 Серияҳо", "menu_favs": "❤️ Дӯстдошта", "menu_premium": "💎 Харидани Premium",
        "menu_profile": "👤 Профили ман", "menu_sub": "📊 Обуна ва таърихи тамошо",
        "welcome": "Хуш омадед, <b>{name}</b>! 🍿\n\nКоди филмро фиристед ё аз меню интихоб кунед.\n{status}",
        "status_premium": "💎 Premium то {date}", "status_free": "🆓 Тарифи оддӣ",
        "btn_back": "⬅️ Бозгашт", "btn_menu": "🏠 Меню", "btn_cancel": "❌ Бекор кардан",
        "btn_confirm": "✅ Тасдиқ", "btn_watch": "▶️ Тамошо", "btn_web": "Дар сайт тамошо кардан",
        "fav_add": "🤍 Ба дӯстдошта", "fav_del": "💔 Аз дӯстдошта тоза кардан",
        "fav_added": "❤️ Ба дӯстдошта илова шуд", "fav_removed": "Аз дӯстдошта тоза шуд",
        "episodes": "Қисмҳо", "season": "Фасли {n}", "ep_prev": "⏮ Пешина", "ep_next": "Минбаъда ⏭",
        "unknown": "🤔 Нафаҳмидам. Менюро истифода баред ё коди филмро фиристед.",
        "invalid": "⚠️ Воридкунии нодуруст. Бори дигар кӯшиш кунед.", "blocked": "⛔️ Дастрасии шумо ба бот баста шудааст.",
        "cancelled": "Бекор шуд.", "search_prompt": "🔎 Номи филм ё сериалро нависед:",
        "code_prompt": "🔢 Коди филмро фиристед (масалан: 1234):", "nothing_found": "😕 Чизе ёфт нашуд.",
        "movies_title": "🎬 <b>Филмҳо</b> (аввал нав)", "series_title": "📺 <b>Серияҳо</b>",
        "favs_title": "❤️ <b>Дӯстдошта</b>", "favs_empty": "Рӯйхати дӯстдошта холӣ аст.",
        "no_video": "🚫 Видео ҳанӯз илова нашудааст.", "loading": "🎬 Омода мешавад", "plan_btn": "{label} — {price} сӯм",
        "pay_approved": "✅ Пардохт тасдиқ шуд! Premium то {date} фаъол аст.",
        "pay_rejected": "❌ Пардохт рад шуд. Агар савол дошта бошед, бо админ тамос гиред.",
        "remind3": "⏰ Premium-и шумо баъд аз 3 рӯз ({date}) тамом мешавад. Тавассути «💎 Харидани Premium» дароз кунед.",
        "remind0": "⌛️ Premium-и шумо имрӯз ({date}) тамом мешавад.", "lang_set": "✅ Забон иваз шуд.",
    },
}


def t(language, key, **kw):
    s = TEXTS.get(language, {}).get(key) or TEXTS["uz"][key]
    return s.format(**kw) if kw else s


def menu_label_map():
    """{tugma matni: kalit} barcha tillar uchun (menyu tugmasi bosilganini aniqlash)."""
    out = {}
    for lg in TEXTS:
        for k in MENU_KEYS:
            out[t(lg, k)] = k
    return out
