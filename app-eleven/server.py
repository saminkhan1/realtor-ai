import os
import sys
import asyncio
import json
import base64
import uuid
# import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Response, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from elevenlabs.client import ElevenLabs
from elevenlabs import play, stream, save


current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.graph import create_graph

load_dotenv()

app = FastAPI()
client = ElevenLabs()
twilio_client = Client()

VOICE_ID = 'oWAxZDx7w5VEj9dCyTzz' # Grace
OUTPUT_FORMAT = 'ulaw_8000'
TEXT = 'This is a test. You can now hang up. Thank you.'

graph = create_graph()
thread_id = str(uuid.uuid4())

graph_config = {
    "configurable": {
        "thread_id": thread_id,
    }
}

@app.get("/")
async def main_route():
    return PlainTextResponse("real estate assistant")

@app.post("/call/incoming")
async def incoming_call(request: Request):
    try:
    # data = await request.form()
    # # recording_url = data.get('RecordingUrl')
    # recording_sid = data.get('RecordingSid')
    # # transcripts = client.transcriptions.list(recording_sid=recording_sid)
    # transcripts = "I want to see some houses in New York City under 800k"

    # url = "ws://localhost:8000/call/connection"
    # async with websockets.connect(url) as websocket:
    #     await websocket.send(json.dumps({"event": "user_message", "user_message": transcripts}))

        response = VoiceResponse()
        response.connect().stream(url=f"wss://oyster-ace-sturgeon.ngrok-free.app/call/connection")
        # response.connect().stream(url=f"wss://{os.getenv('SERVER_DOMAIN')}/call/connection")
        return Response(content=str(response), media_type="text/xml")
    except Exception as err:
        print(f"Error in twilio voice webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )


@app.websocket("/call/connection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            print(message)

            # if message["event"] == "user_message":
            #     user_message = message["user_message"]
            #     print(f"User: {user_message}")
            #     response = graph.invoke(
            #         {"messages": [
            #             {
            #                 "role": "user",
            #                 "content": user_message
            #             }
            #         ]},
            #         graph_config
            #     )
            #     ai_message = response["messages"][-1].content
            #     print(f"AI: {ai_message}")

            if message["event"] == "start" and "start" in message:
                stream_sid = message["start"]["streamSid"]
                response_audio = client.generate(
                    text="hello",
                    voice=VOICE_ID,
                    model="eleven_turbo_v2",
                    output_format=OUTPUT_FORMAT
                    # output_format="mp3_44100_128"
                )

                # save_file_path = f"{uuid.uuid4()}.mp3"
                # save(response_audio, save_file_path)

                audio_data = b''.join(chunk for chunk in response_audio)

                await websocket.send_json({
                    "streamSid": stream_sid,
                    "event": "media",
                    "media": {
                        "payload": base64.b64encode(audio_data).decode('utf-8')
                    }
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
