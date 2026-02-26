import re
from typing import List, Set

from pydantic import ValidationError

from .course_schemas import CourseDefinitionRequest, CourseDefinitionResponse

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
    return {t for t in s.split() if len(t) >= 3}


def validate_response_json(data: dict) -> CourseDefinitionResponse:
    """Ensure response matches CourseDefinitionResponse schema."""
    try:
        return CourseDefinitionResponse.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}") from e


def validate_no_placeholders(obj: CourseDefinitionResponse) -> None:
    combined = " ".join(
        [obj.course_title, obj.course_description, obj.learners_description]
        + obj.learning_objectives
        + obj.prerequisites
        + obj.career_pathway
    )
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, combined, flags=re.IGNORECASE):
            raise ValueError(f"Placeholder text detected (pattern: {pat}).")


def validate_no_duplicates(obj: CourseDefinitionResponse) -> None:
    def check_list(name: str, items: list[str]) -> None:
        normed = [_normalize(x) for x in items]
        if len(normed) != len(set(normed)):
            raise ValueError(f"Duplicates detected in '{name}'.")

    check_list("learning_objectives", obj.learning_objectives)
    check_list("prerequisites", obj.prerequisites)
    check_list("career_pathway", obj.career_pathway)


def validate_career_pathway_membership(obj: CourseDefinitionResponse) -> None:
    invalid = [p for p in obj.career_pathway if p not in ALLOWED_SET]
    if invalid:
        raise ValueError(
            "career_pathway contains invalid value(s): "
            + ", ".join(invalid)
            + ". Must match the allowed list exactly."
        )


def validate_others_not_with_specific(obj: CourseDefinitionResponse) -> None:
    """
    Product rule to reduce pathway spam:
    - If "Others" is selected, it must be the only pathway.
    """
    if "Others" in obj.career_pathway and len(obj.career_pathway) > 1:
        raise ValueError("career_pathway must not include 'Others' alongside specific pathways.")


def validate_title_format(obj: CourseDefinitionResponse) -> None:
    """
    Soft contract checks that are important for your UX:
    - Title should not end with 'course'
    - Avoid camelCase/glued titles like WriteAcademicResearchArticles
    """
    title = obj.course_title.strip()

    if title.lower().endswith(" course"):
        raise ValueError("course_title must NOT end with the word 'course'.")

    # If it has no spaces but has multiple capitals, it's likely camelCase/glued
    if " " not in title and re.search(r"[A-Z].*[A-Z]", title):
        raise ValueError("course_title looks like camelCase/glued words; must be normal text with spaces.")


def validate_relevance(req: CourseDefinitionRequest, obj: CourseDefinitionResponse) -> None:
    """
    Generic drift guard:
    - course_description should mention the complexity level
    - course_description should overlap with course_title tokens (at least 1 meaningful token)
    """
    desc = _normalize(obj.course_description)
    level = req.complexity_level.value.lower()

    if level not in desc:
        raise ValueError("Relevance check failed: course_description must mention complexity_level.")

    title_tokens = _tokenize(req.course_title)
    desc_tokens = _tokenize(obj.course_description)

    if title_tokens and len(title_tokens.intersection(desc_tokens)) < 1:
        raise ValueError("Relevance check failed: course_description must reference course_title.")


def run_validations(req: CourseDefinitionRequest, obj: CourseDefinitionResponse) -> None:
    validate_no_placeholders(obj)
    validate_no_duplicates(obj)
    validate_title_format(obj)
    validate_career_pathway_membership(obj)
    validate_others_not_with_specific(obj)
    validate_relevance(req, obj)
