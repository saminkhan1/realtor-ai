import uuid
import os
from dotenv import load_dotenv
from IPython.display import Image, display


from src.graph import create_graph

def process_single_question(graph, question, config):
    """Process a single question and print the response."""
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )

    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()

    print()  # Add a blank line for better readability between questions

def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Real Estate Assistant Project"

    graph = create_graph()
    
    # try:
    #     with open("graph.png", "wb") as f:
    #         f.write(graph.get_graph().draw_mermaid_png())
    # except Exception:
    #     # This requires some extra dependencies and is optional
    #     pass
    
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "user_id": "user_123",
            "thread_id": thread_id,
        }
    }

    print("Choose an option:")
    print("1. Ask predefined questions")
    print("2. Ask custom questions interactively")

    choice = input("Enter your choice (1 or 2): ").strip()

    if choice == "1":
        questions = [
        "I want to book an appointment to view the apartment on Sept 3 at 10 am.",
        "Change my appointment on Sept 3 to Sept 4.",
        "What properties are available in New York?",
        "Show me houses with at least 3 bedrooms and 2 bathrooms.",
        "Do you have any properties under $500,000?",
        ]
        for question in questions:
            process_single_question(graph, question, config)
    elif choice == "2":
        print("Interactive mode: Enter your questions (type 'exit' to stop).")
        while True:
            question = input("Question: ").strip()
            if question.lower() == 'exit':
                print("Exiting interactive mode.")
                break
            process_single_question(graph, question, config)
    else:
        print("Invalid choice. Please select 1 or 2.")

if __name__ == "__main__":
    main()
