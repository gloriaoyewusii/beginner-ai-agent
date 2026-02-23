from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ProgramRequest(BaseModel):
    program_name: str = Field(..., min_length=2, max_length=120)
    complexity_level: ComplexityLevel


class ProgramResponse(BaseModel):
    program_description: str = Field(..., min_length=20, max_length=900)
    learning_outcomes: List[str] = Field(..., min_length=3, max_length=12)
    learning_objectives: List[str] = Field(..., min_length=3, max_length=16)
    prerequisites: List[str] = Field(default_factory=list, max_length=10)

    # Product rule: user can select up to 5; agent should also output up to 5
    career_pathway: List[str] = Field(..., min_length=1, max_length=5)
