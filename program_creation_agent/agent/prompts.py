from langchain_core.prompts import ChatPromptTemplate

PROGRAM_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "{soul}"),
        (
            "human",
            """
Allowed career pathways (choose 1 to 5 ONLY from this list; exact match):
{career_pathways}

User request:
- program_name: {program_name}
- complexity_level: {complexity_level}

{repair_instruction}

Rules you MUST follow:
1) Output ONLY valid JSON that matches the schema exactly. No extra keys.
2) career_pathway must be a JSON array of 1 to 5 strings, each an EXACT match from the allowed list.
3) Keep content relevant to "{program_name}" at "{complexity_level}" (no unrelated topics).
4) End immediately after the JSON.
""".strip(),
        ),
    ]
)
