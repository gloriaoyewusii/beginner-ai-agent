from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class DayPlan(BaseModel):
    day: int
    title: str
    goals: List[str]
    exercises: List[str]

class CurriculumResponse(BaseModel):
    topic: str
    days: int
    level: str
    plan: List[DayPlan]
