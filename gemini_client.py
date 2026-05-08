"""
services/gemini_client.py

Single-responsibility Gemini API client.
All Gemini interaction flows through here — swap model or SDK version in one place.
"""

import os
import time
import streamlit as st
from typing import Optional

# Support both python-dotenv and Streamlit secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_api_key() -> str:
    """Resolve API key from Streamlit secrets or environment."""
    # Streamlit Cloud secrets take priority
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, AttributeError, FileNotFoundError):
        pass
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Add it to .env or Streamlit secrets."
        )
    return key


def _get_client():
    """Build and cache the Gemini client (cached per Streamlit session)."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai not installed. Run: pip install google-generativeai"
        )
    genai.configure(api_key=_get_api_key())
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "max_output_tokens": 1024,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    )


def generate_with_gemini(
    prompt: str,
    retries: int = 2,
    timeout_seconds: int = 30,
) -> str:
    """
    Send a prompt to Gemini 1.5 Flash and return the text response.

    Args:
        prompt: The full prompt string.
        retries: Number of retry attempts on transient failure.
        timeout_seconds: Not directly supported by SDK, used for retry backoff context.

    Returns:
        Clean string response from the model.

    Raises:
        RuntimeError: If all retries fail.
    """
    model = _get_client()
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = model.generate_content(prompt)

            # Extract text safely
            if response.parts:
                return response.text.strip()

            # Blocked or empty response
            finish = getattr(response.candidates[0], "finish_reason", None) if response.candidates else None
            if finish and str(finish) != "STOP":
                raise RuntimeError(f"Gemini response blocked or incomplete (finish_reason={finish})")

            return response.text.strip()

        except Exception as e:
            last_error = e
            if attempt < retries:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s
                time.sleep(wait)
            continue

    raise RuntimeError(f"Gemini API failed after {retries + 1} attempts: {last_error}")
