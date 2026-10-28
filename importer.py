
# importer.py
import requests

SEARCH_URL = "https://archive.org/advancedsearch.php"


def search_latest(limit=10):
    params = [
        ("q", "mediatype:movies AND licenseurl:*publicdomain*"),
        ("fl[]", "identifier"),
        ("fl[]", "title"),
        ("fl[]", "date"),
        ("sort[]", "addeddate desc"),
        ("rows", str(limit)),
        ("output", "json"),
    ]

    response = requests.get(
        SEARCH_URL,
        params=params,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("response", {}).get("docs", [])


if __name__ == "__main__":
    for movie in search_latest():
        print(
            movie.get("title", "Nomsiz"),
            movie.get("identifier", ""),
            movie.get("date", ""),
        )
      
