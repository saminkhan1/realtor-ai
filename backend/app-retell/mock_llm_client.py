import os

beginSentence = "How may I help you?"


class LlmDummyMock:
    def __init__(self):
        pass

    def draft_begin_messsage(self):
        return {
            "response_id": 0,
            "content": beginSentence,
            "content_complete": True,
            "end_call": False,
        }

    def draft_response(self, request):
        yield {
            "response_id": request["response_id"],
            "content": "I am sorry, can you say that again?",
            "content_complete": True,
            "end_call": False,
        }
