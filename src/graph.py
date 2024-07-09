from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from src.assistant_main import Assistant, ToSearchAssistant, main_assistant_runnable
from src.assistant_search import process_criteria, search_tools, search_assistant_runnable, SearchAssistant
from src.state import State
from typing import Literal

    
def route_main_assistant(state: State) -> Literal[
    "__end__",
    "process_criteria"
]:
    route = tools_condition(state)
    if route == "__end__":
        return "__end__"
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToSearchAssistant.__name__:
            return "process_criteria"
    raise ValueError("Invalid route")


def create_graph():
    builder = StateGraph(State)

    # build main assistant
    builder.add_node("main_assistant", Assistant(main_assistant_runnable))
    builder.set_entry_point("main_assistant")
    builder.add_conditional_edges(
        "main_assistant",
        route_main_assistant,
    )

    # build search assistant
    builder.add_node("process_criteria", process_criteria)
    builder.add_node("search_assistant", SearchAssistant(search_assistant_runnable))
    builder.add_edge("process_criteria", "search_assistant")

    builder.add_node("tools", ToolNode(search_tools))
    builder.add_conditional_edges(
        "search_assistant",
        tools_condition,
    )
    builder.add_edge("tools", "main_assistant")

    # The checkpointer lets the graph persist its state
    memory = SqliteSaver.from_conn_string(":memory:")
    return builder.compile(checkpointer=memory)
