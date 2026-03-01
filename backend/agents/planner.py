"""Planner LLM agent — generates an interview plan from user config."""

import json
from openai import OpenAI

import config
from models import InterviewPlan
from prompts.planner_prompt import build_planner_prompt
from .react_agent import run_react_agent


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

    # --- EDUCATIONAL COMMENT ---
    # Instead of letting the LLM hallucinate a problem in one shot, we delegate this
    # very specific task (finding a problem) to our mini autonomous ReAct agent.
    # We give it a goal, let it loop, and wait for its Final Answer.
    goal = f"Find a {level.lower()} difficulty problem suitable for a {role} at {company}. Use your tool to search the database."
    print("\n" + "*"*60)
    print("🚀 DELEGATING TO REACT AGENT TO RESEARCH A PROBLEM ")
    print("*"*60 + "\n")
    
    try:
        problem_hint = run_react_agent(goal)
    except Exception as e:
        print(f"ReAct Agent Failed. Using fallback. Error: {e}")
        problem_hint = "Make up a coding problem."

    system_prompt = build_planner_prompt(company, role, level, round_type)
    
    # We now inject the ReAct agent's finding back into the Planner's prompt
    system_prompt += f"\n\n[Agent Research Results]\nYou MUST format your plan to include this specific coding problem:\n{problem_hint}"

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
