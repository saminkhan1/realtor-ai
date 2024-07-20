import sqlite3
import os
from langchain_core.messages import AIMessage
from src.util import State
import sqlite3
import os


def query_database(state: State):
    search_criteria = state["search_criteria"]

    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "real_estate_data.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM real_estate WHERE 1 = 1"
    params = []

    # Define valid criteria keys and their corresponding SQL column names
    valid_criteria = {
        "city": "city",
        "state": "state",
        "min_bedroom": "bed",
        "min_bathroom": "bath",
        "max_price": "price",
        "min_price": "price",
    }

    for key, value in search_criteria.items():
        if value is not None:
            sql_column = valid_criteria.get(key)
            if sql_column:
                if key in ["min_bedroom", "min_bathroom"]:
                    query += f" AND {sql_column} >= ?"
                elif key in ["max_price", "min_price"]:
                    operator = "<=" if "max" in key else ">="
                    query += f" AND {sql_column} {operator} ?"
                else:
                    query += f" AND {sql_column} = ?"
                params.append(value)
            else:
                # Handle unexpected criteria keys
                print(f"Unexpected criteria key: {key}")

    query += " LIMIT 2"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return {"messages": [AIMessage(content=f"Here are the search results: {results}")]}
