import json
from typing import Any, Dict, Optional
from fastapi import WebSocket
from .custom_types import ResponseResponse


class MessageAdapter:
    """Base adapter interface for different communication channels"""

    async def receive_text(self) -> str:
        raise NotImplementedError

    async def send_json(
        self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> None:
        raise NotImplementedError


class WebChatSocketAdapter(MessageAdapter):
    """Adapter for WebSocket connections"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def receive_text(self) -> str:
        return await self.websocket.receive_text()

    async def send_json(self, data: Dict[str, Any]) -> None:
        await self.websocket.send_json(data)


class SMSAdapter(MessageAdapter):
    """Adapter for SMS requests/responses"""

    def __init__(self, message: str):
        self.message = message
        self.response: Optional[str] = None

    async def receive_text(self) -> str:
        # Return the SMS message in the same format as WebSocket
        return json.dumps({"content": self.message})

    async def send_json(self, data: Dict[str, Any]) -> None:
        # Store the response content
        self.response = data["content"]


class RetellSocketAdapter(MessageAdapter):
    """Adapter for Retell WebSocket connections"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def receive_text(self) -> str:
        return await self.websocket.receive_text()

    async def send_json(self, data: Dict[str, Any]) -> None:
        print(f"Sending data from RetellSocketAdapter: {data}")
        response = ResponseResponse(
            response_id=data["response_id"],
            content=data["content"],
            content_complete=True,
            end_call=False,
        )
        await self.websocket.send_json(response.__dict__)
