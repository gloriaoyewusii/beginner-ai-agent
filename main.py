from fastapi import FastAPI, HTTPException
from datetime import datetime

from schemas.request_model import EchoIn, ChatIn, CurriculumRequest
from schemas.response_model import CurriculumResponse, DayPlan

from agent import build_curriculum_with_llm

app = FastAPI(title="Beginner Agent API")


@app.get("/")
def home():
    return {"status": "ok", "message": "API is running"}


@app.post("/echo")
def echo(req: EchoIn):
    return {"you_sent": req.text}


@app.post("/chat")
def chat(req: ChatIn):
    msg = req.message.strip().lower()

    if "time" in msg or "date" in msg:
        now = datetime.now().isoformat(timespec="seconds")
        return {"reply": f"The current server time is: {now}"}

    if msg.startswith("calc:"):
        expr = msg.replace("calc:", "").strip()
        allowed = set("0123456789+-*/(). ")
        if any(c not in allowed for c in expr):
            return {"reply": "I can only calculate numbers using + - * / ( ) ."}
        try:
            result = eval(expr, {"__builtins__": {}})
            return {"reply": f"Result: {result}"}
        except Exception:
            return {"reply": "I couldn't calculate that. Try: calc: (10 + 2) * 3"}

    return {"reply": "Try: 'what time is it?' or 'calc: 12/4'."}


@app.post("/curriculum", response_model=CurriculumResponse)
def curriculum(req: CurriculumRequest):
    if req.days is None:
        raise HTTPException(
            status_code=400,
            detail="How many days do you want the curriculum to be? e.g. 3, 5, 7, 14",
        )

    try:
        curriculum = build_curriculum_with_llm(req)
        return curriculum
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
