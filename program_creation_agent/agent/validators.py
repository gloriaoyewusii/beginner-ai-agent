import re
from typing import List, Set

from pydantic import ValidationError

from .schemas import ProgramRequest, ProgramResponse

# ✅ Allowed pathway list (EXACT strings must match)
ALLOWED_PATHWAYS: List[str] = [
    "Software Development & Engineering",
    "Data & AI",
    "Cloud & Infrastructure",
    "Product & Design",
    "Emerging Technologies",
    "Business & Management",
    "Finance & Economics",
    "Marketing & Communications",
    "Human Resources & People Development",
    "Creative & Media",
    "Health & Wellness",
    "Education & Training",
    "Legacy, Policy & Social Services",
    "Entrepreneurship & Innovation",
    "Agriculture, Environment & Food Sciences",
    "Food, Nutrition & Hospitality",
    "Research & Science",
    "Arts, Culture & Creative Industries",
    "Fashion, Beauty, & Personal Care",
    "Travel, Tourism & Leisure",
    "Others",
]

ALLOWED_SET: Set[str] = set(ALLOWED_PATHWAYS)

# Optional: prevents obviously unfinished outputs
PLACEHOLDER_PATTERNS = (
    r"\bTBD\b",
    r"\bTODO\b",
    r"\bN/A\b",
    r"\blorem\b",
    r"\bipsum\b",
)

WS_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^\w\s&,-]")


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = WS_RE.sub(" ", s)
    return s


def _tokenize(s: str) -> set[str]:
    s = _normalize(s)
    s = NON_WORD_RE.sub(" ", s)
    # tokens length >= 3 reduces false matches
    return {t for t in s.split() if len(t) >= 3}


def validate_response_json(data: dict) -> ProgramResponse:
    """Universal: ensure response matches ProgramResponse schema."""
    try:
        return ProgramResponse.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}") from e


def validate_no_placeholders(obj: ProgramResponse) -> None:
    combined = " ".join(
        [obj.program_description]
        + obj.learning_outcomes
        + obj.learning_objectives
        + obj.prerequisites
        + obj.career_pathway
    )
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, combined, flags=re.IGNORECASE):
            raise ValueError(f"Placeholder text detected (pattern: {pat}).")


def validate_no_duplicates(obj: ProgramResponse) -> None:
    def check_list(name: str, items: list[str]) -> None:
        normed = [_normalize(x) for x in items]
        if len(normed) != len(set(normed)):
            raise ValueError(f"Duplicates detected in '{name}'.")

    check_list("learning_outcomes", obj.learning_outcomes)
    check_list("learning_objectives", obj.learning_objectives)
    check_list("prerequisites", obj.prerequisites)
    check_list("career_pathway", obj.career_pathway)


def validate_career_pathway_membership(obj: ProgramResponse) -> None:
    invalid = [p for p in obj.career_pathway if p not in ALLOWED_SET]
    if invalid:
        raise ValueError(
            "career_pathway contains invalid value(s): "
            + ", ".join(invalid)
            + ". Must match the allowed list exactly."
        )


def validate_relevance(req: ProgramRequest, obj: ProgramResponse) -> None:
    """
    Generic drift guard (no hardcoded subjects):
    - description must mention level
    - description must share at least 1 meaningful token with program_name
    """
    desc = _normalize(obj.program_description)
    level = req.complexity_level.value.lower()

    if level not in desc:
        raise ValueError("Relevance check failed: program_description must mention complexity_level.")

    pn_tokens = _tokenize(req.program_name)
    desc_tokens = _tokenize(obj.program_description)

    if pn_tokens and len(pn_tokens.intersection(desc_tokens)) < 1:
        raise ValueError("Relevance check failed: program_description must reference program_name.")


def run_validations(req: ProgramRequest, obj: ProgramResponse) -> None:
    validate_no_placeholders(obj)
    validate_no_duplicates(obj)
    validate_career_pathway_membership(obj)
    validate_relevance(req, obj)
