from openai import AsyncOpenAI
import os
from typing import List
from .custom_types import (
    ResponseRequiredRequest,
    ResponseResponse,
    Utterance,
)
from dotenv import load_dotenv

load_dotenv()
begin_sentence = "Hey there, I'm an AI real estate assistant. How can I help you?"


class VoiceLlmClient:
    def __init__(self):
        self.client = AsyncOpenAI()

    def draft_begin_message(self):
        response = ResponseResponse(
            response_id=0,
            content=begin_sentence,
            content_complete=True,
            end_call=False,
        )
        return response

    def convert_transcript_to_message(self, transcript: List[Utterance]):
        print(f"Converting transcript to OpenAI messages: {transcript}")
        messages = []
        for utterance in transcript:
            if utterance.role == "agent":
                messages.append({"role": "assistant", "content": utterance.content})
            else:
                messages.append({"role": "user", "content": utterance.content})
        print(f"Converted transcript to OpenAI messages: {messages}")
        return messages[-1]["content"]

    def prepare_prompt(self, request: ResponseRequiredRequest):
        prompt = []
        transcript_messages = self.convert_transcript_to_message(
            request.transcript
        )
        for message in transcript_messages:
            prompt.append(message)

        if request.interaction_type == "reminder_required":
            prompt.append(
                {
                    "role": "user",
                    "content": "(Now the user has not responded in a while, you would say:)",
                }
            )
        return prompt

    async def draft_response(self, request: ResponseRequiredRequest):
        prompt = self.prepare_prompt(request)
        stream = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response = ResponseResponse(
                    response_id=request.response_id,
                    content=chunk.choices[0].delta.content,
                    content_complete=False,
                    end_call=False,
                )
                yield response

        # Send final response with "content_complete" set to True to signal completion
        response = ResponseResponse(
            response_id=request.response_id,
            content="",
            content_complete=True,
            end_call=False,
        )
        yield response
