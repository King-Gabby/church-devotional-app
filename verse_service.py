"""
verse_service.py
Bible verse retrieval. All verse dicts use the canonical key: "text".
Never calls AI. All scripture from bible-api.com.
"""
import hashlib, random, requests
from datetime import date
from typing import Tuple

# ── Topic → verse map ───────────────────────────────────────
TOPIC_VERSES: dict[str, list[str]] = {
    "Faith":       ["Hebrews 11:1",       "Romans 10:17",       "Matthew 17:20",    "2 Corinthians 5:7", "James 2:17",       "Mark 11:22"],
    "Anxiety":     ["Philippians 4:6-7",  "1 Peter 5:7",        "Matthew 6:34",     "Isaiah 41:10",      "Psalm 94:19",      "John 14:27"],
    "Purpose":     ["Jeremiah 29:11",     "Ephesians 2:10",     "Romans 8:28",      "Proverbs 19:21",    "Psalm 138:8",      "Isaiah 43:7"],
    "Strength":    ["Isaiah 40:31",       "Philippians 4:13",   "Psalm 46:1",       "2 Corinthians 12:9","Nehemiah 8:10",    "Deuteronomy 31:6"],
    "Hope":        ["Romans 15:13",       "Lamentations 3:22-23","Jeremiah 29:11",  "Psalm 31:24",       "Romans 8:24-25",   "Isaiah 40:31"],
    "Love":        ["1 Corinthians 13:4-7","John 3:16",         "Romans 8:38-39",   "1 John 4:8",        "John 15:13",       "Ephesians 3:17-19"],
    "Wisdom":      ["Proverbs 3:5-6",     "James 1:5",          "Proverbs 2:6",     "Colossians 2:3",    "Psalm 111:10",     "Ecclesiastes 8:1"],
    "Forgiveness": ["Ephesians 4:32",     "Colossians 3:13",    "1 John 1:9",       "Matthew 6:14-15",   "Psalm 103:12",     "Micah 7:18"],
    "Gratitude":   ["1 Thessalonians 5:18","Psalm 107:1",       "Colossians 3:17",  "Psalm 100:4",       "Hebrews 13:15",    "Philippians 4:6"],
    "Peace":       ["John 14:27",         "Isaiah 26:3",        "Philippians 4:7",  "Romans 5:1",        "Colossians 3:15",  "Numbers 6:26"],
    "Courage":     ["Joshua 1:9",         "Psalm 27:1",         "Isaiah 41:13",     "2 Timothy 1:7",     "Deuteronomy 31:6", "1 Corinthians 16:13"],
    "Healing":     ["Jeremiah 17:14",     "Psalm 103:2-3",      "James 5:15",       "Isaiah 53:5",       "Psalm 147:3",      "Exodus 15:26"],
}

# ── Journey plans ────────────────────────────────────────────
JOURNEYS: dict[str, list[dict]] = {
    "Anxiety": [
        {"day": 1, "theme": "God's Presence",  "ref": "Philippians 4:6-7"},
        {"day": 2, "theme": "Cast Your Cares",  "ref": "1 Peter 5:7"},
        {"day": 3, "theme": "Still Waters",     "ref": "Psalm 23:1-3"},
        {"day": 4, "theme": "Perfect Peace",    "ref": "Isaiah 26:3"},
        {"day": 5, "theme": "Do Not Fear",      "ref": "Isaiah 41:10"},
        {"day": 6, "theme": "Find Rest",        "ref": "Matthew 11:28"},
        {"day": 7, "theme": "Joy Returns",      "ref": "Psalm 94:19"},
    ],
    "Faith": [
        {"day": 1, "theme": "What Is Faith?",   "ref": "Hebrews 11:1"},
        {"day": 2, "theme": "Faith That Moves", "ref": "Matthew 17:20"},
        {"day": 3, "theme": "Faith by Hearing", "ref": "Romans 10:17"},
        {"day": 4, "theme": "Walk by Faith",    "ref": "2 Corinthians 5:7"},
        {"day": 5, "theme": "Faith and Works",  "ref": "James 2:17"},
        {"day": 6, "theme": "Shield of Faith",  "ref": "Ephesians 6:16"},
        {"day": 7, "theme": "Author of Faith",  "ref": "Hebrews 12:2"},
    ],
    "Purpose": [
        {"day": 1, "theme": "A Future & Hope",  "ref": "Jeremiah 29:11"},
        {"day": 2, "theme": "His Workmanship",  "ref": "Ephesians 2:10"},
        {"day": 3, "theme": "All Things Work",  "ref": "Romans 8:28"},
        {"day": 4, "theme": "Called by Name",   "ref": "Isaiah 43:1"},
        {"day": 5, "theme": "His Plans Stand",  "ref": "Proverbs 19:21"},
        {"day": 6, "theme": "He Will Complete", "ref": "Psalm 138:8"},
        {"day": 7, "theme": "For His Glory",    "ref": "Isaiah 43:7"},
    ],
    "Strength": [
        {"day": 1, "theme": "Renewed Strength", "ref": "Isaiah 40:31"},
        {"day": 2, "theme": "Through Christ",   "ref": "Philippians 4:13"},
        {"day": 3, "theme": "God Is Refuge",    "ref": "Psalm 46:1"},
        {"day": 4, "theme": "Power in Weakness","ref": "2 Corinthians 12:9"},
        {"day": 5, "theme": "Joy Is Strength",  "ref": "Nehemiah 8:10"},
        {"day": 6, "theme": "Be Strong",        "ref": "Deuteronomy 31:6"},
        {"day": 7, "theme": "Rest Then Rise",   "ref": "Psalm 3:5"},
    ],
}

ALL_TOPICS    = list(TOPIC_VERSES.keys())
JOURNEY_TOPICS = list(JOURNEYS.keys())

# ── Canonical fallback — uses "text" key ─────────────────────
FALLBACK: dict = {
    "reference":      "John 3:16",
    "text":           "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
    "translation_id": "KJV",
    "topic":          "Love",
    "_fallback":      True,
}

_API   = "https://bible-api.com"
_TIMEOUT = 8


def _fetch(ref: str, translation: str = "kjv") -> dict:
    """Raw API call. Returns canonical dict with key 'text'. Raises on failure."""
    url = f"{_API}/{ref.replace(' ', '%20')}?translation={translation}"
    r = requests.get(url, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise ValueError(data["error"])
    return {
        "reference":      data.get("reference", ref).strip(),
        "text":           data.get("text", "").strip(),          # canonical key
        "translation_id": data.get("translation_id", translation).upper(),
    }


def fetch_verse(ref: str, translation: str = "kjv") -> dict:
    """Public: fetch a specific reference. Raises on failure."""
    return _fetch(ref, translation)


def get_verse_for_topic(topic: str, translation: str = "kjv") -> dict:
    refs = TOPIC_VERSES.get(topic)
    if not refs:
        raise ValueError(f"Unknown topic: {topic}")
    weighted = refs[:2] * 2 + refs
    attempts = list(dict.fromkeys([random.choice(weighted)] + refs))
    for ref in attempts:
        try:
            v = _fetch(ref, translation)
            v["topic"] = topic
            return v
        except Exception:
            continue
    fb = dict(FALLBACK)
    fb["topic"] = topic
    return fb


def get_daily_verse(translation: str = "kjv") -> Tuple[dict, str]:
    """
    Deterministic by calendar date — same verse for all users today.
    MD5 of date string → topic index + ref index.
    """
    today = date.today().isoformat()
    seed  = int(hashlib.md5(today.encode()).hexdigest(), 16)
    topic = ALL_TOPICS[seed % len(ALL_TOPICS)]
    refs  = TOPIC_VERSES[topic]
    ref   = refs[seed % len(refs)]
    try:
        v = _fetch(ref, translation)
        v["topic"] = topic
        return v, topic
    except Exception:
        fb = dict(FALLBACK)
        fb["topic"] = topic
        return fb, topic


def get_random_verse(translation: str = "kjv") -> Tuple[dict, str]:
    topic = random.choice(ALL_TOPICS)
    return get_verse_for_topic(topic, translation), topic


def get_journey_verse(topic: str, day: int, translation: str = "kjv") -> dict:
    plan  = JOURNEYS.get(topic, [])
    entry = next((e for e in plan if e["day"] == day), None)
    if not entry:
        raise ValueError(f"No journey entry: {topic} day {day}")
    try:
        v = _fetch(entry["ref"], translation)
        v.update({"topic": topic, "journey_theme": entry["theme"], "journey_day": day})
        return v
    except Exception:
        fb = dict(FALLBACK)
        fb.update({"topic": topic, "journey_theme": entry["theme"], "journey_day": day})
        return fb


def validate_ref(ref: str) -> bool:
    if not ref or len(ref.strip()) < 3:
        return False
    return any(c.isalpha() for c in ref) and any(c.isdigit() for c in ref)