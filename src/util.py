from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_core.runnables import Runnable, RunnableConfig


# Define the SearchCriteria schema
class SearchCriteria(TypedDict):
    city: Optional[str]
    state: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    max_price: Optional[float]
    min_price: Optional[float]


# Custom reducer function for search_criteria
def update_search_criteria(
    current: SearchCriteria, update: SearchCriteria
) -> SearchCriteria:
    # Merge the update into the current state
    return {**current, **update}


# Define the State schema
class State(TypedDict):
    search_criteria: Annotated[SearchCriteria, update_search_criteria]
    messages: Annotated[list[AnyMessage], add_messages]


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


