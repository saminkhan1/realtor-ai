import asyncio
import json
import logging
from datetime import datetime
from langchain_core.messages import HumanMessage, ToolMessage, AIMessageChunk
from src.util.appointment_tools import sensitive_tool_names
from .adapters import MessageAdapter
from typing import List
from .custom_types import (
    ResponseRequiredRequest,
    ResponseResponse,
    Utterance,
)

logger = logging.getLogger(__name__)


async def process_message(
    receiver: MessageAdapter, sender: MessageAdapter, graph, config, data
):
    """Main processing logic for incoming messages."""
    print("Starting process_message")
    raw_data = data
    print(f"Received raw data: {raw_data}")
    if raw_data and "content" in raw_data:
        message_content = raw_data["content"]
        user_message = HumanMessage(content=message_content)

        # Stream and collect the final response
        last_event = None
        final_content = ""

        for event in graph.stream(
            {"messages": [user_message]}, config, stream_mode="values"
        ):
            if "messages" in event and event["messages"]:
                last_event = event["messages"][-1]
                if last_event.content:
                    final_content = last_event.content
                    print(f"Updated final content: {final_content}")

        # Only send the final response
        if final_content:
            print(f"Sending final content")
            await send_response(sender, final_content, config)

        if last_event:
            response = await handle_event(last_event, sender, graph, config)
            if response:
                await send_response(sender, response, config)


async def handle_event(last_event, sender, graph, config):
    """Handle the last event and return the appropriate response."""
    print(f"Handling event: {last_event}")
    tool_calls = last_event.additional_kwargs.get("tool_calls")
    if tool_calls and tool_calls[-1]["function"]["name"] in sensitive_tool_names:
        print(f"Sensitive tool call detected: {tool_calls[-1]}")
        return await handle_sensitive_tool_call(
            sender, graph, tool_calls[-1]["id"], config
        )
    else:
        logger.info("Processing regular event")
        print("Processing regular event")
        return None


async def handle_sensitive_tool_call(sender, graph, tool_call_id, config):
    """Handle the logic for sensitive tool calls."""
    logger.info("Interruption detected for sensitive tool")
    print("Interruption detected for sensitive tool")
    await send_response(
        sender, "Confirmation Required, to confirm please reply with 'yes'", config
    )

    approval_data = await receive_message(sender)
    if approval_data:
        user_approval = approval_data.get("content", "").strip().lower()
        if user_approval == "yes":
            final_content = ""
            for event in graph.stream(None, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    message = event["messages"][-1]
                    if message.content:
                        final_content = message.content
            # Send only the final response
            if final_content:
                await send_response(sender, final_content, config)
            return None
        else:
            prompt = "Action not approved. Please suggest alternatives or ask if there's anything else you can help with."
            print(f"last_toolcall: {tool_call_id} \n")
            final_content = ""
            for event in graph.stream(
                {"messages": [ToolMessage(content=prompt, tool_call_id=tool_call_id)]},
                config,
                stream_mode="values",
            ):
                if "messages" in event and event["messages"]:
                    message = event["messages"][-1]
                    if message.content:
                        final_content = message.content

            # Send only the final response
            if final_content:
                await send_response(sender, final_content, config)
            return None

    return "User did not respond in time."


async def receive_message(receiver: MessageAdapter, timeout=3600):
    """Receive a message from the specified receiver (websocket, SMS, etc.)."""
    print("Waiting to receive message")
    try:
        raw_data = await asyncio.wait_for(receiver.receive_text(), timeout)
        print(f"Raw data received: {raw_data}")
        return json.loads(raw_data)
    except asyncio.TimeoutError:
        logger.warning("Message reception timed out.")
        print("Message reception timed out.")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        print(f"Failed to decode JSON: {e}")
        return None


async def send_response(sender: MessageAdapter, response, config):
    """Send a response back through the specified sender (websocket, SMS, etc.)."""
    print(f"Sending response: {response}")
    response_payload = {
        "type": "bot_response",
        "content": response,
        "timestamp": datetime.now().isoformat(),
    }
    if "response_id" in config["configurable"]:
        response_payload["response_id"] = config["configurable"]["response_id"]
    await sender.send_json(response_payload)


def convert_transcript_to_message(self, transcript: List[Utterance]):
    messages = []
    for utterance in transcript:
        if utterance.role == "agent":
            messages.append({"role": "assistant", "content": utterance.content})
        else:
            messages.append({"role": "user", "content": utterance.content})
    return messages
