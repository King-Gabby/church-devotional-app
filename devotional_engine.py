"""
services/devotional_engine.py
All AI content generation — devotionals, sermons, prayers, study notes.
AI never generates Bible text. Verse text always comes from verse_service.
"""

import json
import re
from typing import Optional
from gemini_client import generate_with_gemini

PASTORAL_RULES = """
You are a pastoral assistant for a Christian church.
RULES (non-negotiable):
- NEVER invent, paraphrase, or modify Bible verses. Verses are given to you.
- Simple, warm, accessible language for all ages.
- No theological jargon. No repetition across sections.
- Tone: pastoral, encouraging, practically helpful — like a trusted elder.
- Family-safe. Non-political. Non-denominational.
- Return ONLY valid JSON. No markdown, no preamble.
"""


def _strip_json(raw: str) -> str:
    return re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.MULTILINE).strip()


def _parse(raw: str) -> Optional[dict]:
    try:
        return json.loads(_strip_json(raw))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# DEVOTIONAL
# ─────────────────────────────────────────────────────────────

def generate_devotional(
    verse_reference: str,
    verse_text: str,
    topic: Optional[str] = None,
    include_prayer: bool = True,
    include_memory: bool = True,
    journey_theme: Optional[str] = None,
) -> dict:
    topic_ctx = f"Theme: {topic}." if topic else ""
    journey_ctx = f"Journey focus: {journey_theme}." if journey_theme else ""

    prompt = f"""{PASTORAL_RULES}

{topic_ctx} {journey_ctx}

Bible Verse ({verse_reference}):
"{verse_text}"

Return JSON with EXACTLY these fields:
{{
  "explanation": "2-3 sentences explaining this verse for everyday life. Simple and warm.",
  "reflection_question": "One personal question connecting the verse to the reader's life.",
  "application": "One specific practical action the reader can take today.",
  "memory_summary": "One sentence of 12 words or fewer capturing the verse's core truth.",
  "prayer_prompt": "A short 2-3 sentence prayer the reader can pray right now."
}}
Return ONLY the JSON."""

    raw = generate_with_gemini(prompt)
    result = _parse(raw) or {
        "explanation": "This verse speaks to God's faithfulness and love in our everyday lives.",
        "reflection_question": "How does this verse speak to what you are carrying today?",
        "application": "Take 5 minutes today to quietly meditate on this verse.",
        "memory_summary": f"Remember the promise of {verse_reference} today.",
        "prayer_prompt": "Lord, let your Word take root in my heart and guide my steps. Amen.",
    }

    result.update({"reference": verse_reference, "verse_text": verse_text, "topic": topic or "General"})
    if not include_memory:
        result.pop("memory_summary", None)
    if not include_prayer:
        result.pop("prayer_prompt", None)
    return result


# ─────────────────────────────────────────────────────────────
# SERMON MODE
# ─────────────────────────────────────────────────────────────

def generate_sermon_outline(verse_reference: str, verse_text: str, audience: str = "congregation") -> dict:
    audience_ctx = {
        "congregation": "a Sunday morning congregation of adults and families",
        "youth": "a youth group of teenagers (13-18 years old) — use relatable, energetic language",
        "small_group": "a small Bible study group of 8-15 people — conversational and discussion-focused",
    }.get(audience, "a congregation")

    prompt = f"""{PASTORAL_RULES}

Bible Verse ({verse_reference}):
"{verse_text}"

Audience: {audience_ctx}

Generate a sermon outline JSON:
{{
  "title": "Engaging sermon title (creative but grounded)",
  "big_idea": "The one central truth of this message in 1 sentence.",
  "introduction": "2-3 sentence opening hook to draw the audience in.",
  "points": [
    {{"point": "Point 1 title", "explanation": "2-3 sentence explanation", "illustration": "Brief real-life illustration or analogy"}},
    {{"point": "Point 2 title", "explanation": "2-3 sentence explanation", "illustration": "Brief real-life illustration or analogy"}},
    {{"point": "Point 3 title", "explanation": "2-3 sentence explanation", "illustration": "Brief real-life illustration or analogy"}}
  ],
  "key_themes": ["theme1", "theme2", "theme3"],
  "conclusion": "2-3 sentence compelling close with a call to action.",
  "discussion_questions": [
    "Question 1 for post-sermon discussion",
    "Question 2",
    "Question 3"
  ],
  "prayer_close": "A short closing prayer for the sermon."
}}
Return ONLY the JSON."""

    raw = generate_with_gemini(prompt)
    result = _parse(raw) or {
        "title": f"A Message from {verse_reference}",
        "big_idea": "God's Word speaks directly to our lives today.",
        "introduction": "Every passage of Scripture has something to say to us, right now, in this season.",
        "points": [
            {"point": "What the Text Says", "explanation": verse_text[:100], "illustration": "Consider how this applies to daily life."},
        ],
        "key_themes": ["Faith", "Scripture", "Application"],
        "conclusion": "Let this Word go with you this week.",
        "discussion_questions": ["What stood out to you?", "How will you apply this?"],
        "prayer_close": "Lord, seal this Word in our hearts. Amen.",
    }
    result.update({"reference": verse_reference, "verse_text": verse_text, "audience": audience})
    return result


# ─────────────────────────────────────────────────────────────
# PRAYER GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_prayer(verse_reference: str, verse_text: str, prayer_type: str = "personal") -> dict:
    type_ctx = {
        "personal": "A personal, intimate prayer for one individual — first person singular (I, me, my).",
        "congregation": "A prayer for a congregation to pray together — first person plural (we, us, our). Suitable for Sunday service.",
        "intercessory": "An intercessory prayer on behalf of others — for families, the community, or a specific need.",
    }.get(prayer_type, "personal")

    prompt = f"""{PASTORAL_RULES}

Bible Verse ({verse_reference}):
"{verse_text}"

Prayer type: {type_ctx}

Generate a prayer JSON:
{{
  "title": "Short prayer title (e.g. 'A Prayer for Peace')",
  "opening": "1-sentence address to God",
  "body": "3-4 sentences of prayer body, directly inspired by the verse's themes. Warm and heartfelt.",
  "declaration": "1 sentence of faith declaration or scripture-based affirmation.",
  "closing": "1-sentence closing (e.g. 'In Jesus' name, Amen.')"
}}
Return ONLY the JSON."""

    raw = generate_with_gemini(prompt)
    result = _parse(raw) or {
        "title": f"Prayer from {verse_reference}",
        "opening": "Heavenly Father,",
        "body": "We come before You today anchored in Your Word. Let this scripture shape our hearts and guide our steps. We trust You with every part of our lives.",
        "declaration": "Your Word does not return void — it accomplishes all You intend.",
        "closing": "In Jesus' name, Amen.",
    }
    result.update({"reference": verse_reference, "verse_text": verse_text, "prayer_type": prayer_type})
    return result


# ─────────────────────────────────────────────────────────────
# BIBLE STUDY MODE
# ─────────────────────────────────────────────────────────────

def generate_study_notes(verse_reference: str, verse_text: str) -> dict:
    prompt = f"""{PASTORAL_RULES}

Bible Verse ({verse_reference}):
"{verse_text}"

Generate Bible study notes JSON:
{{
  "context": "2-3 sentences of historical/literary context for this passage.",
  "key_words": [
    {{"word": "word or phrase from verse", "meaning": "brief explanation of its significance"}}
  ],
  "cross_references": ["Book Chapter:Verse — why it connects"],
  "summary": "2-3 sentence plain-English summary of what this passage is saying.",
  "life_lessons": ["Lesson 1", "Lesson 2", "Lesson 3"],
  "discussion_prompts": [
    "Discussion prompt 1",
    "Discussion prompt 2",
    "Discussion prompt 3"
  ],
  "youth_angle": "1-2 sentences making this verse relatable for young people (teens/young adults)."
}}
Return ONLY the JSON."""

    raw = generate_with_gemini(prompt)
    result = _parse(raw) or {
        "context": "This passage comes from a rich section of Scripture with deep meaning.",
        "key_words": [{"word": verse_reference, "meaning": "A key passage worth studying deeply."}],
        "cross_references": [],
        "summary": verse_text[:200],
        "life_lessons": ["Trust in God's Word", "Apply Scripture daily"],
        "discussion_prompts": ["What does this mean to you?", "How would you live this out?"],
        "youth_angle": "This verse is just as relevant today as when it was written.",
    }
    result.update({"reference": verse_reference, "verse_text": verse_text})
    return result
