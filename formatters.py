"""
formatters.py

Formats devotional content for social media platforms and export.
Zero AI calls — pure string transformation logic.
"""

import csv
import io
import json
from datetime import datetime

# Platform character limits
INSTAGRAM_LIMIT = 2200
WHATSAPP_LIMIT = 700
TWITTER_LIMIT = 280


def _c(text: str) -> str:
    """Clean and normalize text."""
    return text.strip().replace("\n", " ")


def _build_hashtags(topic: str) -> str:
    base = ["#DailyDevotional", "#BibleVerse", "#ChurchLife", "#Faith", "#WordOfGod"]
    if topic and topic != "General":
        tag = f"#{topic.replace(' ', '')}"
        if tag not in base:
            base.insert(0, tag)
    return " ".join(base[:6])


# ---------------------------------------------------------------------------
# Platform formatters
# ---------------------------------------------------------------------------

def format_instagram(d: dict) -> str:
    ref = d["reference"]
    verse = _c(d["verse_text"])
    topic = d.get("topic", "")
    explanation = _c(d.get("explanation", ""))
    reflection = _c(d.get("reflection_question", ""))
    application = _c(d.get("application", ""))
    memory = _c(d.get("memory_summary", ""))
    prayer = _c(d.get("prayer_prompt", ""))

    lines = [
        f"📖 {ref}",
        f'"{verse}"',
        "",
        f"✨ {explanation}",
        "",
        f"🤔 Reflect: {reflection}",
        "",
        f"👣 Apply: {application}",
    ]
    if memory:
        lines += ["", f"💡 Remember: {memory}"]
    if prayer:
        lines += ["", f"🙏 {prayer}"]
    lines += ["", _build_hashtags(topic)]

    caption = "\n".join(lines)
    return caption[:INSTAGRAM_LIMIT]


def format_whatsapp(d: dict) -> str:
    ref = d["reference"]
    verse = _c(d["verse_text"])
    explanation = _c(d.get("explanation", ""))
    application = _c(d.get("application", ""))

    verse_short = verse if len(verse) <= 200 else verse[:197] + "..."

    lines = [
        f"📖 *{ref}*",
        f"_{verse_short}_",
        "",
        explanation,
        "",
        f"👉 {application}",
    ]
    return "\n".join(lines)[:WHATSAPP_LIMIT]


def format_twitter(d: dict) -> str:
    ref = d["reference"]
    topic = d.get("topic", "")
    tag = f"#{topic.replace(' ', '')}" if topic and topic != "General" else "#DailyDevotional"
    message = _c(d.get("memory_summary") or d.get("application") or d.get("explanation", ""))

    base = f"📖 {ref} | {message} {tag} #Bible"
    if len(base) <= TWITTER_LIMIT:
        return base

    overhead = len(f"📖 {ref} |  {tag} #Bible") + 4  # 4 = " ..." space
    return f"📖 {ref} | {message[:TWITTER_LIMIT - overhead]}... {tag} #Bible"


def format_full_text(d: dict) -> str:
    """Plain-text full devotional for download or display."""
    lines = [
        "=" * 40,
        f"Daily Devotional — {d.get('topic', 'General')}",
        f"Scripture: {d['reference']}",
        "=" * 40,
        "",
        f'"{d["verse_text"]}"',
        "",
        "── EXPLANATION ──",
        d.get("explanation", ""),
        "",
        "── REFLECTION ──",
        d.get("reflection_question", ""),
        "",
        "── APPLICATION ──",
        d.get("application", ""),
    ]
    if d.get("memory_summary"):
        lines += ["", "── MEMORY VERSE ──", d["memory_summary"]]
    if d.get("prayer_prompt"):
        lines += ["", "── PRAYER ──", d["prayer_prompt"]]
    lines += ["", f"Generated: {datetime.now().strftime('%B %d, %Y')}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV export helpers
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "date", "topic", "reference", "translation",
    "verse_text", "explanation", "reflection_question",
    "application", "memory_summary", "prayer_prompt",
]


def devotional_to_row(d: dict) -> dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": d.get("topic", ""),
        "reference": d.get("reference", ""),
        "translation": d.get("translation_id", "KJV"),
        "verse_text": d.get("verse_text", ""),
        "explanation": d.get("explanation", ""),
        "reflection_question": d.get("reflection_question", ""),
        "application": d.get("application", ""),
        "memory_summary": d.get("memory_summary", ""),
        "prayer_prompt": d.get("prayer_prompt", ""),
    }


def devotionals_to_csv(devotionals: list[dict]) -> str:
    if not devotionals:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for d in devotionals:
        writer.writerow(devotional_to_row(d))
    return buf.getvalue()
