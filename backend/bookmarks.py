"""書籤管理 — 儲存常用地點，支援自訂分類"""

import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

BOOKMARKS_FILE = Path(__file__).resolve().parent.parent / "data" / "bookmarks.json"


def _load():
    if not BOOKMARKS_FILE.exists():
        return []
    return json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))


def _save(bookmarks):
    BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    BOOKMARKS_FILE.write_text(
        json.dumps(bookmarks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_bookmarks():
    return _load()


def add_bookmark(name, lat, lng, category="預設"):
    bookmarks = _load()
    bm = {
        "id": uuid.uuid4().hex[:8],
        "name": name,
        "lat": lat,
        "lng": lng,
        "category": category,
    }
    bookmarks.append(bm)
    _save(bookmarks)
    return bm


def delete_bookmark(bookmark_id):
    bookmarks = _load()
    bookmarks = [b for b in bookmarks if b["id"] != bookmark_id]
    _save(bookmarks)


def list_categories():
    bookmarks = _load()
    cats = sorted(set(b.get("category", "預設") for b in bookmarks))
    return cats if cats else ["預設"]
