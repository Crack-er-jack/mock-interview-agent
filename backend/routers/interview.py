"""Interview routes — chat messages and evaluation."""

from fastapi import APIRouter, HTTPException

from models import (
    InterviewPhase,
    Message,
    MessageRequest,
    MessageResponse,
    EvaluateRequest,
    EvaluateResponse,
)
from state import get_session, save_session
from agents.interviewer import get_interviewer_reply
from agents.evaluator import evaluate_interview

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.post("/message", response_model=MessageResponse)
async def send_message(req: MessageRequest):
    """Send a user message and get the interviewer's reply."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.phase == InterviewPhase.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview is already completed")

    # Append user message to conversation
    session.conversation.append(Message(role="user", content=req.message))

    # Get interviewer reply
    try:
        plan = session.plan
        result = await get_interviewer_reply(
            company=session.config.company,
            role=session.config.role.value,
            level=session.config.level.value,
            round_type=session.config.round_type.value,
            persona=plan.persona,
            duration_minutes=plan.duration_minutes,
            difficulty=plan.difficulty,
            question_topic_hint=plan.question_topic_hint,
            coding_expectations=plan.coding_expectations,
            ai_policy=plan.ai_policy,
            conversation=session.conversation,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interviewer error: {e}")

    # Append assistant reply
    session.conversation.append(Message(role="assistant", content=result["reply"]))
    session.phase = InterviewPhase(result.get("phase", session.phase.value))

    save_session(session)

    return MessageResponse(reply=result["reply"], phase=result["phase"])


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest):
    """Trigger end-of-interview evaluation and return scorecard."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.phase = InterviewPhase.EVALUATING
    save_session(session)

    try:
        scorecard = await evaluate_interview(
            company=session.config.company,
            role=session.config.role.value,
            level=session.config.level.value,
            round_type=session.config.round_type.value,
            conversation=session.conversation,
            code_submissions=session.code_submissions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation error: {e}")

    session.scorecard = scorecard
    session.phase = InterviewPhase.COMPLETED
    save_session(session)

    return EvaluateResponse(scorecard=scorecard)
