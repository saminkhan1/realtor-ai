from typing import Annotated, Optional, Callable
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig

from src.state import State


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            user_id = config.get("user_id", None)
            state = {**state, "user_info": user_id}
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


# def create_entry_node(assistant_name: str) -> Callable:
#     def entry_node(state: State) -> dict:
#         tool_call_id = state["messages"][-1].tool_calls[0]["id"]
#         return {
#             "messages": [
#                 ToolMessage(
#                     content=f"Entering speciallized {assistant_name}",
#                     # " Do not mention who you are. Act only as the proxy assistant.",
#                     tool_call_id=tool_call_id,
#                 )
#             ]
#         }
    
#     return entry_node