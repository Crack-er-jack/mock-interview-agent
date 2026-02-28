"""Evaluator LLM agent — scores interview performance."""

import json
from openai import OpenAI

import config
from models import Message, CodeRun, Scorecard, ScoreCategory
from prompts.evaluator_prompt import build_evaluator_prompt


def _get_client() -> OpenAI:
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


def _format_transcript(conversation: list[Message]) -> str:
    """Convert conversation list into a readable transcript string."""
    lines = []
    for msg in conversation:
        label = "Interviewer" if msg.role == "assistant" else "Candidate"
        lines.append(f"[{label}]: {msg.content}")
    return "\n".join(lines)


def _format_code_results(submissions: list[CodeRun]) -> str:
    """Format code execution results into a readable string."""
    if not submissions:
        return "No code was submitted."

    parts = []
    for i, run in enumerate(submissions, 1):
        parts.append(
            f"── Submission {i} ──\n"
            f"Code:\n{run.code}\n"
            f"Stdout: {run.stdout}\n"
            f"Stderr: {run.stderr}\n"
            f"Tests passed: {run.passed}/{run.total} | Timed out: {run.timed_out}"
        )
    return "\n\n".join(parts)


async def evaluate_interview(
    company: str,
    role: str,
    level: str,
    round_type: str,
    conversation: list[Message],
    code_submissions: list[CodeRun],
) -> Scorecard:
    """Run the evaluator LLM and return a structured Scorecard."""
    client = _get_client()

    transcript = _format_transcript(conversation)
    code_results = _format_code_results(code_submissions)

    system_prompt = build_evaluator_prompt(
        company=company,
        role=role,
        level=level,
        round_type=round_type,
        transcript=transcript,
        code_results=code_results,
    )

    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Evaluate this interview now."},
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Try to extract JSON using regex in case there's preamble/postamble text
    import re
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        raw_json = json_match.group(0)
    else:
        raw_json = raw

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        # Fallback scorecard if LLM failed to return valid JSON
        print(f"Failed to parse Evaluator JSON: {raw}")
        return Scorecard(
            overall="Evaluation Failed",
            scores={
                "error": ScoreCategory(
                    score=1, max=5, feedback="The AI evaluator failed to return a valid JSON response."
                )
            },
            total=0,
            max_total=25,
            summary=f"Parsing error: {str(e)}",
        )

    # Parse scores
    scores = {}
    for key, val in data.get("scores", {}).items():
        scores[key] = ScoreCategory(
            score=val["score"],
            max=val.get("max", 5),
            feedback=val["feedback"],
        )

    return Scorecard(
        overall=data.get("overall", "No Hire"),
        scores=scores,
        total=data.get("total", sum(s.score for s in scores.values())),
        max_total=data.get("max_total", 25),
        summary=data.get("summary", ""),
    )
