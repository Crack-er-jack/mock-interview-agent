"""Session routes — create and retrieve interview sessions."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from models import (
    InterviewConfig,
    InterviewPhase,
    Message,
    SessionState,
    StartSessionRequest,
    StartSessionResponse,
)
from state import save_session, get_session
from agents.planner import generate_plan
from agents.interviewer import get_interviewer_reply

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest):
    """Create a new interview session, generate a plan, get first question."""
    # Generate interview plan
    try:
        plan = await generate_plan(
            company=req.company,
            role=req.role.value,
            level=req.level.value,
            round_type=req.round_type.value,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {e}")

    # Create session
    session_id = str(uuid.uuid4())
    config = InterviewConfig(
        company=req.company,
        role=req.role,
        level=req.level,
        round_type=req.round_type,
    )

    session = SessionState(
        session_id=session_id,
        config=config,
        plan=plan,
        phase=InterviewPhase.QUESTION,
        created_at=datetime.utcnow(),
    )

    # Get the interviewer's first message (question)
    try:
        result = await get_interviewer_reply(
            company=req.company,
            role=req.role.value,
            level=req.level.value,
            round_type=req.round_type.value,
            persona=plan.persona,
            duration_minutes=plan.duration_minutes,
            difficulty=plan.difficulty,
            question_topic_hint=plan.question_topic_hint,
            coding_expectations=plan.coding_expectations,
            ai_policy=plan.ai_policy,
            conversation=[],
            user_message=None,
        )
        # Add the interviewer's first message to the conversation
        session.conversation.append(
            Message(role="assistant", content=result["reply"])
        )
        session.phase = InterviewPhase(result.get("phase", "question"))
    except Exception as e:
        # Even if the first message fails, still return the session with the plan
        session.conversation.append(
            Message(
                role="assistant",
                content="Hello! I'll be your interviewer today. Let me prepare your question...",
            )
        )

    save_session(session)

    return StartSessionResponse(session_id=session_id, plan=plan)


@router.get("/{session_id}")
async def get_session_state(session_id: str):
    """Retrieve full session state."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
