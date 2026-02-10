"""
LLM provider abstraction layer.
Supports Anthropic Claude, OpenAI, or "none" (offline-only mode).
"""

from typing import List, Dict, Optional
from ..config import settings

# Lazy-init clients to avoid import errors when keys aren't set
_anthropic_client = None
_openai_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def is_llm_available() -> bool:
    if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        return True
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return True
    return False


def chat_completion(
    system_prompt: str,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
) -> str:
    """
    Send a chat completion request to the configured LLM provider.

    messages: list of {"role": "user"|"assistant", "content": "..."}
    Returns: the assistant's response text.
    Raises: RuntimeError if no provider is configured.
    """
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS
    provider = settings.LLM_PROVIDER.lower()

    if provider == "anthropic":
        return _anthropic_chat(system_prompt, messages, max_tokens)
    elif provider == "openai":
        return _openai_chat(system_prompt, messages, max_tokens)
    else:
        raise RuntimeError("No LLM provider configured. Set LLM_PROVIDER in .env")


def _anthropic_chat(
    system_prompt: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
) -> str:
    client = _get_anthropic()
    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def _openai_chat(
    system_prompt: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
) -> str:
    client = _get_openai()
    oai_messages = [{"role": "system", "content": system_prompt}]
    oai_messages.extend(messages)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=oai_messages,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
