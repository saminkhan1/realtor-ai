import uuid
import os
from dotenv import load_dotenv
from IPython.display import Image, display
from langchain_core.messages import ToolMessage, HumanMessage


from src.graph import create_graph

def get_human_approval(tool_call):
    return input("Do you approve of the above actions? Type 'yes' to continue, otherwise provide your reasoning:\n\n").strip().lower()


def process_single_question(graph, question, config):
    """Process a single question and print the response."""
    
    for event in graph.stream(
        {"messages": [HumanMessage(content=question)]}, config, stream_mode="values"):
        if "messages" in event:
            event["messages"][-1].pretty_print()

    snapshot = graph.get_state(config)

    while snapshot.next:
        # Get the last message and its tool call information
        last_message = snapshot.values["messages"][-1]
        if last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                # Extract human-readable tool info
                user_input = get_human_approval(tool_call)
            
                if user_input.strip().lower() == "yes":
                    # Continue with the process
                    result = graph.invoke(None, config)
                else:
                    # Provide reasoning for denying the action
                    result = graph.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                    content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                
                # Update the snapshot to reflect the new state
                snapshot = graph.get_state(config)

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
        "I want to book an appointment to view the first property on Sept 28 at 10 am.",
        "Change my appointment on Sept 14 to Sept 15.",
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
