from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from src.agent import Assistant, re_search_assistant_runnable, re_search_tools
from src.state import State


def create_graph():
    builder = StateGraph(State)

    # Define nodes: these do the work
    builder.add_node("re_assistant", Assistant(re_search_assistant_runnable))
    builder.add_node("tools", ToolNode(re_search_tools))

    # Define edges: these determine how the control flow moves
    builder.set_entry_point("re_assistant")
    builder.add_conditional_edges(
        "re_assistant",
        tools_condition,
    )
    builder.add_edge("tools", "re_assistant")

    # The checkpointer lets the graph persist its state
    memory = SqliteSaver.from_conn_string(":memory:")
    return builder.compile(checkpointer=memory)
