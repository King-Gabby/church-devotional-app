"""
utils/storage.py

Lightweight CSV-based persistence for devotional history and topic analytics.
Interface is intentionally thin — swap to SQLite/Postgres by reimplementing these functions.
"""

import csv
import os
from collections import Counter
from datetime import datetime
from formatters import CSV_FIELDS, devotional_to_row

HISTORY_FILE = "devotional_history.csv"


def _ensure_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def save_devotional(d: dict):
    _ensure_file()
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(devotional_to_row(d))


def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_topic_analytics() -> dict:
    history = load_history()
    counts = Counter(r.get("topic", "Unknown") for r in history if r.get("topic"))
    return dict(counts.most_common())


def get_history_csv_bytes() -> bytes:
    if not os.path.exists(HISTORY_FILE):
        return b""
    with open(HISTORY_FILE, "rb") as f:
        return f.read()


def clear_history():
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()
