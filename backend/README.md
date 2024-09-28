# Real Estate Assistant


Welcome to the AI Agent for Real Estate Professionals. This application is designed to streamline real estate operations, enhancing efficiency through automated communication and task management. The AI agent handles inquiries, schedules appointments, and interacts with clients across multiple platforms, making it an invaluable tool for real estate agents and agencies.

## Key Features

1. **Property Information Inquiry**  
   - Provides detailed property information, including square footage, pricing, condition, and amenities. This ensures potential buyers receive accurate and prompt responses.

2. **Appointment Scheduling**  
   - Integrates with Google Calendar to facilitate the scheduling of property viewings and consultations, allowing clients to book appointments without manual coordination.

3. **Multi-Platform Access**  
   - Accessible through chat-widgets, text messaging, and phone calls, ensuring real-time communication with clients across various channels.

4. **24/7 Availability**  
   - Operates around the clock, ensuring no inquiries go unanswered, reducing missed opportunities, and enhancing client satisfaction.


## Application Workflow

![AI agents graph](graph.png)

### AI Agents Overview

1. **Initialization**  
   - The application begins at the `__start__` node, initializing the AI agent.

2. **Main Interaction Hub**  
   - The `main_agent` node directs users to specific functionalities based on their needs, acting as a central hub for all client interactions.

3. **Property Inquiry Process**  
   - Users seeking property details are routed to the `search_criteria_agent`, which gathers relevant information and queries the `query_database` for detailed property data.

4. **Appointment Management**  
   - Users looking to schedule appointments are guided through the `appointment_agent`, where they can view and confirm available slots using `appointment_tools`. For specialized requests, the `leave_specialized_agent` node is activated.

5. **Human-in-the-Loop**  
   - Agents can sometimes be unreliable or require additional verification for complex tasks. For operations that involve writing or updating data (such as making appointments or altering property details), human input is required to ensure accuracy and correctness. This layer of human approval guarantees that the system is functioning as intended.

6. **Conclusion of Interaction**  
   - After addressing client needs, the interactions return to the `main_agent` for seamless transitions. The workflow concludes at the `__end__` node once all tasks are completed.

## Usage

1. **Chatbot Widget**  
   - Clients can interact through chatbot widgets, which are accessed via WebSockets for real-time communication. This offers an intuitive, web-based interface for inquiries or scheduling appointments.

2. **Text Messaging**  
   - Clients can send text messages to the designated number to interact with the AI agent. The agent will guide them through property inquiries or appointment scheduling.

3. **Phone Interaction**  
   - By calling the provided number, clients can use voice commands to communicate with the AI agent, similar to speaking with a human assistant. Both property inquiries and appointment management are supported through this channel.

## Setup

1. **Install the dependencies**  
   - Run the following command to install required packages:
     ```bash
     pip install -r requirements.txt
     ```

2. **Set up environment variables**  
   - Create a `.env` file in the root directory of the project.
   - Add the necessary environment variables 

3. **Download and set up data**  
   - Download the real estate dataset from [Kaggle](https://www.kaggle.com/datasets/ahmedshahriarsakib/usa-real-estate-dataset) and place it in the `/data` folder.
   - Run `csv_to_sql.py` to convert the CSV file into an SQL database.

4. **Run the main application**  
   - To run the application in the terminal:
     ```bash
     python ai_agent.py
     ```
   - To run the application on a local server for text and call interactions:
     1. Run the `ngrok.exe` file.
     2. Start the server with the following command:
        ```bash
        uvicorn app-retell.server:app --reload
        ```

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

