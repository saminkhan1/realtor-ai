from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from tools.real_estate_tool import search_real_estate
from src.state import State
from dotenv import load_dotenv

load_dotenv()


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


llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

re_search_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful real estate assistant. Use the provided tools to search for properties, "
            "and provide the necessary information to assist the user's queries. When searching, be persistent. "
            "Ensure that follow-up questions are dependent on the criteria/arguments from all previous messages unless explicitly stated otherwise."
            "Expand your query bounds if the first search returns no results. Always consider the entire conversation history. "
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())


re_search_tools = [
    search_real_estate,
    # Add other real estate tools if needed
]

re_search_assistant_runnable = re_search_assistant_prompt | llm.bind_tools(
    re_search_tools
)
