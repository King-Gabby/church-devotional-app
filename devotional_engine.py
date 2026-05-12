"""
services/devotional_engine.py
AI content generation — devotional, sermon, prayer, study.
Canonical schema: all verse dicts use key "text".
AI never generates or modifies scripture — only interprets provided text.

Error contract:
  - Quota exhausted → returns dict with _quota_error: True (graceful fallback shown in UI)
  - Parse failure   → returns dict with safe fallback content
  - Never raises to the UI layer
"""
import json
import re
from typing import Optional

from gemini_client import generate_with_gemini, QUOTA_EXCEEDED


# ── Shared voice ──────────────────────────────────────────────
_VOICE = """You are a contemplative pastoral voice writing for a church devotional platform.
Tone: calm, clear, unhurried. A trusted elder — not a motivational speaker.
Language: modern English. Accessible. No King James syntax.
Rules:
- NEVER invent, recall, or rewrite Bible verses. They are always provided.
- No clichés: no "God is good", "blessed beyond measure", generic affirmations.
- Each section must say something distinct. No repetition.
- No filler. Every sentence earns its place.
- Family-safe. Non-denominational. Non-political.
- Return ONLY valid JSON. No markdown fences, no preamble, no extra text."""


def _parse(raw: str) -> Optional[dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
        # Unwrap single-key wrapper if Gemini added one
        if isinstance(parsed, dict) and len(parsed) == 1:
            inner = next(iter(parsed.values()))
            if isinstance(inner, dict):
                return inner
        return parsed
    except Exception:
        return None


def _s(d: dict, key: str, fallback: str = "") -> str:
    return str(d.get(key) or fallback).strip()


def _quota_fallback(reference: str, verse_text: str, topic: Optional[str]) -> dict:
    """Graceful fallback devotional when Gemini quota is exceeded."""
    return {
        "reference":   reference,
        "text":        verse_text,
        "topic":       topic or "General",
        "explanation": (
            f"Take a moment today to sit quietly with {reference}. "
            "Let the words settle rather than reaching immediately for their meaning. "
            "Sometimes the most honest response to Scripture is simply to let it be present."
        ),
        "reflection": "What does this verse stir in you today — not what it means, but what it makes you feel?",
        "application": "Read this verse once more slowly, and carry one word from it with you through the day.",
        "memory":      f"One word from {reference} — let it follow you today.",
        "prayer": (
            "Lord, I'm here with Your Word even when I don't have words of my own. "
            "Let that be enough today. Amen."
        ),
        "_quota_error": True,
    }


# ─────────────────────────────────────────────────────────────
# DEVOTIONAL
# ─────────────────────────────────────────────────────────────

def generate_devotional(
    reference: str,
    verse_text: str,
    topic: Optional[str] = None,
    journey_theme: Optional[str] = None,
    include_prayer: bool = True,
    include_memory: bool = True,
) -> dict:
    lens = " ".join(filter(None, [
        f"Today's theme is '{journey_theme}'." if journey_theme else "",
        f"The reader is exploring {topic}." if (topic and not journey_theme) else "",
    ]))

    prompt = f"""{_VOICE}

{lens}

The reader is sitting with this verse today:
{reference} — "{verse_text}"

Write a devotional that invites stillness, not just action.
The explanation should unpack what is happening in the text — not restate it.
The reflection must be specific enough that it can be answered honestly.
The application should be a real, achievable action — not vague platitudes.
The prayer should sound like something a real person prays alone, not a public liturgy.

Return exactly this JSON:
{{
  "explanation": "2-3 sentences. Unpack the verse's central image in plain language. Do not restate the verse.",
  "reflection": "One personal question. Specific. Surfaces something honest.",
  "application": "One concrete action. Something doable today.",
  "memory": "10-12 words. The verse's core truth made memorable.",
  "prayer": "2-3 sentences. First person. Honest before reverent."
}}"""

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return _quota_fallback(reference, verse_text, topic)

    parsed = _parse(raw) or {}

    result = {
        "reference":   reference,
        "text":        verse_text,
        "topic":       topic or "General",
        "explanation": _s(parsed, "explanation", f"This passage from {reference} holds a truth worth sitting with today."),
        "reflection":  _s(parsed, "reflection", "Where in your life does this verse find the most resistance?"),
        "application": _s(parsed, "application", "Write one word from this verse somewhere you'll see it today."),
        "memory":      _s(parsed, "memory", f"The promise of {reference} is alive today."),
        "prayer":      _s(parsed, "prayer", f"Lord, let {reference} do its work in me today. Amen."),
    }

    if not include_memory:
        result.pop("memory", None)
    if not include_prayer:
        result.pop("prayer", None)

    return result


# ─────────────────────────────────────────────────────────────
# SERMON
# ─────────────────────────────────────────────────────────────

_AUD = {
    "congregation": "Mixed Sunday congregation — veterans and first-timers. Speak to both.",
    "youth":        "Teenagers and young adults (14–24). Skeptical of performance, hungry for truth. Direct.",
    "small_group":  "6–15 adults meeting mid-week. Conversational. Leave space for questions.",
}


def generate_sermon(reference: str, verse_text: str, audience: str = "congregation") -> dict:
    prompt = f"""{_VOICE}

Audience: {_AUD.get(audience, _AUD['congregation'])}
Scripture: {reference} — "{verse_text}"

Each point must build on the last — not repeat it with different words.
Title should be honest, not clever. Big idea: one sentence a child could understand.
Illustrations from recognizable everyday life.

Return exactly this JSON:
{{
  "title": "Honest sermon title",
  "big_idea": "The whole message in one sentence.",
  "introduction": "2-3 sentences opening a question or tension the audience already lives with.",
  "points": [
    {{"point": "Short declarative title", "explanation": "2-3 sentences from the text.", "illustration": "1-2 sentences — concrete real-life analogy."}},
    {{"point": "Short declarative title", "explanation": "2-3 sentences.", "illustration": "1-2 sentences."}},
    {{"point": "Short declarative title", "explanation": "2-3 sentences.", "illustration": "1-2 sentences."}}
  ],
  "conclusion": "2-3 sentences. One thing to walk out with.",
  "discussion_questions": [
    "A question creating genuine conversation.",
    "A question connecting to personal experience.",
    "A question about concrete response this week."
  ],
  "closing_prayer": "2-3 sentences. Honest and direct."
}}"""

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return {
            "title": f"A Word from {reference}",
            "big_idea": "God meets us where we actually are.",
            "introduction": "Most of us arrived here carrying something. This text has something to say about that.",
            "points": [
                {"point": "What the text says", "explanation": verse_text[:140], "illustration": "Think of a time one sentence changed how you saw an entire situation."},
                {"point": "What it means now", "explanation": "The original hearers faced something specific. The human need is the same.", "illustration": "The distance between their world and ours is smaller than it looks."},
                {"point": "What we do with it", "explanation": "Faith without response stays inside the building. This passage asks for something.", "illustration": "A decision deferred is still a decision."},
            ],
            "conclusion": "You don't have to resolve everything today. But you do have to take one step.",
            "discussion_questions": ["What in this passage surprised you?", "Where do you see yourself in this text?", "What will you change this week?"],
            "closing_prayer": "Lord, do with this what only You can. Amen.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text, "audience": audience})
    return parsed


# ─────────────────────────────────────────────────────────────
# PRAYER
# ─────────────────────────────────────────────────────────────

_PRAYER_CTX = {
    "personal":     "First person singular (I, me, my). Honest. Praying alone.",
    "congregation": "First person plural (we, us, our). Suitable to read aloud on Sunday.",
    "intercessory": "Praying on behalf of others — families, communities, people in pain.",
}


def generate_prayer(reference: str, verse_text: str, prayer_type: str = "personal") -> dict:
    prompt = f"""{_VOICE}

Prayer voice: {_PRAYER_CTX.get(prayer_type, _PRAYER_CTX['personal'])}
Scripture: {reference} — "{verse_text}"

Write a prayer flowing directly from this specific verse — not a generic prayer with a reference added.
The body should name something real from human experience that connects to this text.
Avoid repeated phrases, religious performance, template language.

Return exactly this JSON:
{{
  "title": "Short honest title (e.g. 'When Everything Feels Uncertain')",
  "opening": "One sentence addressing God. Find the right name for this moment.",
  "body": "3-4 sentences arising from this verse. Name real feelings. Honest before reverent.",
  "declaration": "One sentence of faith anchored in what this verse promises.",
  "closing": "One sentence. Simple and true."
}}"""

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return {
            "title": f"Praying Through {reference}",
            "opening": "Lord —",
            "body": (
                "I'm bringing this verse and my honest self before You. "
                "Not the version of me that has it together — the one who needs what this text promises. "
                "Meet me in the gap between what I know and what I'm living."
            ),
            "declaration": f"What You promised in {reference} is still true today.",
            "closing": "In Jesus' name. Amen.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text, "prayer_type": prayer_type})
    return parsed


# ─────────────────────────────────────────────────────────────
# BIBLE STUDY
# ─────────────────────────────────────────────────────────────

def generate_study(reference: str, verse_text: str) -> dict:
    prompt = f"""{_VOICE}

Scripture: {reference} — "{verse_text}"

Notes that respect the reader's intelligence. Context only if it genuinely changes how the verse lands.
Discussion prompts that create genuine conversation — not Sunday school answers.
Youth angle: name a specific real situation, don't just assert relevance.

Return exactly this JSON:
{{
  "context": "2-3 sentences. Only background that changes how the verse is heard.",
  "summary": "2-3 sentences. Plain English. No jargon.",
  "key_words": [
    {{"word": "A significant word or phrase", "meaning": "What it meant originally and why it still matters."}}
  ],
  "life_lessons": [
    "A lesson requiring something from the reader.",
    "A lesson about a specific relationship or situation.",
    "A lesson challenging a common assumption."
  ],
  "discussion_prompts": [
    "A question surfacing tension or honest doubt.",
    "A question connecting to personal experience.",
    "A question about faithful response this week."
  ],
  "youth_angle": "1-2 sentences. A specific situation — school, friendship, identity — where this verse becomes concrete."
}}"""

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return {
            "context": f"{reference} was written to people navigating real uncertainty — the human need is the same.",
            "summary": verse_text[:200],
            "key_words": [{"word": "the passage", "meaning": "Read it slowly a second time. The first read rarely catches everything."}],
            "life_lessons": [
                "What we believe about God shows up in how we treat ordinary moments.",
                "Scripture was written for communities, not private consumption.",
                "Faithful response usually requires something small and specific.",
            ],
            "discussion_prompts": [
                "What do you find hardest to believe about what this verse claims?",
                "When have you experienced something close to what this text describes?",
                "What would living this verse look like in one relationship this week?",
            ],
            "youth_angle": "If you're under pressure to perform or fit in, this verse speaks to the question of what you're actually worth — and who gets to decide.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text})
    return parsed