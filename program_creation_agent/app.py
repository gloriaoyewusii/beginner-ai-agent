from fastapi import FastAPI, HTTPException
from agent.schemas import ProgramRequest, ProgramResponse
from agent.generator import generate_program
from starlette.concurrency import run_in_threadpool

app = FastAPI(title="Program Builder Agent")

@app.post("/program", response_model=ProgramResponse)
async def build_program(req: ProgramRequest, model: str = "qwen2.5:3b"):
    try:
        return await run_in_threadpool(generate_program, req, model)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "program_generation_failed", "message": str(e)})
