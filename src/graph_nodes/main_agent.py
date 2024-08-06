from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langgraph.prebuilt import tools_condition
from typing import Literal

from src.util.state import State
from src.util.prompts import system_prompt, agent_prompt
from src.util.general_tools import ToSearchAgent, ToAppointmentAgent

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")

main_agent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt + agent_prompt),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

main_tools = [ToSearchAgent, ToAppointmentAgent]

main_agent_runnable = main_agent_prompt | llm.bind_tools(main_tools)


def route_main_agent(state: State) -> Literal[
    "__end__",
    "search_criteria_agent",
    "appointment_agent"
]:
    route = tools_condition(state)
    if route == "__end__":
        return "__end__"
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToSearchAgent.__name__:
            return "search_criteria_agent"
        if tool_calls[0]["name"] == ToAppointmentAgent.__name__:
            return "appointment_agent"
    raise ValueError("Invalid route")