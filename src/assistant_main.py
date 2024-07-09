from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from src.state import State
from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel

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

class ToSearchAssistant(BaseModel):
    """Transfers work to a specialized assistant to search for real estates."""

    # request: str = Field(
    #     description="Any additional information or requests from the user regarding their search criteria."
    # )

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "request": "The user is interested in outdoor activities and scenic views.",
    #         }
    #     }

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")


main_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful real estate assistant."
            " Your primary role is to identify customer's intent"
            " and delegate the task to the appropriate specialized assistant by invoking the corresponding tool"
            " The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

main_assistant_runnable = main_assistant_prompt | llm.bind_tools(
    [ToSearchAssistant]
)
