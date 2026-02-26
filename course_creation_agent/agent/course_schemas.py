from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class CourseDefinitionRequest(BaseModel):
    course_title: str = Field(..., min_length=2, max_length=100)
    complexity_level: ComplexityLevel


class CourseDefinitionResponse(BaseModel):
    course_title: str = Field(..., min_length=2, max_length=100)
    course_description: str = Field(..., min_length=20, max_length=2500)
   # learning_outcomes: List[str] = Field(..., min_length=3, max_length=12)
    learning_objectives: List[str] = Field(..., min_length=3, max_length=16)
    prerequisites: List[str] = Field(default_factory=list, max_length=10)
    learners_description: str = Field(..., min_length=20, max_length=2500)
    career_pathway: List[str] = Field(..., min_length=1, max_length=1)
