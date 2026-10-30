import os, hmac, hashlib
from collections import defaultdict, deque
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from pydantic import BaseModel
from rag import answer

load_dotenv()
app = FastAPI()

WA_TOKEN = os.environ["WA_TOKEN"]
PHONE_ID = os.environ["WA_PHONE_ID"]
VERIFY = os.environ["WA_VERIFY_TOKEN"]
SECRET = os.environ["WA_APP_SECRET"].encode()

history = defaultdict(lambda: deque(maxlen=6))   # memori percakapan per nomor
seen = deque(maxlen=1000)                        # dedupe message id (webhook bisa retry)

async def send_wa(to, text):
    async with httpx.AsyncClient(timeout=20) as c:
        await c.post(
            f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {WA_TOKEN}"},
            json={"messaging_product": "whatsapp", "to": to,
                  "type": "text", "text": {"body": text}},
        )

async def handle(sender, text):
    h = history[sender]
    reply, escalate = answer(text, list(h))
    h.append({"role": "user", "content": text})
    h.append({"role": "assistant", "content": reply})
    await send_wa(sender, reply)
    if escalate:
        # TODO: kirim notifikasi ke agen CS (Slack/email/helpdesk) beserta sender + text
        print(f"[ESKALASI] {sender}: {text}")

@app.get("/webhook")
async def verify(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == VERIFY:
        return Response(p.get("hub.challenge"), media_type="text/plain")
    raise HTTPException(403)

@app.post("/webhook")
async def receive(request: Request, bg: BackgroundTasks):
    raw = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(403, "bad signature")

    data = await request.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change["value"].get("messages", []):
                if msg["id"] in seen:
                    continue
                seen.append(msg["id"])
                if msg.get("type") == "text":
                    bg.add_task(handle, msg["from"], msg["text"]["body"])
                else:
                    bg.add_task(send_wa, msg["from"],
                                "Maaf, saat ini saya hanya bisa membaca pesan teks ya.")
    return {"status": "ok"}

class ChatIn(BaseModel):
    user: str = "tester"
    text: str

@app.post("/chat")
async def chat(body: ChatIn):
    h = history[body.user]
    reply, escalate = answer(body.text, list(h))
    h.append({"role": "user", "content": body.text})
    h.append({"role": "assistant", "content": reply})
    return {"reply": reply, "escalate": escalate}