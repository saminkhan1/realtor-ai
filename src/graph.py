from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph
from src.search_criteria_agent import search_criteria_agent
from src.state import State


def create_graph():
    builder = StateGraph(State)

    # Define nodes: these do the work
    builder.add_node("search_criteria_agent", search_criteria_agent)
    # TODO: add node for db_query_agent
    # TODO: add tool db_query_agent

    # Define edges: these determine how the control flow moves
    builder.set_entry_point("search_criteria_agent")
    # TODO: add edges between search_criteria_agent and db_query_agent
    # TODO: add edges between tool node and db_query_agent
    builder.set_finish_point("search_criteria_agent")

    # The checkpointer lets the graph persist its state
    memory = SqliteSaver.from_conn_string(":memory:")
    return builder.compile(checkpointer=memory)
