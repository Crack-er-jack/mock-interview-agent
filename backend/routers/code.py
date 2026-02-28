"""Code execution routes — run user code in the sandbox."""

from fastapi import APIRouter, HTTPException

from models import (
    CodeExecuteRequest,
    CodeExecuteResponse,
    CodeRun,
    InterviewPhase,
)
from state import get_session, save_session
from sandbox.executor import execute_code

router = APIRouter(prefix="/api/code", tags=["code"])


@router.post("/execute", response_model=CodeExecuteResponse)
async def run_code(req: CodeExecuteRequest):
    """Execute user code in the sandbox and return results."""
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.phase == InterviewPhase.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview is already completed")

    # Execute code (no hidden tests for MVP — user just runs their own code)
    result = execute_code(code=req.code, test_cases=None)

    # Log the submission
    code_run = CodeRun(
        code=req.code,
        stdout=result["stdout"],
        stderr=result["stderr"],
        passed=result["passed"],
        failed=result["failed"],
        total=result["total"],
        timed_out=result["timed_out"],
    )
    session.code_submissions.append(code_run)

    # Update phase to coding if not already
    if session.phase not in (InterviewPhase.CODING, InterviewPhase.EVALUATING, InterviewPhase.COMPLETED):
        session.phase = InterviewPhase.CODING

    save_session(session)

    return CodeExecuteResponse(**result)
