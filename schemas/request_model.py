from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class EchoIn(BaseModel):
    text: str

class ChatIn(BaseModel):
    message: str

class CurriculumRequest(BaseModel):
    topic: str = Field(..., examples=["Java"])
    days: Optional[int] = Field(default=None, ge=1, le=14, examples=[3])
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    constraints: Optional[List[str]] = None
