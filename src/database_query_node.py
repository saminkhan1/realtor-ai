from langchain_core.messages import AIMessage
from src.util import State
import sqlite3
import os

def process_criteria(criteria_key, criteria_value, query, params):
    query += f" AND {criteria_key} = ?"
    params.append(criteria_value)
    return (query, params)

def query_database(state: State):
    search_criteria = state["search_criteria"]

    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "real_estate_data.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    city = search_criteria.get("city", None)
    state = search_criteria.get("state", None)
    min_bedroom = search_criteria.get("min_bedroom", None)
    min_bathroom = search_criteria.get("min_bathroom", None)
    max_price = search_criteria.get("max_price", None)
    min_price = search_criteria.get("min_price", None)

    query = "SELECT * FROM real_estate WHERE 1 = 1"
    params = []

    if city:
        query += " AND city = ?"
        params.append(city)    

    if state:
        query += " AND state = ?"
        params.append(state)

    if min_bedroom is not None:
        query += " AND bed >= ?"
        params.append(min_bedroom)
    
    if min_bathroom is not None:
        query += " AND bath >= ?"
        params.append(min_bathroom)
    
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    query += " LIMIT 3"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return {"messages": [AIMessage(content=f"Here are the search results: {results}")]}