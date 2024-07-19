import sqlite3
import os
from langchain_core.messages import AIMessage
from src.util import State



def build_query(search_criteria):
    """Builds a SQL query based on the search criteria."""
    query = "SELECT * FROM real_estate WHERE 1=1"
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

    query += " LIMIT 3"
    return query, params


def query_database(state: State):
    search_criteria = state.get("search_criteria", {})
    db_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "real_estate_data.db"
    )

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query, params = build_query(search_criteria)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        results = [dict(zip(column_names, row)) for row in rows]
    except sqlite3.Error as e:
        results = {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

    return {"messages": [AIMessage(content=f"Here are the search results: {results}")]}
