"""Interviewer LLM agent — simulates a technical interviewer."""

import json
from openai import OpenAI

import config
from models import Message
from prompts.interviewer_prompt import build_interviewer_prompt, INTERVIEWER_FIRST_MESSAGE


def _get_client() -> OpenAI:
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


def _build_openai_messages(
    system_prompt: str,
    conversation: list[Message],
    user_message: str | None = None,
) -> list[dict]:
    """Convert session conversation into OpenAI message format."""
    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    if user_message is not None:
        messages.append({"role": "user", "content": user_message})

    return messages


async def get_interviewer_reply(
    company: str,
    role: str,
    level: str,
    round_type: str,
    persona: str,
    duration_minutes: int,
    difficulty: str,
    question_topic_hint: str,
    coding_expectations: str,
    ai_policy: str,
    conversation: list[Message],
    user_message: str | None = None,
) -> dict:
    """
    Send conversation + new user message to the interviewer LLM.
    Returns {"reply": str, "phase": str}.
    """
    client = _get_client()

    system_prompt = build_interviewer_prompt(
        company=company,
        role=role,
        level=level,
        round_type=round_type,
        persona=persona,
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        question_topic_hint=question_topic_hint,
        coding_expectations=coding_expectations,
        ai_policy=ai_policy,
    )

    # If this is the very first message (no conversation yet), use the start prompt
    if not conversation and user_message is None:
        user_message = INTERVIEWER_FIRST_MESSAGE

    messages = _build_openai_messages(system_prompt, conversation, user_message)

    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    try:
        data = json.loads(raw)
        return {
            "reply": data.get("reply", raw),
            "phase": data.get("phase", "question"),
        }
    except json.JSONDecodeError:
        # Fallback: return the raw text as the reply
        return {"reply": raw, "phase": "question"}
