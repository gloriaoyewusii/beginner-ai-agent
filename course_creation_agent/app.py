from fastapi import FastAPI, HTTPException, Body
from starlette.concurrency import run_in_threadpool

from agent.course_schemas import CourseDefinitionRequest, CourseDefinitionResponse
from agent.course_generator import generate_course
from agent.course_input_parser import parse_user_text_to_course_request


app = FastAPI(title="Course Builder Agent")


@app.post("/course", response_model=CourseDefinitionResponse)
async def build_course(req: CourseDefinitionRequest, model: str = "qwen2.5:3b"):
    try:
        return await run_in_threadpool(generate_course, req, model)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "course_generation_failed", "message": str(e)},
        )


@app.post("/course-from-text", response_model=CourseDefinitionResponse)
async def build_course_from_text(
    text: str = Body(..., embed=True),
    model: str = "qwen2.5:3b",
):
    try:
        req = await run_in_threadpool(parse_user_text_to_course_request, text, model)
        return await run_in_threadpool(generate_course, req, model)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "course_generation_failed", "message": str(e)},
        )
