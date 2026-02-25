from langchain_core.prompts import ChatPromptTemplate

COURSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "{course_soul}"),
        (
            "human",
            """
Allowed career pathways (choose 1 to 5 ONLY from this list; exact match):
{career_pathways}

User request:
- course_title: {course_title}
- complexity_level: {complexity_level}

{repair_instruction}

Rules you MUST follow:
1) Output ONLY valid JSON that matches the schema exactly. No extra keys.
2) career_pathway must be a JSON array of 1 to 5 strings, each an EXACT match from the allowed list.
2b) Prefer 1–2 highly relevant pathways; include more only if clearly justified.
2c) Use "Others" only if no specific pathway fits.
3) Keep content relevant to "{course_title}" at "{complexity_level}" (no unrelated topics).
4) End immediately after the JSON.
5) course_title must be normal text with spaces (not camelCase) and MUST NOT end with the word "course".
""".strip(),
        ),
    ]
)
