"""
utils/storage.py
CSV + JSON persistence: history, favorites, analytics.
Interface-first — swap to SQLite/Postgres by reimplementing these functions only.
"""

import csv, json, os
from collections import Counter
from datetime import datetime, date
from formatters import CSV_FIELDS, to_row

HISTORY_FILE  = "devotional_history.csv"
FAVORITES_FILE = "favorites.json"


# ── History ─────────────────────────────────────────────────

def _ensure_history():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

def save_devotional(d: dict):
    _ensure_history()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(to_row(d))

def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_history_csv_bytes() -> bytes:
    return open(HISTORY_FILE, "rb").read() if os.path.exists(HISTORY_FILE) else b""

def clear_history():
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


# ── Favorites ───────────────────────────────────────────────

def load_favorites() -> list[dict]:
    if not os.path.exists(FAVORITES_FILE):
        return []
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_favorite(d: dict):
    favs = load_favorites()
    # Deduplicate by reference
    if not any(f.get("reference") == d.get("reference") for f in favs):
        favs.append({**d, "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, indent=2, ensure_ascii=False)

def remove_favorite(reference: str):
    favs = [f for f in load_favorites() if f.get("reference") != reference]
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, indent=2, ensure_ascii=False)

def is_favorite(reference: str) -> bool:
    return any(f.get("reference") == reference for f in load_favorites())


# ── Daily verse cache ────────────────────────────────────────

DAILY_CACHE_FILE = "daily_cache.json"

def get_cached_daily() -> dict | None:
    if not os.path.exists(DAILY_CACHE_FILE):
        return None
    with open(DAILY_CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("date") == date.today().isoformat():
        return data
    return None

def cache_daily(d: dict, topic: str):
    payload = {**d, "date": date.today().isoformat(), "topic": topic}
    with open(DAILY_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


# ── Analytics ───────────────────────────────────────────────

def get_topic_analytics() -> dict:
    history = load_history()
    counts = Counter(r.get("topic","Unknown") for r in history if r.get("topic"))
    return dict(counts.most_common())

def get_streak() -> int:
    """Count consecutive days with at least one devotional generated."""
    history = load_history()
    if not history:
        return 0
    dates = sorted({r["date"][:10] for r in history if r.get("date")}, reverse=True)
    streak = 0
    prev = None
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d").date()
        if prev is None:
            if (date.today() - dt).days > 1:
                break
            streak = 1
        elif (prev - dt).days == 1:
            streak += 1
        else:
            break
        prev = dt
    return streak
