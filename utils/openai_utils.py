"""Shared helpers for working with the OpenAI API."""

from functools import lru_cache
import os

from openai import OpenAI

from .logger import logger


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI | None:
    """Return a cached OpenAI client if an API key is available.

    Creating an ``OpenAI`` client triggers network lookups and environment
    validation.  The original implementation instantiated a new client on every
    call which could add noticeable latency when multiple helpers relied on this
    function.  The result is now cached so subsequent calls reuse the same
    client instance.
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; OpenAI features disabled")
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover - network failures
        logger.error("Failed to create OpenAI client: %s", exc)
        return None
