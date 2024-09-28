import asyncio
import logging
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from langchain_core.messages import HumanMessage, ToolMessage
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from concurrent.futures import TimeoutError as ConnectionTimeoutError
from retell import Retell
from retell.resources.call import RegisterCallResponse

from .custom_types import ConfigResponse, ResponseRequiredRequest
from .llm import LlmClient
from .twilio_server import TwilioClient
from src.graph import create_graph

load_dotenv(override=True)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()
retell = Retell(api_key=os.environ["RETELL_API_KEY"])
twilio_client = TwilioClient()

# In-memory stores
active_sessions: Dict[str, Dict] = {}
website_ids: Dict[str, str] = {
    "website1": "http://localhost:5173",
    "website2": "http://localhost:5174",
    # ... add all 50 website IDs and their origins
}

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in website_ids.values()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class Graph:
    def __init__(self):
        self.graph = create_graph()

    def get_graph(self):
        return self.graph

@app.on_event("startup")
async def startup_event():
    app.state.graph = Graph()
    logger.info("Graph initialized")
    asyncio.create_task(cleanup_inactive_sessions())
    logger.info("Cleanup task started")

def get_graph():
    return app.state.graph.get_graph()

@app.get("/")
async def main_route() -> str:
    return "Hello World! I'm a Real Estate Assistant"

@app.websocket("/ws/{website_id}/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    website_id: str, 
    thread_id: str,
    graph: Graph = Depends(get_graph)
):
    if website_id not in website_ids:
        await websocket.close(code=4001, reason="Invalid website ID")
        return

    origin = websocket.headers.get("origin")
    if origin != website_ids[website_id]:
        await websocket.close(code=4002, reason="Unauthorized origin")
        return

    await websocket.accept()
    logger.info(f"WebSocket connection accepted for website_id: {website_id}, thread_id: {thread_id}")

    try:
        active_sessions[thread_id] = {
            "website_id": website_id,
            "last_activity": datetime.now(),
            "websocket": websocket
        }

        config = {
            "configurable": {
                "user_id": website_id,
                "thread_id": thread_id,
            }
        }

        while True:
            try:
                raw_data = await asyncio.wait_for(websocket.receive_text(), timeout=3600)  # 1 hour timeout
                try:
                    data = json.loads(raw_data)
                    if isinstance(data, dict) and "content" in data:
                        message_content = data["content"]
                    elif isinstance(data, dict) and "approval" in data:
                        # Handle tool call approval
                        user_input = data["approval"]
                        if user_input.lower() == "yes":
                            result = graph.invoke(None, config)
                        else:
                            result = graph.invoke(
                                {
                                    "messages": [
                                        ToolMessage(
                                            tool_call_id=last_message.tool_calls[0].id,
                                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                        )
                                    ]
                                },
                                config,
                            )
                        await websocket.send_json({
                            "type": "bot_response",
                            "content": result["messages"][-1].content,
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    else:
                        raise ValueError("Invalid message format")
                except (json.JSONDecodeError, ValueError) as e:
                    await websocket.send_json({"type": "error", "content": str(e)})
                    continue

                try:
                    message = ChatMessage(content=message_content)
                except ValidationError as val_err:
                    logger.error(f"Validation error: {str(val_err)}")
                    await websocket.send_json({"type": "error", "content": "Invalid message format."})
                    continue
                
                # Process the message using the graph
                for event in graph.stream(
                    {"messages": [HumanMessage(content=message.content)]}, 
                    config, 
                    stream_mode="values"
                ):
                    if "messages" in event:
                        await websocket.send_json({
                            "type": "bot_response",
                            "content": event["messages"][-1].content,
                            "timestamp": datetime.now().isoformat()
                        })

                snapshot = graph.get_state(config)

                while snapshot.next:
                    last_message = snapshot.values["messages"][-1]
                    if last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            # Send tool call info to client for approval
                            await websocket.send_json({
                                "type": "tool_call",
                                "content": str(tool_call),
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # Wait for client approval
                            approval_data = await websocket.receive_json()
                            user_input = approval_data.get("approval", "").lower()

                            if user_input == "yes":
                                result = graph.invoke(None, config)
                            else:
                                result = graph.invoke(
                                    {
                                        "messages": [
                                            ToolMessage(
                                                tool_call_id=last_message.tool_calls[0].id,
                                                content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                            )
                                        ]
                                    },
                                    config,
                                )
                            
                            # Send the result back to the client
                            await websocket.send_json({
                                "type": "bot_response",
                                "content": result["messages"][-1].content,
                                "timestamp": datetime.now().isoformat()
                            })

                            snapshot = graph.get_state(config)

                active_sessions[thread_id]["last_activity"] = datetime.now()

            except asyncio.TimeoutError:
                logger.warning(f"Session timeout for thread_id: {thread_id}")
                break
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for website_id: {website_id}, thread_id: {thread_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket communication for thread_id {thread_id}: {str(e)}")
                await websocket.send_json({"type": "error", "content": "An error occurred during processing."})

    finally:
        if thread_id in active_sessions:
            del active_sessions[thread_id]
            logger.info(f"Session removed for thread_id: {thread_id}")

async def cleanup_inactive_sessions():
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        now = datetime.now()          
        to_remove = [
            thread_id for thread_id, session in active_sessions.items()
            if now - session["last_activity"] > timedelta(hours=1)
        ]
        for thread_id in to_remove:
            try:
                session = active_sessions[thread_id]
                await session["websocket"].close(code=4000, reason="Session timeout")
                del active_sessions[thread_id]
                logger.info(f"Closed inactive session for thread_id: {thread_id}")
            except Exception as e:
                logger.error(f"Error closing websocket for thread_id {thread_id}: {str(e)}")
        
        logger.info(f"Cleaned up {len(to_remove)} inactive sessions")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/twilio-voice-webhook/{agent_id_path}")
async def handle_twilio_voice_webhook(request: Request, agent_id_path: str):
    try:
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
            sample_rate=8000,
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
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        event_messages = {
            "call_started": "Call started event",
            "call_ended": "Call ended event",
            "call_analyzed": "Call analyzed event"
        }

        event = post_data.get("event")
        call_id = post_data["data"].get("call_id")

        print(event_messages.get(event, "Unknown event"), call_id or event)
        return JSONResponse(status_code=200, content={"received": True})

    except Exception as err:
        print(f"Error in webhook: {err}")
        return JSONResponse(
            status_code=500, content={"message": "Internal Server Error"}
        )

@app.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    try:
        await websocket.accept()

        graph = create_graph()
        graph_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        llm_client = LlmClient(graph, graph_config)

        config = ConfigResponse(
            response_type="config",
            config={
                "auto_reconnect": True,
                "call_details": True,
            },
            response_id=1,
        )
        await websocket.send_json(config.__dict__)

        response_id = 0
        first_event = llm_client.draft_begin_message()
        await websocket.send_json(first_event.__dict__)

        async def handle_message(request_json):
            nonlocal response_id

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
        form_data = await request.form()
        user_message = form_data.get("Body", None).strip()

        result = graph.invoke(
            {"messages": [HumanMessage(content=user_message)]}, config
        )

        ai_message = result["messages"][-1].content

        resp = MessagingResponse()
        resp.message(ai_message)

        return Response(content=ai_message, media_type="text/plain")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Response(content="An error occurred", status_code=500)

@app.exception_handler(HTTPException)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )

