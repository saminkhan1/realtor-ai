from typing import List, AsyncGenerator
from .custom_types import ResponseRequiredRequest, ResponseResponse, Utterance


BEGIN_SENTENCE = "Hey there, I'm an AI real estate assistant. How can I help you?"


class LlmClient:
    def __init__(self, graph, graph_config):
        self.graph = graph
        self.graph_config = graph_config

    def draft_begin_message(self) -> ResponseResponse:
        """Generate the initial message for the conversation."""
        return ResponseResponse(
            response_id=0,
            content=BEGIN_SENTENCE,
            content_complete=True,
            end_call=False,
        )

    @staticmethod
    def _convert_transcript_to_messages(transcript: List[Utterance]) -> List[dict]:
        """Convert the last utterance in the transcript to a message format."""
        utterance = transcript[-1]
        role = "assistant" if utterance.role == "agent" else "user"
        return [{"role": role, "content": utterance.content}]


    def _prepare_prompt(self, request: ResponseRequiredRequest):
        prompt = []
        transcript_messages = self._convert_transcript_to_messages(request.transcript)

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

    async def draft_response(self, request: ResponseRequiredRequest) -> AsyncGenerator[ResponseResponse, None]:
        """Generate a draft response based on the request."""
        prompt = self._prepare_prompt(request)
        result = self.graph.invoke({"messages": prompt}, self.graph_config)

        last_message_content = result["messages"][-1].content

        # Yield the intermediate response
        yield ResponseResponse(
            response_id=request.response_id,
            content=last_message_content,
            content_complete=False,
            end_call=False,
        )

        # Yield the final response to indicate completion
        yield ResponseResponse(
            response_id=request.response_id,
            content="",
            content_complete=True,
            end_call=False,
        )
