import uuid
import logging
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from langchain_core.messages import HumanMessage

from src.graph import create_graph

# ngrok http --domain=oyster-ace-sturgeon.ngrok-free.app 8000

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graph = create_graph()
thread_id = str(uuid.uuid4())
# Example usage of the graph
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

@app.post("/sms")
async def handle_sms(request: Request):
    try:
        # Get the message the user sent our Twilio number
        form_data = await request.form()
        user_message = form_data.get('Body', None).strip()
        logger.info(f"User message: {user_message}")

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=user_message)
                ]
            },
            config
        )

        ai_message = result["messages"][-1].content
        logger.info(f"AI message: {ai_message}")

        # Create Twilio response
        resp = MessagingResponse()
        resp.message(ai_message)
        final_response = str(resp)
        logger.info(f"Final Twilio response: {final_response}")
        
        return Response(content=final_response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return Response(content="An error occurred", status_code=500)

# @app.post("/voice")
# async def handle_voice(request: Request):
#     form_data = await request.form()
#     # For voice, you might want to use Twilio's speech recognition
#     # or handle DTMF input. This example assumes speech-to-text is already done.
#     incoming_msg = form_data.get('SpeechResult', '').strip()

#     # Process with LangGraph
#     result = chain.invoke({"messages": [HumanMessage(content=incoming_msg)]})
#     ai_response = result["messages"][-1].content

#     # Create Twilio voice response
#     resp = VoiceResponse()
#     resp.say(ai_response)
    
#     return Response(content=str(resp), media_type="application/xml")