from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.prebuilt import tools_condition
from typing import Literal

from src.util import State

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

main_agent_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful real estate assistant."
            " Your primary role is to identify user's intent,"
            " and delegate the task to the appropriate specialized assistant,"
            " then answer the user based on information provided by pecialized assistant."
            " The user is not aware of other assistants, so do not mention them."
            
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

class ToSearchAssistant(BaseModel):
    """Transfers work to a specialized assistant to search for real estates."""

    request: str = Field(
        description="Any additional information or requests from the user regarding their search criteria."
    )

main_agent_runnable = main_agent_prompt | llm.bind_tools(
    [ToSearchAssistant]
)

def route_main_agent(state: State) -> Literal[
    "__end__",
    "search_criteria_agent"
]:
    route = tools_condition(state)
    if route == "__end__":
        return "__end__"
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToSearchAssistant.__name__:
            return "search_criteria_agent"
    raise ValueError("Invalid route")

