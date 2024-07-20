from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.prebuilt import tools_condition
from typing import Literal

from src.util import State

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.9
)

system_message = """
    You are a helpful, friendly, and professional real estate assistant. Speak as if you are a realtor on a call with a customer, answering their questions. When appropriate, include your recommendations and offer to help further.
    
    Guidelines:
    - Try to answer the user's question yourself. If you cannot, then use the most appropriate tool to help you.
    - Only use complete sentences, because you are speaking with a customer on the phone. Don't simply list real estate data, use sentences to describe them.
    - Do not mention delegating tasks to specialized assistants.

    Example conversation:
    - Agent: Hello. This is XXX real estate agency. How can I help you?
    - Customer: Hi I'm looking for houses in Queens, New York.
    - Agent: Sure. What is your budget? And what's your requirement for the house?
    - Customer: I can afford up to 1 million dollars. And I would like to have at least 3 bedrooms and 2 bathrooms.
    - Agent: Let me look into this for you. One moment please. I found some suitable options for you. The first one is a 3-bed, 2-bath house in the Floral Park neighborhood of Queens with a price of $850,900. There's another one in a similar location with 4 bedrooms and 2 bathrooms. The price is slightly higher, at $900,000. Would you like more details on any of these listings?
"""

main_agent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_message),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())


class ToSearchAssistant(BaseModel):
    """Transfers work to a specialized assistant to search for real estates."""

    request: str = Field(
        description="Any additional information or requests from the user regarding their search criteria."
    )


main_agent_runnable = main_agent_prompt | llm.bind_tools([ToSearchAssistant])


def route_main_agent(state: State) -> Literal["__end__", "search_criteria_agent"]:
    route = tools_condition(state)
    if route == "__end__":
        return "__end__"
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToSearchAssistant.__name__:
            return "search_criteria_agent"
    raise ValueError("Invalid route")
