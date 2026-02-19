
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Beginner Agent API")

# ---------- Data shape (what we expect the user to send) ----------
class EchoIn(BaseModel):
    text: str

class ChatIn(BaseModel):
    message: str


# ---------- 1) Health check ----------
@app.get("/")
def home():
    return {"status": "ok", "message": "API is running"}


# ---------- 2) Echo endpoint ----------
@app.post("/echo")
def echo(req: EchoIn):
    return {"you_sent": req.text}


# ---------- 3) Fake agent endpoint (still NO AI) ----------
@app.post("/chat")
def chat(req: ChatIn):
    msg = req.message.strip().lower()

    # "Tool" example: time tool (real data)
    if "time" in msg or "date" in msg:
        now = datetime.now().isoformat(timespec="seconds")
        return {"reply": f"The current server time is: {now}"}

    # "Tool" example: a tiny calculator (very limited on purpose)
    if msg.startswith("calc:"):
        expr = msg.replace("calc:", "").strip()
        allowed = set("0123456789+-*/(). ")
        if any(c not in allowed for c in expr):
            return {"reply": "I can only calculate numbers using + - * / ( ) ."}
        try:
            result = eval(expr, {"__builtins__": {}})
            return {"reply": f"Result: {result}"}
        except Exception:
            return {"reply": "I couldn't calculate that. Try something like: calc: (10 + 2) * 3"}

    # Default fallback (no AI)
    return {"reply": "I’m a beginner fake-agent 🙂 Try: 'what time is it?' or 'calc: 12/4'."}
