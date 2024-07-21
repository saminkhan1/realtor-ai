from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages.utils import AnyMessage  # Updated import


# Define the SearchCriteria schema
class SearchCriteria(TypedDict):
    """Stores search criteria for a real estate search."""
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
