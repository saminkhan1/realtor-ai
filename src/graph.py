from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

from src.search_criteria_agent import search_criteria_agent
from src.util import State, Assistant
from src.main_agent import main_agent_runnable, route_main_agent
from src.database_query_node import query_database


def create_graph():
    """Creates a graph of nodes and edges."""
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
