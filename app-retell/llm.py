from openai import AsyncOpenAI
import os
import uuid
from typing import List
from .custom_types import (
    ResponseRequiredRequest,
    ResponseResponse,
    Utterance,
)

begin_sentence = "Hey there, I'm an AI real estate assistant. How can I help you?"

class LlmClient:
    def __init__(self, graph, graph_config):
        self.graph = graph
        self.graph_config = graph_config

    def draft_begin_message(self):
        response = ResponseResponse(
            response_id=0,
            content=begin_sentence,
            content_complete=True,
            end_call=False,
        )
        return response

    def convert_transcript_to_openai_messages(self, transcript: List[Utterance]):
        messages = []
        utterance = transcript[-1]
        if utterance.role == "agent":
            messages.append({"role": "assistant", "content": utterance.content})
        else:
            messages.append({"role": "user", "content": utterance.content})
        print(messages)
        return messages

    def prepare_prompt(self, request: ResponseRequiredRequest):
        prompt = []
        transcript_messages = self.convert_transcript_to_openai_messages(
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
        result = self.graph.invoke(
            {"messages": prompt},
            self.graph_config
        )

        response = ResponseResponse(
            response_id=request.response_id,
            content=result["messages"][-1].content,
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
