import os, json, sqlite3, time, uuid
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
BASE_URL = os.getenv("LLM_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "")
DB = "data/calls.db"
REC_DIR = Path("data/recordings")
REC_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ["Converted", "Interested", "Follow-up Required", "Not Interested", "Demo Requested", "No Response"]

SYSTEM_PROMPT = """You are Riya, a friendly sales agent on a phone call for FlowDesk, a fictional helpdesk SaaS for small support teams.
FlowDesk (demo product, details are fictional): shared inbox for email and chat, ticket assignment, automation rules, reports, 14-day free trial, plans from 20 USD per agent per month.
Rules:
- This is a spoken call. Reply in 1 to 3 short sentences. No lists, no emojis, no markdown.
- Reply in the language the customer uses (English, Hindi or Telugu).
- Ask one question at a time to learn their team size, current tool and pain points.
- Answer objections politely. Never invent features, prices or discounts beyond those above; if unsure, offer a demo or follow-up.
- Aim to get a clear next step: sign up for the trial, book a demo, or a follow-up call.
- Never summarize the call yourself. If asked for a summary, say it will appear on screen after the call ends and continue the conversation.
- If the customer wants to end the call, thank them and say goodbye."""

app = FastAPI()

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

with db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS calls (
        id TEXT PRIMARY KEY, started_at TEXT, ended_at TEXT, duration INTEGER,
        consent INTEGER, transcript TEXT, summary TEXT, requirements TEXT,
        objections TEXT, next_steps TEXT, status TEXT, recording TEXT)""")

class Msg(BaseModel):
    role: str
    content: str

class StartIn(BaseModel):
    consent: bool

class ChatIn(BaseModel):
    messages: list[Msg]

class EndIn(BaseModel):
    transcript: list[Msg]
    duration: int = 0

async def llm(messages, max_tokens=300):
    if not (BASE_URL and API_KEY and MODEL):
        raise HTTPException(500, "LLM is not configured in .env")
    body = {"model": MODEL, "messages": messages, "temperature": 0.6, "max_tokens": max_tokens}
    effort = os.getenv("LLM_REASONING", "")
    if effort:
        body["reasoning_effort"] = effort
    last = ""
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post(BASE_URL + "/chat/completions", headers={"Authorization": "Bearer " + API_KEY}, json=body)
        if r.status_code == 200:
            return (r.json()["choices"][0]["message"].get("content") or "").strip()
        last = f"LLM error {r.status_code}: {r.text[:300]}"
        if r.status_code == 400 and "tool" in r.text.lower() and attempt < 2:
            continue
        break
    raise HTTPException(502, last)
@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": bool(BASE_URL and API_KEY and MODEL)}

@app.post("/api/calls")
def start_call(body: StartIn):
    cid = uuid.uuid4().hex[:12]
    with db() as con:
        con.execute("INSERT INTO calls (id, started_at, consent, transcript) VALUES (?,?,?,?)",
                    (cid, time.strftime("%Y-%m-%d %H:%M:%S"), int(body.consent), "[]"))
    return {"id": cid}

@app.post("/api/chat")
async def chat(body: ChatIn):
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    msgs += [m.model_dump() for m in body.messages]
    if len(body.messages) == 0:
        msgs.append({"role": "user", "content": "(The call just connected. Greet the customer and ask how you can help.)"})
    return {"reply": await llm(msgs)}

@app.post("/api/calls/{cid}/end")
async def end_call(cid: str, body: EndIn):
    with db() as con:
        if not con.execute("SELECT id FROM calls WHERE id=?", (cid,)).fetchone():
            raise HTTPException(404, "call not found")
    transcript = [m.model_dump() for m in body.transcript]
    user_turns = [m for m in transcript if m["role"] == "user" and m["content"].strip()]
    result = {"summary": "The customer did not speak during the call.", "requirements": "None captured.",
              "objections": "None.", "next_steps": "Try calling again later.", "status": "No Response"}
    if user_turns:
        text = "\n".join(f"{m['role']}: {m['content']}" for m in transcript)
        prompt = ("Read this sales call transcript and reply with ONLY a JSON object with keys: "
                  "summary (2-3 sentences), requirements (string), objections (string), next_steps (string), "
                  "status (exactly one of: " + ", ".join(STATUSES) + "). "
                  "Use Converted only if the customer clearly agreed to buy or sign up. "
                  "Use Demo Requested if they asked for a demo. Write in English.\n\nTranscript:\n" + text)
        raw = await llm([{"role": "user", "content": prompt}], max_tokens=1500)
        try:
            data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            for k in ["summary", "requirements", "objections", "next_steps"]:
                result[k] = str(data.get(k, result[k]))
            result["status"] = data["status"] if data.get("status") in STATUSES else "Follow-up Required"
        except Exception:
            result["summary"] = "Summary could not be generated automatically."
            result["status"] = "Follow-up Required"
    with db() as con:
        con.execute("""UPDATE calls SET ended_at=?, duration=?, transcript=?, summary=?, requirements=?,
                       objections=?, next_steps=?, status=? WHERE id=?""",
                    (time.strftime("%Y-%m-%d %H:%M:%S"), body.duration, json.dumps(transcript),
                     result["summary"], result["requirements"], result["objections"],
                     result["next_steps"], result["status"], cid))
    return result

@app.post("/api/calls/{cid}/recording")
async def upload_recording(cid: str, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix or ".webm"
    path = REC_DIR / (cid + ext)
    path.write_bytes(await file.read())
    with db() as con:
        con.execute("UPDATE calls SET recording=? WHERE id=?", (path.name, cid))
    return {"saved": path.name}

@app.get("/api/calls")
def list_calls():
    with db() as con:
        rows = con.execute("SELECT id, started_at, duration, status, summary, recording FROM calls ORDER BY started_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.get("/api/calls/{cid}")
def get_call(cid: str):
    with db() as con:
        row = con.execute("SELECT * FROM calls WHERE id=?", (cid,)).fetchone()
    if not row:
        raise HTTPException(404, "call not found")
    d = dict(row)
    d["transcript"] = json.loads(d["transcript"] or "[]")
    return d

@app.get("/api/calls/{cid}/recording")
def get_recording(cid: str):
    with db() as con:
        row = con.execute("SELECT recording FROM calls WHERE id=?", (cid,)).fetchone()
    if not row or not row["recording"]:
        raise HTTPException(404, "no recording")
    return FileResponse(REC_DIR / row["recording"])

app.mount("/", StaticFiles(directory="static", html=True), name="static")
