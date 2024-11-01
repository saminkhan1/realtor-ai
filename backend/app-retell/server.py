import asyncio
from email import generator
import logging
import json
import os
from datetime import datetime
from tracemalloc import start
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, Request, WebSocket, Depends, Response, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, ToolMessage
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from concurrent.futures import TimeoutError as ConnectionTimeoutError
from retell import Retell
from .custom_types import (
    ConfigResponse,
    ResponseRequiredRequest,
)
from .voice_llm_client import VoiceLlmClient

from src.graph import create_graph
from .adapters import RetellSocketAdapter, WebChatSocketAdapter, SMSAdapter
from .message_handler import (
    convert_transcript_to_message,
    process_message,
    handle_event,
    handle_sensitive_tool_call,
    receive_message,
    send_response,
)

load_dotenv(override=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()
load_dotenv()
retell = Retell(api_key=os.getenv("RETELL_API_KEY", ""))

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Graph:
    def __init__(self):
        self.graph = create_graph()

    def get_graph(self):
        return self.graph


def get_graph():
    return app.state.graph.get_graph()


@app.on_event("startup")
async def startup_event():
    app.state.graph = Graph()


@app.get("/")
async def main_route() -> str:
    return "Hello World! I'm a Real Estate Assistant"


# WebSocket endpoint for browser chat
@app.websocket("/ws/{website_id}/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    website_id: str,
    thread_id: str,
    graph: Graph = Depends(get_graph),
):
    await websocket.accept()

    config = {
        "configurable": {
            "user_id": website_id,
            "thread_id": thread_id,
        }
    }

    adapter = WebChatSocketAdapter(websocket)
    try:
        # while True:
        async for data in websocket.iter_json():
            try:
                print(f"Received data: {data}")
                await process_message(adapter, adapter, graph, config, data)
            except Exception as e:
                logger.error(f"Error during WebSocket message processing: {str(e)}")
                await send_response(
                    adapter, "An error occurred during processing.", config
                )
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for thread {thread_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}")


# SMS endpoint for Twilio
@app.post("/sms")
async def handle_sms(request: Request, graph: Graph = Depends(get_graph)):
    try:
        form_data = await request.form()
        user_message = form_data.get("Body", "").strip()
        sender_id = form_data.get("From", "unknown")

        config = {
            "configurable": {
                "user_id": sender_id,
                "thread_id": f"sms_{sender_id}",
            }
        }

        # Create SMS adapter with the incoming message
        adapter = SMSAdapter(user_message)

        # Process the message using the same flow as WebSocket
        await process_message(
            adapter, adapter, graph, config, config["configurable"]["thread_id"]
        )

        # Create Twilio response
        twilio_response = MessagingResponse()
        if adapter.response:
            twilio_response.message(adapter.response)

        return Response(content=str(twilio_response), media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing SMS message: {str(e)}")
        twilio_response = MessagingResponse()
        twilio_response.message("An error occurred. Please try again later.")
        return Response(
            content=str(twilio_response), media_type="application/xml", status_code=500
        )


# Handle webhook from Retell server. This is used to receive events from Retell server.
# Including call_started, call_ended, call_analyzed
@app.post("/retell-webhook")
async def handle_webhook(request: Request):
    try:
        post_data = await request.json()

        # Validate signature - using the exact same format as original
        signature = request.headers.get("X-Retell-Signature")
        if not signature:
            logger.warning("Missing Retell signature header")
            return JSONResponse(
                status_code=401, content={"message": "Missing signature header"}
            )

        valid_signature = retell.verify(
            json.dumps(post_data, separators=(",", ":"), ensure_ascii=False),
            api_key=str(os.environ["RETELL_API_KEY"]),
            signature=signature,
        )

        if not valid_signature:
            logger.warning(
                f"Invalid signature for call {post_data.get('data', {}).get('call_id')}"
            )
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        # Handle different event types with logging
        event_type = post_data.get("event")
        call_id = post_data.get("data", {}).get("call_id")

        match event_type:
            case "call_started":
                logger.info("Call started", extra={"call_id": call_id})
            case "call_ended":
                logger.info("Call ended", extra={"call_id": call_id})
            case "call_analyzed":
                logger.info("Call analyzed", extra={"call_id": call_id})
            case _:
                logger.warning(
                    f"Unknown event type: {event_type}", extra={"call_id": call_id}
                )

        return JSONResponse(status_code=200, content={"received": True})

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JSONResponse(status_code=400, content={"message": "Invalid JSON format"})
    except Exception as err:
        logger.exception("Error processing webhook")
        return JSONResponse(
            status_code=500, content={"message": "Internal server error"}
        )


# start a websocket server to exchange text input and output with Retell server. Retell server
# will send over transcriptions and other information. This server here will be responsible for
# generator responses with LLM and send back to Retell server.
@app.websocket("/retell-llm-websocket/{call_id}")
async def websocket_handler(
    websocket: WebSocket, call_id: str, graph: Graph = Depends(get_graph)
):
    try:
        await websocket.accept()
        llm_client = VoiceLlmClient()

        # Send optional initial config to Retell server
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

        async def handle_message(request_json: dict) -> None:
            nonlocal response_id

            try:
                interaction_type = request_json.get("interaction_type")

                match interaction_type:
                    case "call_details":
                        logger.info(
                            "Call details received",
                            extra={
                                "call_id": call_id,
                                "details": json.dumps(request_json),
                            },
                        )
                        return

                    case "ping_pong":
                        await websocket.send_json(
                            {
                                "response_type": "ping_pong",
                                "timestamp": request_json.get("timestamp"),
                            }
                        )
                        return

                    case "update_only":
                        return

                    case "response_required" | "reminder_required":
                        response_id = request_json["response_id"]
                        request = ResponseRequiredRequest(
                            interaction_type=interaction_type,
                            response_id=response_id,
                            transcript=request_json["transcript"],
                        )

                        handler_config = {
                            "configurable": {
                                "user_id": call_id,
                                "thread_id": call_id,
                                "response_id": response_id,
                            }
                        }

                        adapter = RetellSocketAdapter(websocket)
                        # convert transcript to openai messages
                        message = llm_client.convert_transcript_to_message(
                            request.transcript
                        )
                        data = {"content": message}

                        await process_message(
                            adapter, adapter, graph, handler_config, data
                        )

                        # async for event in llm_client.draft_response(
                        #     request, graph, config
                        # ):
                        #     if request.response_id < response_id:
                        #         logger.info(
                        #             "Abandoning old response due to new request"
                        #         )
                        #         break
                        #     await websocket.send_json(event.__dict__)

            except KeyError as e:
                logger.error(
                    f"Missing required field in message: {e}",
                    extra={"call_id": call_id},
                )
            except Exception as e:
                logger.exception("Error processing message", extra={"call_id": call_id})
                raise

        async for data in websocket.iter_json():
            await handle_message(data)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", extra={"call_id": call_id})
    except ConnectionTimeoutError:
        logger.error("Connection timeout", extra={"call_id": call_id})
    except Exception as e:
        logger.exception("Unexpected WebSocket error", extra={"call_id": call_id})
        if websocket.client_state.CONNECTED:
            await websocket.close(1011, "Server error")


# For testing purposes, we can use the dummy mock class to test the websocket connection

# @app.websocket("/retell-llm-websocket/{call_id}")
# async def websocket_handler(websocket: WebSocket, call_id: str):
#     await websocket.accept()
#     print(f"Handle llm ws for: {call_id}")

#     llm_client = LlmDummyMock()

#     # send first message to signal ready of server
#     response_id = 0
#     first_event = llm_client.draft_begin_messsage()
#     await websocket.send_text(json.dumps(first_event))

#     async def stream_response(request):
#         nonlocal response_id
#         for event in llm_client.draft_response(request):
#             await websocket.send_text(json.dumps(event))
#             if request["response_id"] < response_id:
#                 return  # new response needed, abondon this one

#     try:
#         while True:
#             message = await websocket.receive_text()
#             request = json.loads(message)
#             # print out transcript
#             os.system("cls" if os.name == "nt" else "clear")
#             print(json.dumps(request, indent=4))

#             if "response_id" not in request:
#                 continue  # no response needed, process live transcript update if needed
#             response_id = request["response_id"]
#             asyncio.create_task(stream_response(request))
#     except WebSocketDisconnect:
#         print(f"LLM WebSocket disconnected for {call_id}")
#     except Exception as e:
#         print(f"LLM WebSocket error for {call_id}: {e}")
#     finally:
#         print(f"LLM WebSocket connection closed for {call_id}")
