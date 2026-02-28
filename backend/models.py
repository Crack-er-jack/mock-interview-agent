"""Pydantic models for requests, responses, and session state."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────

class Role(str, Enum):
    SDE = "SDE"
    DATA_ANALYST = "Data Analyst"


class Level(str, Enum):
    INTERN = "Intern"
    SDE1 = "SDE1"
    SDE2 = "SDE2"


class RoundType(str, Enum):
    DSA = "DSA"
    SQL = "SQL"
    ML = "ML"
    SYSTEM_DESIGN = "System Design"


class InterviewPhase(str, Enum):
    PLANNING = "planning"
    QUESTION = "question"
    CLARIFICATION = "clarification"
    COMPLEXITY = "complexity"
    EDGE_CASES = "edge_cases"
    CODING = "coding"
    EVALUATING = "evaluating"
    COMPLETED = "completed"


# ── Core domain models ──────────────────────────────────────

class InterviewConfig(BaseModel):
    company: str = Field(..., min_length=1, max_length=100)
    role: Role
    level: Level
    round_type: RoundType


class InterviewPlan(BaseModel):
    duration_minutes: int
    difficulty: str
    persona: str
    coding_expectations: str
    ai_policy: str
    question_topic_hint: str


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CodeRun(BaseModel):
    code: str
    stdout: str = ""
    stderr: str = ""
    passed: int = 0
    failed: int = 0
    total: int = 0
    timed_out: bool = False


class ScoreCategory(BaseModel):
    score: int = Field(..., ge=1, le=5)
    max: int = 5
    feedback: str


class Scorecard(BaseModel):
    overall: str  # "Strong Hire" / "Hire" / "Lean Hire" / "No Hire"
    scores: dict[str, ScoreCategory]
    total: int
    max_total: int = 25
    summary: str


class SessionState(BaseModel):
    session_id: str
    config: InterviewConfig
    plan: Optional[InterviewPlan] = None
    conversation: list[Message] = Field(default_factory=list)
    code_submissions: list[CodeRun] = Field(default_factory=list)
    phase: InterviewPhase = InterviewPhase.PLANNING
    scorecard: Optional[Scorecard] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Request / Response schemas ───────────────────────────────

class StartSessionRequest(BaseModel):
    company: str = Field(..., min_length=1)
    role: Role
    level: Level
    round_type: RoundType


class StartSessionResponse(BaseModel):
    session_id: str
    plan: InterviewPlan


class MessageRequest(BaseModel):
    session_id: str
    message: str


class MessageResponse(BaseModel):
    reply: str
    phase: str


class CodeExecuteRequest(BaseModel):
    session_id: str
    code: str


class CodeExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    passed: int
    failed: int
    total: int
    timed_out: bool


class EvaluateRequest(BaseModel):
    session_id: str


class EvaluateResponse(BaseModel):
    scorecard: Scorecard
