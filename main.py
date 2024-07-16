import uuid
import os
from dotenv import load_dotenv
from src.graph import create_graph


def main():
    graph = create_graph()
    thread_id = str(uuid.uuid4())
    # Example usage of the graph
    config = {
        "configurable": {
            "user_id": "user_123",
            "thread_id": thread_id,
        }
    }

    questions = [
        "What properties are available in New York?",
        # "Show me houses with at least 3 bedrooms and 2 bathrooms.",
        # "Do you have any properties under $500,000?",
        "What properties are available in Chicago?",
    ]

    for question in questions:
        events = graph.stream(
            {"messages": ("user", question)}, config, stream_mode="values"
        )
        # for event in events:
        #     print(event)
        for event in events:
            if "messages" in event:
                event["messages"][-1].pretty_print()


if __name__ == "__main__":
    load_dotenv()
    # Now you can access the environment variables directly
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Real Estate Assistant Project"
    # Set other environment variables as needed
    main()
