"""
services/verse_service.py

Bible verse retrieval — API, topic maps, manual input.
This module NEVER calls any AI API. Verse text is always from an external source.
"""

import random
import requests
from typing import Tuple, Optional

# ---------------------------------------------------------------------------
# Topic → reference map  (extend freely — these are verified real refs)
# Weighted: first 2 entries per topic get 2× probability
# ---------------------------------------------------------------------------
TOPIC_VERSES: dict[str, list[str]] = {
    "Faith": [
        "Hebrews 11:1", "Romans 10:17", "Matthew 17:20",
        "2 Corinthians 5:7", "James 2:17", "Mark 11:22",
    ],
    "Anxiety": [
        "Philippians 4:6-7", "1 Peter 5:7", "Matthew 6:34",
        "Isaiah 41:10", "Psalm 94:19", "John 14:27",
    ],
    "Purpose": [
        "Jeremiah 29:11", "Ephesians 2:10", "Romans 8:28",
        "Proverbs 19:21", "Psalm 138:8", "Isaiah 43:7",
    ],
    "Strength": [
        "Isaiah 40:31", "Philippians 4:13", "Psalm 46:1",
        "2 Corinthians 12:9", "Nehemiah 8:10", "Deuteronomy 31:6",
    ],
    "Hope": [
        "Romans 15:13", "Lamentations 3:22-23", "Jeremiah 29:11",
        "Psalm 31:24", "Romans 8:24-25", "Isaiah 40:31",
    ],
    "Love": [
        "1 Corinthians 13:4-7", "John 3:16", "Romans 8:38-39",
        "1 John 4:8", "John 15:13", "Ephesians 3:17-19",
    ],
    "Wisdom": [
        "Proverbs 3:5-6", "James 1:5", "Proverbs 2:6",
        "Colossians 2:3", "Psalm 111:10", "Ecclesiastes 8:1",
    ],
    "Forgiveness": [
        "Ephesians 4:32", "Colossians 3:13", "1 John 1:9",
        "Matthew 6:14-15", "Psalm 103:12", "Micah 7:18",
    ],
    "Gratitude": [
        "1 Thessalonians 5:18", "Psalm 107:1", "Colossians 3:17",
        "Psalm 100:4", "Hebrews 13:15", "Philippians 4:6",
    ],
    "Peace": [
        "John 14:27", "Isaiah 26:3", "Philippians 4:7",
        "Romans 5:1", "Colossians 3:15", "Numbers 6:26",
    ],
    "Courage": [
        "Joshua 1:9", "Psalm 27:1", "Isaiah 41:13",
        "2 Timothy 1:7", "Deuteronomy 31:6", "1 Corinthians 16:13",
    ],
    "Healing": [
        "Jeremiah 17:14", "Psalm 103:2-3", "James 5:15",
        "Isaiah 53:5", "Psalm 147:3", "Exodus 15:26",
    ],
}

ALL_TOPICS = list(TOPIC_VERSES.keys())

# Hardcoded emergency fallback — only used when API is completely unreachable
EMERGENCY_FALLBACK: dict = {
    "reference": "John 3:16",
    "text": (
        "For God so loved the world, that he gave his only begotten Son, "
        "that whosoever believeth in him should not perish, but have everlasting life."
    ),
    "translation_id": "KJV",
    "topic": "Love",
    "_is_fallback": True,
}

BIBLE_API_BASE = "https://bible-api.com"
REQUEST_TIMEOUT = 8  # seconds


def _fetch_from_api(reference: str, translation: str = "kjv") -> dict:
    """
    Raw fetch from bible-api.com.
    Raises requests.RequestException or ValueError on failure.
    """
    ref_encoded = reference.replace(" ", "%20")
    url = f"{BIBLE_API_BASE}/{ref_encoded}?translation={translation}"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise ValueError(f"bible-api.com error: {data['error']}")
    return {
        "reference": data.get("reference", reference).strip(),
        "text": data.get("text", "").strip(),
        "translation_id": data.get("translation_id", translation).upper(),
    }


def fetch_verse(reference: str, translation: str = "kjv") -> dict:
    """
    Public method: fetch a specific verse reference.
    Returns {reference, text, translation_id}.
    Raises on failure — caller handles fallback.
    """
    return _fetch_from_api(reference, translation)


def get_verse_for_topic(topic: str, translation: str = "kjv") -> dict:
    """
    Fetch a verse for a given topic.
    Uses weighted random (first 2 refs = 2× probability).
    Tries alternates on failure before returning emergency fallback.
    """
    refs = TOPIC_VERSES.get(topic)
    if not refs:
        raise ValueError(f"Unknown topic: '{topic}'. Available: {ALL_TOPICS}")

    weighted = refs[:2] * 2 + refs
    primary = random.choice(weighted)
    attempts = [primary] + [r for r in refs if r != primary]

    for ref in attempts:
        try:
            result = _fetch_from_api(ref, translation)
            result["topic"] = topic
            return result
        except Exception:
            continue

    # All attempts failed — use emergency fallback
    fallback = dict(EMERGENCY_FALLBACK)
    fallback["topic"] = topic
    return fallback


def get_random_verse(translation: str = "kjv") -> Tuple[dict, str]:
    """
    Pick a random topic and fetch a verse from it.
    Returns (verse_dict, topic_name).
    """
    topic = random.choice(ALL_TOPICS)
    verse = get_verse_for_topic(topic, translation)
    return verse, topic


def get_all_topics() -> list[str]:
    return ALL_TOPICS
