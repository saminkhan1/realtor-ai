# Real Estate Assistant

## Project Structure

- `data/`: Directory for database files.
- `scripts/`: Directory for SQL scripts and other utility scripts.
- `src/`: Directory for the main source code of the project.
- `main.py`: The entry point of the application.
- `requirements.txt`: Lists the Python dependencies required for the project.
- `README.md`: Documentation for the project.

## Setup

1. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Create a `.env` file in the root directory of the project.
   - Add the following environment variables to the `.env` file:
     ```
     LANGCHAIN_API_KEY=
     LANGCHAIN_API_KEY=
     LANGCHAIN_TRACING_V2=true
     LANGCHAIN_PROJECT=Real Estate Assistant Project
     ```
   - Replace the empty values with your API keys obtained from the respective services.
   - Ensure that the `.env` file is included in the project's `.gitignore` to prevent sensitive information from being committed to version control.

4. **Download and setup data**
   - download csv file of realestate data from https://www.kaggle.com/datasets/ahmedshahriarsakib/usa-real-estate-dataset to `/data` folder
   - use `csv_to_sql.py` and run the file to convert csv to sql database

5. **Run the main application:**

   run ngrok.exe file, then on terminal run
   ```bash
   uvicorn app-retell.server:app --reload
   ```

## Description

This project implements a real estate assistant that helps users search for properties based on various criteria. The assistant is built using Python and leverages natural language processing (NLP) techniques to understand user queries and provide relevant responses.

The main components of the project include:
- **Database Management:** The `data/` directory contains SQLite database files (`real_estate_data.db` and `realtor-data.csv`) to store real estate property data.
- **Tools:** The `tools/` directory holds AI agent tools like `search_real_estate` in `real_estate_tool.py` for property search functionality.
- **Source Code:** The `src/` directory contains the main source code of the project, including the agent logic (`agent.py`), state management (`state.py`), graph definition (`graph.py`), and initialization (`__init__.py`).
- **Entry Point:** The `main.py` file serves as the entry point of the application, orchestrating the interaction with the real estate assistant.
- **Dependencies:** The `requirements.txt` file lists all Python dependencies required for the project.


## Usage

To use the real estate assistant, follow the setup instructions provided above. Once the environment is set up, run the `main.py` script to interact with the assistant. The assistant can understand natural language queries related to real estate properties and provide relevant information based on the data stored in the database.

## Contributions

Contributions to this project are welcome. If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request on the GitHub repository.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
