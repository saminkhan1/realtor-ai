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
    # print("search criteria from state", search_criteria)

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

    query += " LIMIT 2"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return {
        "messages": [
            AIMessage(
                content=f"Here are the search results: {results}"
            )
        ]
    }

# @tool
# def search_real_estate(
#     brokered_by: Optional[str] = None,
#     status: Optional[str] = None,
#     price_min: Optional[float] = None,
#     price_max: Optional[float] = None,
#     bed_min: Optional[int] = None,
#     bed_max: Optional[int] = None,
#     bath_min: Optional[int] = None,
#     bath_max: Optional[int] = None,
#     acre_lot_min: Optional[float] = None,
#     acre_lot_max: Optional[float] = None,
#     street: Optional[str] = None,
#     city: Optional[str] = None,
#     state: Optional[str] = None,
#     zip_code: Optional[str] = None,
#     house_size_min: Optional[float] = None,
#     house_size_max: Optional[float] = None,
#     prev_sold_date: Optional[str] = None,
#     limit: int = 3,
# ) -> list[dict]:
#     """Search for real estate properties based on various criteria."""
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()

#     query = "SELECT * FROM real_estate WHERE 1 = 1"
#     params = []

#     if brokered_by:
#         query += " AND brokered_by = ?"
#         params.append(brokered_by)

#     if status:
#         query += " AND status = ?"
#         params.append(status)

#     if price_min is not None:
#         query += " AND price >= ?"
#         params.append(price_min)

#     if price_max is not None:
#         query += " AND price <= ?"
#         params.append(price_max)

#     if bed_min is not None:
#         query += " AND bed >= ?"
#         params.append(bed_min)

#     if bed_max is not None:
#         query += " AND bed <= ?"
#         params.append(bed_max)

#     if bath_min is not None:
#         query += " AND bath >= ?"
#         params.append(bath_min)

#     if bath_max is not None:
#         query += " AND bath <= ?"
#         params.append(bath_max)

#     if acre_lot_min is not None:
#         query += " AND acre_lot >= ?"
#         params.append(acre_lot_min)

#     if acre_lot_max is not None:
#         query += " AND acre_lot <= ?"
#         params.append(acre_lot_max)

#     if street:
#         query += " AND street = ?"
#         params.append(street)

#     if city:
#         query += " AND city = ?"
#         params.append(city)

#     if state:
#         query += " AND state = ?"
#         params.append(state)

#     if zip_code:
#         query += " AND zip_code = ?"
#         params.append(zip_code)

#     if house_size_min is not None:
#         query += " AND house_size >= ?"
#         params.append(house_size_min)

#     if house_size_max is not None:
#         query += " AND house_size <= ?"
#         params.append(house_size_max)

#     if prev_sold_date:
#         query += " AND prev_sold_date = ?"
#         params.append(prev_sold_date)

#     query += " LIMIT ?"
#     params.append(limit)

#     cursor.execute(query, params)
#     rows = cursor.fetchall()
#     column_names = [column[0] for column in cursor.description]
#     results = [dict(zip(column_names, row)) for row in rows]

#     cursor.close()
#     conn.close()

#     return results