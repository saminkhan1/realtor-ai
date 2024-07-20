import json
import os
import asyncio
import uuid
import sys
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from concurrent.futures import TimeoutError as ConnectionTimeoutError
from langchain_core.messages import HumanMessage
from retell import Retell
from retell.resources.call import RegisterCallResponse

from .custom_types import (
    ConfigResponse,
    ResponseRequiredRequest,
)
from .twilio_server import TwilioClient
from .llm import LlmClient  # or use .llm_with_func_calling

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)


from src.graph import create_graph


# ngrok http --domain=oyster-ace-sturgeon.ngrok-free.app 8000

app = FastAPI()
retell = Retell(api_key=os.environ["RETELL_API_KEY"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graph = create_graph()
thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}

questions = [
    "What properties are available in New York?",
    # "Show me houses with at least 3 bedrooms and 2 bathrooms.",
    # "Do you have any properties under $500,000?",
]


load_dotenv(override=True)
app = FastAPI()
retell = Retell(api_key=os.environ["RETELL_API_KEY"])
twilio_client = TwilioClient()


@app.get("/")
async def main_route():
    return PlainTextResponse("real estate assistant")

# Handle webhook from Retell server. This is used to receive events from Retell server.
# Including call_started, call_ended, call_analyzed
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        post_data = await request.json()
        valid_signature = retell.verify(
            json.dumps(post_data, separators=(",", ":")),
            api_key=str(os.environ["RETELL_API_KEY"]),
            signature=str(request.headers.get("X-Retell-Signature")),
        )
        if not valid_signature:
            print(
                "Received Unauthorized",
                post_data["event"],
                post_data["data"]["call_id"],
            )
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})
        if post_data["event"] == "call_started":
            print("Call started event", post_data["data"]["call_id"])
        elif post_data["event"] == "call_ended":
            print("Call ended event", post_data["data"]["call_id"])
        elif post_data["event"] == "call_analyzed":
            print("Call analyzed event", post_data["data"]["call_id"])
        else:
            print("Unknown event", post_data["event"])
        return JSONResponse(status_code=200, content={"received": True})
    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )


# Twilio voice webhook. This will be called whenever there is an incoming or outgoing call.
# Register call with Retell at this stage and pass in returned call_id to Retell.
@app.post("/twilio-voice-webhook/{agent_id_path}")
async def handle_twilio_voice_webhook(request: Request, agent_id_path: str):
    try:
        # Check if it is machine
        post_data = await request.form()
        if "AnsweredBy" in post_data and post_data["AnsweredBy"] == "machine_start":
            twilio_client.end_call(post_data["CallSid"])
            return PlainTextResponse("")
        elif "AnsweredBy" in post_data:
            return PlainTextResponse("")

        call_response: RegisterCallResponse = retell.call.register(
            agent_id=agent_id_path,
            audio_websocket_protocol="twilio",
            audio_encoding="mulaw",
            sample_rate=8000,  # Sample rate has to be 8000 for Twilio
            from_number=post_data["From"],
            to_number=post_data["To"],
            metadata={
                "twilio_call_sid": post_data["CallSid"],
            },
        )
        print(f"Call response: {call_response}")

        response = VoiceResponse()
        start = response.connect()
        start.stream(
            url=f"wss://api.retellai.com/audio-websocket/{call_response.call_id}"
        )
        return PlainTextResponse(str(response), media_type="text/xml")
    except Exception as err:
        print(f"Error in twilio voice webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )


# Start a websocket server to exchange text input and output with Retell server. Retell server
# will send over transcriptions and other information. This server here will be responsible for
# generating responses with LLM and send back to Retell server.
@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    try:
        await websocket.accept()
        
        graph = create_graph()
        graph_config = {
            "configurable": {
                "thread_id": str(uuid.uuid4())
            }
        }
        llm_client = LlmClient(graph, graph_config)

        # Send optional config to Retell server
        config = ConfigResponse(
            response_type="config",
            config={
                "auto_reconnect": True,
                "call_details": True,
            },
            response_id=1,
        )
        await websocket.send_json(config.__dict__)

        # Send first message to signal ready of server
        response_id = 0
        first_event = llm_client.draft_begin_message()
        await websocket.send_json(first_event.__dict__)

        async def handle_message(request_json):
            nonlocal response_id

            # There are 5 types of interaction_type: call_details, pingpong, update_only, response_required, and reminder_required.
            # Not all of them need to be handled, only response_required and reminder_required.
            if request_json["interaction_type"] == "call_details":
                print(json.dumps(request_json, indent=2))
                return
            if request_json["interaction_type"] == "ping_pong":
                await websocket.send_json(
                    {
                        "response_type": "ping_pong",
                        "timestamp": request_json["timestamp"],
                    }
                )
                return
            if request_json["interaction_type"] == "update_only":
                return
            if (
                request_json["interaction_type"] == "response_required"
                or request_json["interaction_type"] == "reminder_required"
            ):
                response_id = request_json["response_id"]
                request = ResponseRequiredRequest(
                    interaction_type=request_json["interaction_type"],
                    response_id=response_id,
                    transcript=request_json["transcript"],
                )
                print(
                    f"""Received interaction_type={request_json['interaction_type']}, response_id={response_id}, last_transcript={request_json['transcript'][-1]['content']}"""
                )

                async for event in llm_client.draft_response(request):
                    await websocket.send_json(event.__dict__)
                    if request.response_id < response_id:
                        break  # new response needed, abandon this one

        async for data in websocket.iter_json():
            asyncio.create_task(handle_message(data))

    except WebSocketDisconnect:
        print(f"LLM WebSocket disconnected for {call_id}")
    except ConnectionTimeoutError as e:
        print("Connection timeout error for {call_id}")
    except Exception as e:
        print(f"Error in LLM WebSocket: {e} for {call_id}")
        await websocket.close(1011, "Server error")
    finally:
        print(f"LLM WebSocket connection closed for {call_id}")



@app.post("/sms")
async def handle_sms(request: Request):
    try:
        # Get the message the user sent our Twilio number
        form_data = await request.form()
        user_message = form_data.get('Body', None).strip()
        # logger.info(f"User message: {user_message}")

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=user_message)
                ]
            },
            config
        )

        ai_message = result["messages"][-1].content
        # logger.info(f"AI message: {ai_message}")

        # Create Twilio response
        resp = MessagingResponse()
        resp.message(ai_message)
        final_response = str(resp)
        # logger.info(f"Final Twilio response: {final_response}")
        
        return Response(content=ai_message, media_type="text/plain")
        # return Response(content=final_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Response(content="An error occurred", status_code=500)
