from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnableConfig
from tools.real_estate_tool import search_real_estate
from src.state import State
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

def process_criteria(state: State):
    print("process_criteria")
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    # hard code a criteria for testing
    processed_criteria = {
        "city": "New York City",
        "bedrooms": 3,
        "bathrooms": 2,
        "max_price": 500000
    }
    return {
        "messages": [
            ToolMessage(
                content="process_criteria",
                tool_call_id=tool_call_id
            )
        ],
        "search_criteria": processed_criteria
    }


class SearchAssistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            # force add processed criteria to the state
            search_criteria = state.get("search_criteria", None)
            query = f"The user wishes to look for real estates with the following search criteria {search_criteria}"
            messages_with_query = state["messages"] + [("user", query)]
            state = {**state, "messages": messages_with_query}
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

re_search_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for searching real estates."
            " The primary assistant delegates work to you whenever the user needs help updating their bookings. "
            " Use the provided tools to search for properties. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. Always consider the entire conversation history. "
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())


search_tools = [
    search_real_estate,
    # Add other real estate tools if needed
]

search_assistant_runnable = re_search_assistant_prompt | llm.bind_tools(
    search_tools
)
