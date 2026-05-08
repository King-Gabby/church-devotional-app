"""
services/verse_service.py
Bible verse retrieval — API, topic maps, manual input, daily verse.
NEVER calls AI. Verse text always comes from bible-api.com.
"""

import hashlib
import random
import requests
from datetime import date
from typing import Tuple

TOPIC_VERSES: dict[str, list[str]] = {
    "Faith":       ["Hebrews 11:1", "Romans 10:17", "Matthew 17:20", "2 Corinthians 5:7", "James 2:17", "Mark 11:22"],
    "Anxiety":     ["Philippians 4:6-7", "1 Peter 5:7", "Matthew 6:34", "Isaiah 41:10", "Psalm 94:19", "John 14:27"],
    "Purpose":     ["Jeremiah 29:11", "Ephesians 2:10", "Romans 8:28", "Proverbs 19:21", "Psalm 138:8", "Isaiah 43:7"],
    "Strength":    ["Isaiah 40:31", "Philippians 4:13", "Psalm 46:1", "2 Corinthians 12:9", "Nehemiah 8:10", "Deuteronomy 31:6"],
    "Hope":        ["Romans 15:13", "Lamentations 3:22-23", "Jeremiah 29:11", "Psalm 31:24", "Romans 8:24-25", "Isaiah 40:31"],
    "Love":        ["1 Corinthians 13:4-7", "John 3:16", "Romans 8:38-39", "1 John 4:8", "John 15:13", "Ephesians 3:17-19"],
    "Wisdom":      ["Proverbs 3:5-6", "James 1:5", "Proverbs 2:6", "Colossians 2:3", "Psalm 111:10", "Ecclesiastes 8:1"],
    "Forgiveness": ["Ephesians 4:32", "Colossians 3:13", "1 John 1:9", "Matthew 6:14-15", "Psalm 103:12", "Micah 7:18"],
    "Gratitude":   ["1 Thessalonians 5:18", "Psalm 107:1", "Colossians 3:17", "Psalm 100:4", "Hebrews 13:15", "Philippians 4:6"],
    "Peace":       ["John 14:27", "Isaiah 26:3", "Philippians 4:7", "Romans 5:1", "Colossians 3:15", "Numbers 6:26"],
    "Courage":     ["Joshua 1:9", "Psalm 27:1", "Isaiah 41:13", "2 Timothy 1:7", "Deuteronomy 31:6", "1 Corinthians 16:13"],
    "Healing":     ["Jeremiah 17:14", "Psalm 103:2-3", "James 5:15", "Isaiah 53:5", "Psalm 147:3", "Exodus 15:26"],
}

# 7-day journey plans
TOPIC_JOURNEYS: dict[str, list[dict]] = {
    "Anxiety": [
        {"day": 1, "theme": "God's Presence", "ref": "Philippians 4:6-7"},
        {"day": 2, "theme": "Cast Your Burdens", "ref": "1 Peter 5:7"},
        {"day": 3, "theme": "Still Waters", "ref": "Psalm 23:1-3"},
        {"day": 4, "theme": "Perfect Peace", "ref": "Isaiah 26:3"},
        {"day": 5, "theme": "Do Not Fear", "ref": "Isaiah 41:10"},
        {"day": 6, "theme": "Rest in Him", "ref": "Matthew 11:28"},
        {"day": 7, "theme": "Joy Returns", "ref": "Psalm 94:19"},
    ],
    "Faith": [
        {"day": 1, "theme": "What Is Faith?", "ref": "Hebrews 11:1"},
        {"day": 2, "theme": "Faith That Moves", "ref": "Matthew 17:20"},
        {"day": 3, "theme": "Faith by Hearing", "ref": "Romans 10:17"},
        {"day": 4, "theme": "Walking by Faith", "ref": "2 Corinthians 5:7"},
        {"day": 5, "theme": "Faith With Works", "ref": "James 2:17"},
        {"day": 6, "theme": "Shield of Faith", "ref": "Ephesians 6:16"},
        {"day": 7, "theme": "Author of Faith", "ref": "Hebrews 12:2"},
    ],
    "Purpose": [
        {"day": 1, "theme": "You Are Created", "ref": "Jeremiah 29:11"},
        {"day": 2, "theme": "His Workmanship", "ref": "Ephesians 2:10"},
        {"day": 3, "theme": "All Things Work", "ref": "Romans 8:28"},
        {"day": 4, "theme": "Called by Name", "ref": "Isaiah 43:1"},
        {"day": 5, "theme": "His Plans Stand", "ref": "Proverbs 19:21"},
        {"day": 6, "theme": "Complete the Work", "ref": "Psalm 138:8"},
        {"day": 7, "theme": "Glory to God", "ref": "Isaiah 43:7"},
    ],
    "Strength": [
        {"day": 1, "theme": "Renewed Strength", "ref": "Isaiah 40:31"},
        {"day": 2, "theme": "Through Christ", "ref": "Philippians 4:13"},
        {"day": 3, "theme": "God Is Our Refuge", "ref": "Psalm 46:1"},
        {"day": 4, "theme": "Power in Weakness", "ref": "2 Corinthians 12:9"},
        {"day": 5, "theme": "Joy Is Strength", "ref": "Nehemiah 8:10"},
        {"day": 6, "theme": "Be Strong", "ref": "Deuteronomy 31:6"},
        {"day": 7, "theme": "Rest Then Rise", "ref": "Psalm 3:5"},
    ],
}

ALL_TOPICS = list(TOPIC_VERSES.keys())
JOURNEY_TOPICS = list(TOPIC_JOURNEYS.keys())

EMERGENCY_FALLBACK = {
    "reference": "John 3:16",
    "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.",
    "translation_id": "KJV",
    "topic": "Love",
    "_is_fallback": True,
}

API_BASE = "https://bible-api.com"
TIMEOUT = 8


def _fetch(reference: str, translation: str = "kjv") -> dict:
    url = f"{API_BASE}/{reference.replace(' ', '%20')}?translation={translation}"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise ValueError(data["error"])
    return {
        "reference": data.get("reference", reference).strip(),
        "text": data.get("text", "").strip(),
        "translation_id": data.get("translation_id", translation).upper(),
    }


def fetch_verse(reference: str, translation: str = "kjv") -> dict:
    return _fetch(reference, translation)


def get_verse_for_topic(topic: str, translation: str = "kjv") -> dict:
    refs = TOPIC_VERSES.get(topic)
    if not refs:
        raise ValueError(f"Unknown topic: {topic}")
    weighted = refs[:2] * 2 + refs
    attempts = [random.choice(weighted)] + [r for r in refs]
    for ref in dict.fromkeys(attempts):   # deduplicate, preserve order
        try:
            result = _fetch(ref, translation)
            result["topic"] = topic
            return result
        except Exception:
            continue
    fb = dict(EMERGENCY_FALLBACK)
    fb["topic"] = topic
    return fb


def get_random_verse(translation: str = "kjv") -> Tuple[dict, str]:
    topic = random.choice(ALL_TOPICS)
    return get_verse_for_topic(topic, translation), topic


def get_daily_verse(translation: str = "kjv") -> Tuple[dict, str]:
    """
    Deterministic daily verse — same for everyone on the same calendar date.
    Uses date hash to pick topic + ref index, so it rotates predictably.
    """
    today = date.today().isoformat()
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)
    topic = ALL_TOPICS[seed % len(ALL_TOPICS)]
    refs = TOPIC_VERSES[topic]
    ref = refs[seed % len(refs)]
    try:
        result = _fetch(ref, translation)
        result["topic"] = topic
        return result, topic
    except Exception:
        fb = dict(EMERGENCY_FALLBACK)
        fb["topic"] = topic
        return fb, topic


def get_journey_verse(topic: str, day: int, translation: str = "kjv") -> dict:
    """Fetch the verse for a specific day of a topic journey."""
    plan = TOPIC_JOURNEYS.get(topic, [])
    entry = next((d for d in plan if d["day"] == day), None)
    if not entry:
        raise ValueError(f"No journey entry for {topic} day {day}")
    try:
        result = _fetch(entry["ref"], translation)
        result["topic"] = topic
        result["journey_theme"] = entry["theme"]
        result["journey_day"] = day
        return result
    except Exception:
        return {**EMERGENCY_FALLBACK, "topic": topic, "journey_theme": entry["theme"], "journey_day": day}


def get_all_topics() -> list[str]:
    return ALL_TOPICS


def validate_reference(reference: str) -> bool:
    """Quick validation — reject obviously malformed refs before hitting API."""
    if not reference or len(reference) < 3:
        return False
    has_book = any(c.isalpha() for c in reference)
    has_number = any(c.isdigit() for c in reference)
    return has_book and has_number
