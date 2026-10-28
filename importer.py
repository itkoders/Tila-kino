
# importer.py
"""Internet Archive'dan huquqi tekshirilishi mumkin bo'lgan
kino nomzodlarini topish va Tilakino bazasiga yashirin qo'shish.
"""

import logging
import random
import re
from urllib.parse import quote

import requests

import db
import services

log = logging.getLogger("tilakino.importer")

SEARCH_URL = "https://archive.org/advancedsearch.php"
METADATA_URL = "https://archive.org/metadata/{}"
TIMEOUT = 25

# Tijoriy foydalanishga ruxsat beruvchi keng tarqalgan litsenziyalar.
# Har bir elementning huquqiy holati baribir alohida tekshirilishi kerak.
ALLOWED_LICENSE_PARTS = (
    "creativecommons.org/publicdomain/zero",
    "creativecommons.org/licenses/by/",
    "creativecommons.org/licenses/by-sa/",
    "creativecommons.org/licenses/by-nd/",
    "publicdomain",
)


def search_latest(limit=20):
    response = requests.get(
        SEARCH_URL,
        params=[
            ("q", 'mediatype:movies AND licenseurl:*'),
            ("fl[]", "identifier"),
            ("fl[]", "title"),
            ("sort[]", "addeddate desc"),
            ("rows", str(limit)),
            ("output", "json"),
        ],
        timeout=TIMEOUT,
        headers={"User-Agent": "TilakinoRightsReview/1.0"},
    )
    response.raise_for_status()
    return response.json().get("response", {}).get("docs", [])


def get_item(identifier):
    response = requests.get(
        METADATA_URL.format(quote(identifier, safe="")),
        timeout=TIMEOUT,
        headers={"User-Agent": "TilakinoRightsReview/1.0"},
    )
    response.raise_for_status()
    return response.json()


def license_is_candidate(metadata):
    meta = metadata.get("metadata") or {}
    license_url = str(meta.get("licenseurl") or "").lower()

    # Non-commercial litsenziyalarni va litsenziyasi yo'qlarni rad etamiz.
    if not license_url or "by-nc" in license_url:
        return False

    return any(part in license_url for part in ALLOWED_LICENSE_PARTS)


def find_mp4(metadata):
    files = metadata.get("files") or []

    for item in files:
        name = str(item.get("name") or "")
        if not name.lower().endswith(".mp4"):
            continue
        if item.get("private") == "true":
            continue

        # Katta fayl ekanligi yoki ochilishi kafolatlanmaydi.
        return name

    return None


def new_code():
    for _ in range(100):
        code = f"{random.randint(0, 9999):04d}"
        if not services.get_movie_by_code(code, published_only=False):
            return code
    raise RuntimeError("Bo'sh 4 xonali kino kodi topilmadi")


def import_candidates(limit=20):
    # DB va sxema app.py dagi kabi ishga tushiriladi.
    db.init()
    db.init_schema()

    result = {
        "checked": 0,
        "added_pending_review": 0,
        "skipped": 0,
        "errors": 0,
    }

    for item in search_latest(limit):
        identifier = item.get("identifier")
        title = str(item.get("title") or "").strip()

        if not identifier or not title:
            result["skipped"] += 1
            continue

        result["checked"] += 1

        try:
            metadata = get_item(identifier)
            meta = metadata.get("metadata") or {}

            # Oldin katalogda shu nomli kino borligini tekshiramiz.
            if services.admin_find(title, limit=20):
                result["skipped"] += 1
                continue

            if not license_is_candidate(metadata):
                result["skipped"] += 1
                continue

            mp4_name = find_mp4(metadata)
            if not mp4_name:
                result["skipped"] += 1
                continue

            # Tilakino loyihasidagi til kodlari bilan mos.
            # Avtomatik tarjima qilinmagan, original nom saqlanadi.
            year = None
            date_value = str(meta.get("year") or meta.get("date") or "")
            match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", date_value)
            if match:
                year = match.group(1)

            movie = services.create_movie({
                "code": new_code(),
                "kind": "movie",
                "title": title[:200],
                "year": year,
                "country": None,
                "genre": "Tekshiruv kutilmoqda",
                "language": "uz",
                "description": (
                    "Manba: Internet Archive. "
                    f"Manba identifikatori: {identifier}. "
                    f"Litsenziya: {meta.get('licenseurl', 'noma’lum')}. "
                    "Nashr qilishdan oldin administrator huquq va faylni tekshirishi kerak."
                ),
                "rating": None,
                "poster_file_id": None,
            })

            # Muhim: foydalanuvchilarga hozircha ko'rsatilmaydi.
            services.set_published(movie["id"], False)

            video_url = (
                "https://archive.org/download/"
                + quote(identifier, safe="")
                + "/"
                + quote(mp4_name, safe="/")
            )

            services.set_variant(
                quality="medium",
                movie_id=movie["id"],
                external_url=video_url,
                label="Internet Archive — tekshirish kerak",
            )

            result["added_pending_review"] += 1
            log.info(
                "Tekshiruvga qo'shildi: code=%s id=%s",
                movie["code"], identifier
            )

        except ValueError as exc:
            # Masalan, kod takrorlangan bo'lishi mumkin.
            result["skipped"] += 1
            log.info("Kino o'tkazib yuborildi: %s", exc)
        except Exception:
            result["errors"] += 1
            log.exception("Import xatosi: %s", identifier)

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(import_candidates())
    
