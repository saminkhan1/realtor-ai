from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda

from src.util.state import State

class Assistant:
    def __init__(self, runnable: Runnable, append_tool_message: bool = False):
        self.runnable = runnable
        self.append_tool_message = append_tool_message

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            user_id = config.get("user_id", None)
            state = {**state, "user_info": user_id}

            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and self.append_tool_message:
                tool_call_id = last_message.tool_calls[0]["id"]
                tool_message = ToolMessage(
                    content="Entering specialized agent.", tool_call_id=tool_call_id
                )
                state["messages"].append(tool_message)
                
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

def back_to_main(state: State) -> dict:
    last_tool_call = state["messages"][-1].tool_calls[0]
    tool_call_id = last_tool_call["id"]

    return {
        "messages": [
            ToolMessage(
                content="Back to main agent.", tool_call_id=tool_call_id
            ),
        ],
    }

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

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