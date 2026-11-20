"""Ask router — questions answered from the stored reviews, with citations."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.deps import known_competitor
from modules.ask import ask

router = APIRouter(tags=["ask"])


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    competitor: str | None = None
    history: list[Turn] = Field(default_factory=list, max_length=12)


@router.post("/ask")
def ask_question(body: AskRequest):
    name = known_competitor(body.competitor) if body.competitor else None
    return ask(body.question.strip(), name, [t.model_dump() for t in body.history])
