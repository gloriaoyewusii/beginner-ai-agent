import json
from typing import Optional

from schemas.request_model import CurriculumRequest
from schemas.response_model import CurriculumResponse, DayPlan
from llm import generate_text


SYSTEM_RULES = """
You are a curriculum-building assistant.
You MUST follow the user's topic, level, and days exactly.
You MUST output ONLY valid JSON that matches this schema:

{
  "topic": string,
  "days": integer,
  "level": string,
  "plan": [
    {
      "day": integer,
      "title": string,
      "goals": [string, ...],
      "exercises": [string, ...]
    },
    ...
  ]
}

Rules:
- plan length MUST equal "days"
- day numbers must start at 1 and increase by 1
- do NOT include any extra keys outside the schema
- do NOT include markdown, code fences, or explanations. JSON ONLY.
"""


def _extract_json(text: str) -> str:
    """
    Models sometimes add extra text. We'll extract the first {...} block.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return ""
    return text[start : end + 1]


def _fallback_rule_based(req: CurriculumRequest) -> CurriculumResponse:
    # Your old logic (safe fallback)
    plan = []
    for d in range(1, req.days + 1):
        plan.append(
            DayPlan(
                day=d,
                title=f"Day {d}: Intro to {req.topic.strip()}",
                goals=[
                    f"Understand key basics of {req.topic.strip()}",
                    f"Learn core concepts for day {d}",
                ],
                exercises=[
                    f"Write short notes on what you learned about {req.topic.strip()}",
                    f"Do a small practice task related to {req.topic.strip()}",
                ],
            )
        )

    return CurriculumResponse(
        topic=req.topic.strip(),
        days=req.days,
        level=req.level,
        plan=plan,
    )


def build_curriculum_with_llm(req: CurriculumRequest, max_retries: int = 2) -> CurriculumResponse:
    """
    Agent behavior:
    - if days missing -> raise (caller decides to ask user)
    - ask LLM for strict JSON
    - parse JSON
    - validate with Pydantic (CurriculumResponse)
    - ensure plan length matches days, and topic/level match request
    - retry if invalid
    - fallback if still failing
    """
    if req.days is None:
        raise ValueError("days is required to build a curriculum")

    user_prompt = f"""
User request:
- topic: {req.topic}
- days: {req.days}
- level: {req.level}
- constraints: {req.constraints}

Now produce the JSON curriculum.
"""

    last_error: Optional[str] = None

    for attempt in range(max_retries + 1):
        raw = generate_text(SYSTEM_RULES + "\n" + user_prompt, max_new_tokens=700)
        json_str = _extract_json(raw)

        try:
            data = json.loads(json_str)
            # Validate shape/types
            curriculum = CurriculumResponse.model_validate(data)

            # Extra deterministic checks (trust your code, not the model)
            if curriculum.days != req.days:
                raise ValueError("days mismatch")
            if curriculum.topic.strip().lower() != req.topic.strip().lower():
                raise ValueError("topic mismatch")
            if curriculum.level.strip().lower() != req.level.strip().lower():
                raise ValueError("level mismatch")
            if len(curriculum.plan) != req.days:
                raise ValueError("plan length mismatch")

            # Ensure day numbers are 1..days
            expected_days = list(range(1, req.days + 1))
            got_days = [dp.day for dp in curriculum.plan]
            if got_days != expected_days:
                raise ValueError("day numbers must be 1..days in order")

            return curriculum

        except Exception as e:
            last_error = str(e)

            # On retry, we can nudge the model with the error
            user_prompt += f"\nIMPORTANT: Your last output failed validation because: {last_error}. Fix it and output JSON only.\n"
            continue

    # If we get here, LLM failed multiple times → fallback
    return _fallback_rule_based(req)
