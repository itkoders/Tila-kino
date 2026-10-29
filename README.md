# TILAKINO Cinema — Telegram kino boti (Flask + webhook)

`kino_bot.py` dagi imkoniyatlar (kod bo'yicha kino, nom qidiruv, referal, chek bilan to'lov, broadcast, eslatma)
saqlangan va TILAKINO talablariga ko'ra qayta qurilgan: Flask webhook, PostgreSQL/SQLite, admin panel, Premium,
seriallar, 4 tilli interfeys, animatsiyali bot va sayt.

## Fayllar
| Fayl | Vazifasi |
|---|---|
| `app.py` | Flask: `/webhook`, `/health`, `/payments/callback/generic`, `/cron/tick`, sayt va `/api/*` |
| `handlers.py` | Foydalanuvchi tomoni (menyu, katalog, tomosha, sevimlilar, Premium, profil) |
| `admin.py` | Admin panel (kino/serial/epizod, Premium, foydalanuvchilar, homiy, statistika, broadcast, yordamchi adminlar) |
| `services.py` / `db.py` | Biznes mantiq va ma'lumotlar bazasi (jadvallar, indekslar, tranzaksiyalar) |
| `tg.py` / `ui.py` | Telegram API mijozi, tugmalar, **animatsiyalar** |
| `i18n.py` | uz / ru / en / tg matnlari |
| `payment_providers.py` | To'lov provayderlari (hozir: imzolangan `generic` webhook) |
| `scheduler.py` | Muddat tugashi, 3 kunlik va tugash kuni eslatmalari |
| `templates/` | Animatsiyali sayt (mobilga moslashgan) |
| `tests/` | Avtomatik testlar repozitoriyda hozircha mavjud emas; deploydan oldin alohida tekshirish kerak |

## Muhit o'zgaruvchilari (Render → Environment)
| Nomi | Majburiy | Izoh |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ha | @BotFather tokeni (chatga yozmang!) |
| `WEBHOOK_SECRET` | ha | O'zingiz o'ylab topgan uzun kalit: faqat `A-Z a-z 0-9 _ -` |
| `DATABASE_URL` | **ha (production)** | PostgreSQL manzili. Bo'lmasa SQLite ishlatiladi va Render bepul rejasida **qayta ishga tushganda ma'lumot yo'qoladi** |
| `ADMIN_ID` | yo'q | Standart `6359925487` |
| `RENDER_EXTERNAL_URL` | avtomatik | Render o'zi beradi; webhook shu manzilga o'rnatiladi |
| `BOT_USERNAME` | tavsiya | Botning @usernamesi (taklif havolasi va saytdagi havola uchun) |
| `CRON_SECRET` | tavsiya | `/cron/tick` himoyasi |
| `PAYMENT_CALLBACK_SECRET` | ixtiyoriy | Faqat avtomatik to'lov ulansa |
| `ANIMATIONS`, `ANIM_DELAY` | yo'q | Animatsiyani o'chirish (`0`) / kadr tezligi (soniya, standart 0.35) |
| `WELCOME_GIF_FILE_ID` | yo'q | Telegramdagi TILAKINO kirish GIF animatsiyasining `file_id` qiymati; bo'sh bo'lsa matnli animatsiya ishlaydi |

## Android'dan o'rnatish (brauzer yetadi)
1. **GitHub** (`itkoders/Kino`) → *Add file → Upload files*: ushbu papkadagi barcha fayllarni (`templates/` va `tests/` bilan) yuklang → *Commit*.
   Eski `kino_bot.py` ga tegmasangiz ham bo'ladi (Render uni ishlatmaydi).
2. **Bepul PostgreSQL**: Render → *New → PostgreSQL* (yoki Neon/Supabase) → *Internal/External Database URL* ni nusxalang.
3. **Render** → xizmat `tilakino-telegram-bot` → *Settings*:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60`
   - Health Check Path: `/health`
4. *Environment* bo'limida yuqoridagi o'zgaruvchilarni kiriting (`DATABASE_URL` ni ham).
5. *Manual Deploy → Deploy latest commit*. Ishga tushganda webhook avtomatik o'rnatiladi.
6. Eslatmalar uchun (bepul reja uxlab qoladi): cron-job.org da har 10 daqiqada
   `https://tilakino-telegram-bot.onrender.com/cron/tick?key=CRON_SECRET_QIYMATI` ni chaqiring.

## Birinchi sozlash (Telegramda)
1. Botga `/start`, keyin `/admin`.
2. **💎 Premium → 💳 Karta ma'lumoti** — to'lov rekvizitlarini kiriting (bo'sh bo'lsa to'lov ochilmaydi).
3. **🎬 Kino va seriallar → ➕ Kino qo'shish** — savollarga javob bering, poster yuboring, so'ng kartadan
   **📀 Medium video** (oddiy foydalanuvchi) va **💎 High video** (Premium) ni yuboring.
   Katta fayllar uchun **🔗 havola** (https) ham qo'shish mumkin — saytda ko'rinadi.
4. Faqat o'zingizga tegishli yoki tarqatishga ruxsat berilgan kontentni yuklang.

## Kirish GIF animatsiyasini sozlash\nTelegramda botga GIF animatsiyasini yuboring va caption (izoh) qatoriga `/setwelcome` deb yozing. Buni faqat admin qila oladi. Bot GIF `file_id` qiymatini ma'lumotlar bazasida saqlaydi; GIF yuklanmasa, matnli animatsiyaga qaytadi.\n\n## Animatsiyalar
- Botda: `/start` da yozilib chiqadigan TILAKINO, tomosha oldidan progress-bar, sahifalar xabarni joyida yangilanadi.
- Saytda: kartalar ketma-ket paydo bo'lishi, poster yuklanguncha shimmer, hover effekti, player va epizodlar animatsiyasi;
  `prefers-reduced-motion` yoqilgan qurilmalarda o'chadi.

## Ruxsatlar
Asosiy admin (ID `6359925487`) hamma narsani qila oladi. Yordamchilar: **🛡 Yordamchi adminlar** → `ID catalog,stats` yoki `ID all`.
Ruxsatlar: `catalog, premium, users, sponsor, stats, broadcast`. Yordamchi asosiy adminni o'chira/almashtira olmaydi.
Tekshiruv faqat Telegram yuborgan raqamli ID bo'yicha.

## Muammolarni hal qilish
- `/health` da `problems` ro'yxati — qaysi o'zgaruvchi yetishmayotganini ko'rsatadi.
- Bot javob bermasa: Render *Logs*; `WEBHOOK_SECRET` belgilari mosligini tekshiring.
- Ma'lumot yo'qolsa: `DATABASE_URL` yo'q (SQLite vaqtinchalik).
- "Videoni yuborib bo'lmadi": file_id boshqa bot tokeniga tegishli — videoni shu bot orqali qayta yuklang.

## Tekshirish ro'yxati (haqiqiy holat)
| Holat | Element |
|---|---|
| ⚠️ Avtomatik test natijasi tasdiqlanmagan | Repozitoriyda `tests/` papkasi yo'q; 67 ta test o'tgan degan oldingi yozuv tasdiqlanmagan |
| ⚠️ Sinalmagan (sizning muhitingizda tekshiring) | Render deploy, haqiqiy webhook, haqiqiy Telegram xabarlari, **PostgreSQL** (kod yozilgan, lekin sinov SQLite'da o'tdi), gunicorn |
| ⛔️ Ulanmagan | Click/Payme/Uzum kabi aniq to'lov provayderlari (merchant hisobi kerak). Hozir: qo'lda tasdiqlash + imzolangan `generic` webhook |
| ℹ️ Cheklov | Poster/video Telegram file_id orqali; sayt faqat `https` tashqi havola (medium) ni o'ynatadi, High faqat botda |

Testlarni ishga tushirish (kompyuter bo'lsa): `pip install -r requirements-dev.txt && pytest -q`
