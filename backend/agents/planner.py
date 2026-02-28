"""Planner LLM agent — generates an interview plan from user config."""

import json
from openai import OpenAI

import config
from models import InterviewPlan
from prompts.planner_prompt import build_planner_prompt


def _get_client() -> OpenAI:
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


async def generate_plan(
    company: str,
    role: str,
    level: str,
    round_type: str,
) -> InterviewPlan:
    """Call the LLM to produce a structured interview plan."""
    if config.QUICK_TEST_MODE:
        return InterviewPlan(
            duration_minutes=1,
            difficulty="Easy",
            persona="Straightforward",
            coding_expectations="Provide a working Python function",
            ai_policy="No external tools",
            question_topic_hint=(
                "Ask the candidate to write a Python function `def has_permutation_substring(s1, s2):` "
                "that returns True if any permutation of s1 is a substring of s2."
            ),
        )

    client = _get_client()

    system_prompt = build_planner_prompt(company, role, level, round_type)

    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the interview plan now."},
        ],
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines)

    data = json.loads(raw)
    return InterviewPlan(**data)
