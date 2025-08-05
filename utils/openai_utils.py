"""Shared helpers for working with the OpenAI API."""

import os
from openai import OpenAI


def get_openai_client() -> OpenAI | None:
    """Return an OpenAI client if an API key is available."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None
