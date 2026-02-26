from fastapi import FastAPI, HTTPException, Body
from starlette.concurrency import run_in_threadpool

# --- Program agent imports ---
from program_creation_agent.agent.schemas import ProgramRequest, ProgramResponse
from program_creation_agent.agent.generator import generate_program
from program_creation_agent.agent.input_parser import parse_user_text_to_request

# --- Course agent imports ---
from course_creation_agent.agent.course_schemas import (
    CourseDefinitionRequest,
    CourseDefinitionResponse,
)
from course_creation_agent.agent.course_generator import generate_course
from course_creation_agent.agent.input_parser import parse_user_text_to_course_request


app = FastAPI(title="Orchestrator API")


# -----------------------------
# Program endpoints
# -----------------------------
@app.post("/program", response_model=ProgramResponse)
async def build_program(req: ProgramRequest, model: str = "qwen2.5:3b"):
    try:
        return await run_in_threadpool(generate_program, req, model)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "program_generation_failed", "message": str(e)})


@app.post("/program-from-text", response_model=ProgramResponse)
async def build_program_from_text(
    text: str = Body(..., embed=True),
    model: str = "qwen2.5:3b",
):
    try:
        req = await run_in_threadpool(parse_user_text_to_request, text, model)
        return await run_in_threadpool(generate_program, req, model)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "program_generation_failed", "message": str(e)})


# -----------------------------
# Course endpoints
# -----------------------------
@app.post("/course", response_model=CourseDefinitionResponse)
async def build_course(req: CourseDefinitionRequest, model: str = "qwen2.5:3b"):
    try:
        return await run_in_threadpool(generate_course, req, model)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "course_generation_failed", "message": str(e)})


@app.post("/course-from-text", response_model=CourseDefinitionResponse)
async def build_course_from_text(
    text: str = Body(..., embed=True),
    model: str = "qwen2.5:3b",
):
    try:
        req = await run_in_threadpool(parse_user_text_to_course_request, text, model)
        return await run_in_threadpool(generate_course, req, model)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "course_generation_failed", "message": str(e)})


# -----------------------------
# Linking endpoint (Program → Course)
# -----------------------------
@app.post("/course-from-program", response_model=CourseDefinitionResponse)
async def build_course_from_program(
    program: ProgramResponse,
    model: str = "qwen2.5:3b",
):
    """
    Simple linking strategy:
    - Create a text prompt from program output
    - Use course-from-text parser+generator pipeline
    """
    try:
        prompt = (
            "Create a course definition that aligns with this program:\n\n"
            f"Program description: {program.program_description}\n\n"
            f"Learning outcomes: {program.learning_outcomes}\n\n"
            "Choose an appropriate course title and default to beginner if not stated."
        )

        req = await run_in_threadpool(parse_user_text_to_course_request, prompt, model)
        return await run_in_threadpool(generate_course, req, model)

    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "course_generation_failed", "message": str(e)})
