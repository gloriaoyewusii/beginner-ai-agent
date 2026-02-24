# agent/input_parser.py
"""
Input Parser (NL -> ProgramRequest)

Goal:
- Accept a free-text sentence like:
    "create an intro to data science program for beginners"
- Extract:
    - program_name
    - complexity_level (beginner | intermediate | advanced)

This is a small interpreter layer that runs BEFORE the ProgramBuilder agent.
It converts messy human input into clean, structured input.

Design choices:
- Uses LangChain + ChatOllama (Ollama backend)
- Returns ONLY ProgramRequest
- Defaults complexity_level to 'beginner' if missing
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import ChatOllama

from .schemas import ProgramRequest, ComplexityLevel


# -----------------------------
# Intermediate parsed structure
# -----------------------------
class ParsedInput(BaseModel):
    """
    Intermediate schema used only inside the parser.
    """
    program_name: str = Field(..., min_length=2, max_length=120)
    complexity_level: Optional[str] = Field(
        default=None,
        description="beginner | intermediate | advanced or null if missing"
    )


# -----------------------------
# Prompt for extraction
# -----------------------------
_PARSER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are InputParser.

Your ONLY job is to extract structured fields from a user's free-text request.

Rules:
- Output MUST follow the provided JSON schema exactly.
- Do NOT generate a program.
- Do NOT add extra keys.
- complexity_level must be exactly one of:
  - beginner
  - intermediate
  - advanced
- If complexity_level is not explicitly stated, set it to null.
- program_name MUST be a clean, concise title (2–8 words).
- Remove filler phrases like:
  "I want", "create", "build", "generate", "program", "on", "on how to".
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
    # temperature=0 keeps extraction consistent and deterministic
    return ChatOllama(model=model, temperature=0)


# -----------------------------
# Public API
# -----------------------------
def parse_user_text_to_request(
    text: str,
    model: str = "qwen2.5:3b",
    max_retries: int = 2,
) -> ProgramRequest:
    """
    Convert free text -> ProgramRequest.

    Behavior:
    - Defaults complexity_level to 'beginner' if missing
    - Retries if parsing fails
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Input text is empty.")

    llm = _make_llm(model)

    parser = PydanticOutputParser(pydantic_object=ParsedInput)
    format_instructions = parser.get_format_instructions()

    chain = _PARSER_PROMPT | llm | parser

    last_error: Optional[Exception] = None
    repair_note = ""

    for attempt in range(max_retries + 1):
        try:
            effective_text = text if attempt == 0 else f"{text}\n\nREPAIR NOTE: {repair_note}"

            parsed: ParsedInput = chain.invoke(
                {
                    "text": effective_text,
                    "format_instructions": format_instructions,
                }
            )

            # -----------------------------
            # Normalize complexity level
            # -----------------------------
            if parsed.complexity_level is None:
                level = ComplexityLevel.beginner
            else:
                level_str = parsed.complexity_level.strip().lower()
                try:
                    level = ComplexityLevel(level_str)
                except Exception:
                    raise ValueError(
                        f"Invalid complexity_level '{parsed.complexity_level}'. "
                        "Must be exactly: beginner | intermediate | advanced."
                    )

            # -----------------------------
            # Build final request
            # -----------------------------
            return ProgramRequest(
                program_name=parsed.program_name.strip(),
                complexity_level=level,
            )

        except (ValidationError, ValueError) as e:
            last_error = e
            repair_note = (
                f"Previous output failed: {str(e)}. "
                "Return ONLY valid JSON matching the schema."
            )

    raise ValueError(
        f"Input parsing failed after {max_retries + 1} attempts: {last_error}"
    )
