from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from src.state import State
from dotenv import load_dotenv
from typing import Optional

from langchain_core.pydantic_v1 import BaseModel


load_dotenv()
# Create a ChatOpenAI instance
model = ChatOpenAI(model="gpt-3.5-turbo-0125")


class SearchCriteriaObject(BaseModel):
    city: Optional[str]
    state: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    max_price: Optional[float]
    min_price: Optional[float]


structured_llm = model.with_structured_output(SearchCriteriaObject)

SYSTEM_MESSAGE = """
You are an AI assistant for a real estate search application. Your task is to interpret user queries about property searches and generate a JSON object representing the search criteria. The criteria should follow this structure:

    {
        "search_criteria": {
            "city": Optional[str],
            "state": Optional[str],
            "min_bedroom": Optional[int],
            "min_bathroom": Optional[int],
            "max_price": Optional[float],
            "min_price": Optional[float]
        }
    }

    Guidelines:
    1. If the user's query indicates a new search (e.g., asking about a different location), create a new search criteria object, discarding any previous criteria.
    2. If the query is a follow-up or modification to a previous search, update the existing criteria by adding new information or modifying existing fields.
    3. Use singular forms for 'bedroom' and 'bathroom' in the JSON output.
    4. For bedroom and bathroom counts, use the 'min_' prefix to indicate "at least" this many.
    5. Infer the state if a well-known city is mentioned (e.g., "New York" implies "New York" state).
    6. If a price range is mentioned, use 'min_price' and 'max_price' accordingly.
    7. Only include fields in the JSON that are explicitly mentioned or can be reasonably inferred from the user's query.
    8. The entire response should be a valid JSON object with a single key "search_criteria" containing the search criteria object.
"""


def search_criteria_agent(state: State) -> Dict[str, Any]:
    # Extract the last user message
    last_user_message = state["messages"][-1] if state["messages"] else None

    if last_user_message is None:
        return {
            "messages": [
                AIMessage(
                    content="I'm sorry, but I couldn't find a user message to respond to."
                )
            ]
        }

    user_query = last_user_message.content
    current_criteria = state.get("search_criteria", {})
    # Prepare the messages for the ChatOpenAI model
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": f"Current Criteria: {current_criteria}"},
        {"role": "user", "content": f"User Query: {user_query}"},
    ]

    # Get the response from the model
    response = model.invoke(messages)

    # Extract the new search criteria from the response
    # Note: In a real implementation, you'd want to add error handling here
    new_search_criteria = eval(response.content)
    # Generate a response message
    response = "I've updated your search criteria based on your request. Here's what I understood:\n"
    for key, value in new_search_criteria.items():
        if value is not None:
            response += f"- {key.replace('_', ' ').capitalize()}: {value}\n"

    response += "\nIs there anything else you'd like to modify or add to your search?"

    # Return the updated state
    return {
        "search_criteria": new_search_criteria,
        "messages": [AIMessage(content=response)],
    }
