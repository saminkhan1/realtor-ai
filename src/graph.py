from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

from src.search_criteria_agent import search_criteria_agent
from src.util import State, Assistant
from src.main_agent import main_agent_runnable, route_main_agent
from src.database_query_node import query_database



def create_graph():
    builder = StateGraph(State)

    # Define nodes: these do the work
    builder.add_node("main_agent", Assistant(main_agent_runnable))
    builder.add_node("search_criteria_agent", search_criteria_agent)
    builder.add_node("query_database", query_database)

    # Define edges: these determine how the control flow moves
    builder.set_entry_point("main_agent")
    builder.add_conditional_edges("main_agent", route_main_agent)
    builder.add_edge("search_criteria_agent", "query_database")
    builder.add_edge("query_database", "main_agent")

    # The checkpointer lets the graph persist its state
    memory = SqliteSaver.from_conn_string(":memory:")
    return builder.compile(checkpointer=memory)


# def create_graph():
#     builder = StateGraph(State)

#     # build main assistant
#     builder.add_node("main_assistant", Assistant(main_assistant_runnable))
#     builder.set_entry_point("main_assistant")
#     builder.add_conditional_edges(
#         "main_assistant",
#         route_main_assistant,
#     )

#     # build search assistant
#     builder.add_node("process_criteria", process_criteria)
#     builder.add_node("search_assistant", Assistant(search_assistant_runnable))
#     builder.add_edge("process_criteria", "search_assistant")

#     builder.add_node("tools", ToolNode(search_tools))
#     builder.add_conditional_edges(
#         "search_assistant",
#         tools_condition,
#     )
#     builder.add_edge("tools", "main_assistant")

#     # The checkpointer lets the graph persist its state
#     memory = SqliteSaver.from_conn_string(":memory:")
#     return builder.compile(checkpointer=memory)
