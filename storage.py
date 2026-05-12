"""
storage.py
Persistence: history (CSV), favorites (JSON), daily cache (JSON).
All devotional dicts use canonical key "text".
"""
import csv, json, os
from collections import Counter
from datetime import datetime, date

HISTORY_FILE  = "devotional_history.csv"
FAVORITES_FILE = "favorites.json"
DAILY_FILE    = "daily_cache.json"

FIELDS = [
    "date", "topic", "reference", "translation", "text",
    "explanation", "reflection", "application", "memory", "prayer",
]


def _ensure_history():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def _to_row(d: dict) -> dict:
    return {
        "date":        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic":       d.get("topic", ""),
        "reference":   d.get("reference", ""),
        "translation": d.get("translation_id", "KJV"),
        "text":        d.get("text", ""),               # canonical key
        "explanation": d.get("explanation", ""),
        "reflection":  d.get("reflection", ""),
        "application": d.get("application", ""),
        "memory":      d.get("memory", ""),
        "prayer":      d.get("prayer", ""),
    }


# ── History ──────────────────────────────────────────────────

def save_devotional(d: dict):
    _ensure_history()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(_to_row(d))


def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def history_csv_bytes() -> bytes:
    return open(HISTORY_FILE, "rb").read() if os.path.exists(HISTORY_FILE) else b""


def clear_history():
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writeheader()


# ── Favorites ────────────────────────────────────────────────

def load_favorites() -> list[dict]:
    if not os.path.exists(FAVORITES_FILE):
        return []
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_favorite(d: dict):
    favs = load_favorites()
    ref  = d.get("reference", "")
    if not any(f.get("reference") == ref for f in favs):
        entry = {**d, "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
        favs.append(entry)
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, indent=2, ensure_ascii=False)


def remove_favorite(ref: str):
    favs = [f for f in load_favorites() if f.get("reference") != ref]
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, indent=2, ensure_ascii=False)


def is_favorite(ref: str) -> bool:
    return any(f.get("reference") == ref for f in load_favorites())


# ── Daily cache ──────────────────────────────────────────────

def get_cached_daily() -> dict | None:
    if not os.path.exists(DAILY_FILE):
        return None
    try:
        with open(DAILY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("cached_date") == date.today().isoformat():
            return data
    except Exception:
        pass
    return None


def cache_daily(devotional: dict):
    payload = {**devotional, "cached_date": date.today().isoformat()}
    with open(DAILY_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


# ── Analytics ────────────────────────────────────────────────

def topic_counts() -> dict:
    rows   = load_history()
    counts = Counter(r.get("topic", "General") for r in rows if r.get("topic"))
    return dict(counts.most_common())


def get_streak() -> int:
    rows = load_history()
    if not rows:
        return 0
    dates  = sorted({r["date"][:10] for r in rows if r.get("date")}, reverse=True)
    streak = 0
    prev   = None
    for ds in dates:
        try:
            dt = datetime.strptime(ds, "%Y-%m-%d").date()
        except ValueError:
            continue
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