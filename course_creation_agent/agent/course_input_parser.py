# agent/input_parser.py
"""
Course Input Parser (NL -> CourseDefinitionRequest)

Goal:
- Accept free-text like:
    "I want to learn how to write academic research articles"
- Extract:
    - course_title
    - complexity_level (beginner | intermediate | advanced)

Product policy:
- Only trust complexity_level if the user explicitly mentions:
  beginner / intermediate / advanced
- Otherwise default to beginner (ignore LLM guesses)

Design choices:
- Uses LangChain + ChatOllama (Ollama backend)
- Returns ONLY CourseDefinitionRequest
- Keeps cleanup lightweight and generic (not subject hardcoding)
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama

from .course_schemas import CourseDefinitionRequest, ComplexityLevel


# -----------------------------
# Intermediate parsed structure
# -----------------------------
class ParsedCourseInput(BaseModel):
    """
    Intermediate schema used only inside the parser.
    """
    course_title: str = Field(..., min_length=2, max_length=100)
    complexity_level: Optional[str] = Field(
        default=None,
        description="beginner | intermediate | advanced or null if missing",
    )


# -----------------------------
# Prompt for extraction
# -----------------------------
_PARSER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are CourseInputParser.

Your ONLY job is to extract structured fields from a user's free-text request.

Rules:
- Output MUST follow the provided JSON schema exactly.
- Do NOT generate course content.
- Do NOT add extra keys.
- complexity_level must be exactly one of:
  - beginner
  - intermediate
  - advanced
- If complexity_level is not explicitly stated in the user text, set it to null.
- course_title MUST be a clean, concise title (2–10 words).
- course_title MUST be normal text with spaces (not camelCase).
- course_title MUST be Title Case.
- course_title MUST NOT end with the word "Course".
- Remove filler phrases like:
  "I want", "I would like", "teach me", "learn", "create", "build", "generate", "a course", "program", "on", "on how to", "how to".
""".strip(),
        ),
        (
            "human",
            """
{format_instructions}

User text:
{text}
""".strip(),
        ),
    ]
)


# -----------------------------
# LLM factory
# -----------------------------
def _make_llm(model: str) -> ChatOllama:
    return ChatOllama(model=model, temperature=0)


# -----------------------------
# Helpers (lightweight cleanup)
# -----------------------------
_CAMEL_SPLIT_RE = re.compile(r"([a-z])([A-Z])")
_WS_RE = re.compile(r"\s+")


def _cleanup_title(title: str) -> str:
    t = (title or "").strip()

    # Split camelCase/glued words -> add spaces
    t = _CAMEL_SPLIT_RE.sub(r"\1 \2", t)

    # Remove trailing "course" if model included it
    t = re.sub(r"\bcourse\b\s*$", "", t, flags=re.IGNORECASE).strip()

    # Collapse repeated spaces
    t = _WS_RE.sub(" ", t).strip()

    # Basic Title Case (keeps it simple; avoids heavy NLP)
    # Note: .title() can be imperfect for acronyms, but acceptable for prototype.
    t = t.title()

    return t


_LEVEL_WORD_RE = re.compile(r"\b(beginner|intermediate|advanced)\b", re.IGNORECASE)


# -----------------------------
# Public API
# -----------------------------
def parse_user_text_to_course_request(
    text: str,
    model: str = "qwen2.5:3b",
    max_retries: int = 2,
) -> CourseDefinitionRequest:
    """
    Convert free text -> CourseDefinitionRequest.

    Behavior:
    - If user does NOT explicitly mention a level word:
        default beginner (ignore LLM guess)
    - If user explicitly mentions a level word:
        validate and use it (fallback to beginner if invalid)
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Input text is empty.")

    llm = _make_llm(model)
    parser = PydanticOutputParser(pydantic_object=ParsedCourseInput)
    format_instructions = parser.get_format_instructions()

    chain = _PARSER_PROMPT | llm | parser

    last_error: Optional[Exception] = None
    repair_note = ""

    for attempt in range(max_retries + 1):
        try:
            effective_text = text if attempt == 0 else f"{text}\n\nREPAIR NOTE: {repair_note}"

            parsed: ParsedCourseInput = chain.invoke(
                {"text": effective_text, "format_instructions": format_instructions}
            )

            # Enforce product policy: only trust level if explicitly present in user text
            explicit_level = _LEVEL_WORD_RE.search(text)

            if not explicit_level:
                level = ComplexityLevel.beginner
            else:
                if parsed.complexity_level is None:
                    level = ComplexityLevel.beginner
                else:
                    level_str = parsed.complexity_level.strip().lower()
                    try:
                        level = ComplexityLevel(level_str)
                    except Exception:
                        level = ComplexityLevel.beginner

            course_title = _cleanup_title(parsed.course_title)

            return CourseDefinitionRequest(
                course_title=course_title,
                complexity_level=level,
            )

        except (ValidationError, ValueError) as e:
            last_error = e
            repair_note = (
                f"Previous output failed: {str(e)}. "
                "Return ONLY valid JSON matching the schema."
            )

    raise ValueError(f"Input parsing failed after {max_retries + 1} attempts: {last_error}")
