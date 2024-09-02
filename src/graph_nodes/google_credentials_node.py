from langchain_core.messages import ToolMessage

from src.util.g_cal_functions import get_credentials
from src.util.state import State

def retrieve_credentials(state: State):
    credentials  = get_credentials()

    last_tool_call = state["messages"][-1].tool_calls[0]
    tool_call_id = last_tool_call["id"]

    print(credentials)

    return {
        "messages": [ToolMessage(
            content="Retrieved Google credentials.",
            tool_call_id=tool_call_id
        )],
        "google_credentials": credentials.to_json(),
    }
