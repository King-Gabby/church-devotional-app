"""
services/devotional_engine.py

Generates devotional content from a verified Bible verse using Gemini.
AI is ONLY used for: explanation, reflection question, application, prayer.
AI NEVER generates or modifies Bible text.
"""

import json
import re
from typing import Optional

from gemini_client import generate_with_gemini

# ---------------------------------------------------------------------------
# Prompt template — controls tone, structure, and safety contract
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATE = """
You are a pastoral assistant for a Christian church congregation.
Your job is to generate short, encouraging devotional content based on a Bible verse that is provided to you.

STRICT RULES:
- You MUST NOT invent, paraphrase, or modify any Bible verse. The verse is given to you.
- Use simple, warm, accessible language suitable for all ages.
- Avoid theological jargon.
- Each section must be distinct — no repetition across explanation, reflection, and application.
- Tone: pastoral, encouraging, practically helpful. Like a trusted elder speaking.
- Keep it family-safe and non-political.
- Respond ONLY with a valid JSON object. No markdown fences, no extra text.

Bible Verse ({reference}):
"{verse_text}"

{topic_line}

Generate a JSON object with EXACTLY these fields:
{{
  "explanation": "2–3 sentences explaining this verse in everyday life. Simple and warm.",
  "reflection_question": "One personal question that helps the reader connect this verse to their life.",
  "application": "One specific, practical action the reader can take today inspired by this verse.",
  "memory_summary": "One memorable sentence of 12 words or fewer capturing the verse's core truth.",
  "prayer_prompt": "A short 2–3 sentence prayer the reader can pray right now based on this verse."
}}

Return ONLY the JSON object. Nothing else.
"""


def _parse_json_safe(raw: str) -> Optional[dict]:
    """Strip markdown fences and parse JSON safely."""
    cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _fallback_devotional(reference: str, verse_text: str) -> dict:
    """Safe defaults when Gemini fails or returns unparseable output."""
    return {
        "explanation": "This verse reminds us of God's faithfulness and love for us each day.",
        "reflection_question": "How does this verse speak to what you are facing today?",
        "application": "Take a moment to quietly meditate on this verse and let it guide your next step.",
        "memory_summary": f"Hold onto the promise of {reference} today.",
        "prayer_prompt": "Lord, let your Word take root in my heart and guide my steps. Amen.",
    }


def generate_devotional(
    verse_reference: str,
    verse_text: str,
    topic: Optional[str] = None,
    include_prayer: bool = True,
    include_memory_summary: bool = True,
) -> dict:
    """
    Generate a complete devotional from a verified Bible verse.

    Args:
        verse_reference: e.g. "Philippians 4:6-7"
        verse_text: The actual scripture text (always from API, never AI-generated)
        topic: Optional theme context (Faith, Anxiety, etc.)
        include_prayer: Whether to include prayer_prompt in output
        include_memory_summary: Whether to include memory_summary in output

    Returns:
        dict with keys: explanation, reflection_question, application,
                        memory_summary (opt), prayer_prompt (opt),
                        reference, verse_text, topic
    """
    topic_line = f"Theme of this devotional: {topic}." if topic else ""

    prompt = _PROMPT_TEMPLATE.format(
        reference=verse_reference,
        verse_text=verse_text,
        topic_line=topic_line,
    )

    try:
        raw = generate_with_gemini(prompt)
        result = _parse_json_safe(raw)
        if not result:
            # Gemini returned text but not valid JSON — use fallback
            result = _fallback_devotional(verse_reference, verse_text)
    except Exception:
        result = _fallback_devotional(verse_reference, verse_text)

    # Attach source metadata — never from AI
    result["reference"] = verse_reference
    result["verse_text"] = verse_text
    result["topic"] = topic or "General"

    if not include_memory_summary:
        result.pop("memory_summary", None)
    if not include_prayer:
        result.pop("prayer_prompt", None)

    return result
