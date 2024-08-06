from typing import Annotated, Optional, Callable, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import ToolMessage


# Define the SearchCriteria schema
class SearchCriteria(TypedDict):
    city: Optional[str]
    state: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    max_price: Optional[float]
    min_price: Optional[float]


def update_search_criteria(
    current: SearchCriteria, new: SearchCriteria
) -> SearchCriteria:
    result = current.copy()
    
    city_in_new = "city" in new
    state_in_new = "state" in new

    if city_in_new and state_in_new:
        result["city"] = new["city"]
        result["state"] = new["state"]
    # if only "city" in new criteria, remove the previous "state" in criteria
    # to avoid errors such as - city: Chicago, state: New York
    # where previous criteria had - city: New York, state: New York
    # and new criteria had - city: Chiaco, but no state
    elif city_in_new:
        result["city"] = new["city"]
        result.pop("state", None)
    elif state_in_new:
        result["state"] = new["state"]
        result.pop("city", None)
    
    # Merge the remaining criteria
    for key in ["min_bedroom", "min_bathroom", "max_price", "min_price"]:
        if key in new:
            result[key] = new[key]
    
    return result


# Define the State schema
class State(TypedDict):
    search_criteria: Annotated[SearchCriteria, update_search_criteria]
    messages: Annotated[list[AnyMessage], add_messages]

