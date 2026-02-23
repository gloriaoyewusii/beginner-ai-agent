import json
from pathlib import Path
from typing import Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

# Keep your existing import if you want; warning is okay.
#from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama


from .schemas import ProgramRequest, ProgramResponse
from .prompts import PROGRAM_PROMPT
from .validators import ALLOWED_PATHWAYS, validate_response_json, run_validations

SOUL_PATH = Path(__file__).resolve().parent / "soul.md"


def load_soul() -> str:
    return SOUL_PATH.read_text(encoding="utf-8")


def make_llm(model: str) -> ChatOllama:
    return ChatOllama(model=model, temperature=0)


def generate_program(req: ProgramRequest, model: str = "qwen2.5:3b", max_retries: int = 2) -> ProgramResponse:
    soul = load_soul()
    llm = make_llm(model)
    parser = JsonOutputParser()

    pathways_text = json.dumps(ALLOWED_PATHWAYS, ensure_ascii=False)

    chain = (
        RunnablePassthrough.assign(
            soul=lambda _: soul,
            career_pathways=lambda _: pathways_text,
        )
        | PROGRAM_PROMPT
        | llm
        | parser
    )

    last_error: Optional[Exception] = None
    repair_instruction = ""  # empty for attempt 1

    for _attempt in range(max_retries + 1):
        try:
            payload = {
                **req.model_dump(),
                "repair_instruction": repair_instruction,
            }

            data = chain.invoke(payload)

            obj = validate_response_json(data)
            run_validations(req, obj)

            return obj

        except Exception as e:
            last_error = e
            repair_instruction = (
                "IMPORTANT: Your previous output failed validation.\n"
                f"Validation error: {str(e)}\n"
                "Fix the JSON to satisfy the error. Keep the same schema. "
                "Return ONLY corrected JSON. Do not add extra keys."
            )

    raise ValueError(f"Generation failed after {max_retries + 1} attempts: {last_error}")
