import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Response, PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse
from elevenlabs import generate, set_api_key
import asyncio
import json
import base64

load_dotenv()

app = FastAPI()

# set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# PORT = int(os.getenv("PORT", "5000"))
VOICE_ID = 'oWAxZDx7w5VEj9dCyTzz' # Grace
OUTPUT_FORMAT = 'ulaw_8000'
TEXT = 'This is a test. You can now hang up. Thank you.'

@app.get("/")
async def main_route():
    return PlainTextResponse("real estate assistant")

@app.post("/call/incoming")
async def incoming_call():
    twiml = VoiceResponse()
    twiml.connect().stream(url=f"wss://{os.getenv('SERVER_DOMAIN')}/call/connection")
    return Response(content=str(twiml), media_type="text/xml")

@app.websocket("/call/connection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["event"] == "start" and "start" in message:
                stream_sid = message["start"]["streamSid"]
                audio = generate(
                    text=TEXT,
                    voice=VOICE_ID,
                    model="eleven_turbo_v2",
                    output_format=OUTPUT_FORMAT
                )

                await websocket.send_json({
                    "streamSid": stream_sid,
                    "event": "media",
                    "media": {
                        "payload": base64.b64encode(audio).decode('utf-8')
                    }
                })
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print(f"Local: http://localhost:{PORT}")
    print(f"Remote: https://{os.getenv('SERVER_DOMAIN')}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)