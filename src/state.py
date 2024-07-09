from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


# Define the SearchCriteria schema
class SearchCriteria(TypedDict):
    city: Optional[str]
    state_location: Optional[str] #changing it to state_location, to avoid confusion with langgraph's state
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
