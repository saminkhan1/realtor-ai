import os
import pandas as pd
from sqlalchemy import create_engine, text

# Get the current directory of the script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Relative path to your CSV file
csv_file_path = os.path.join(current_directory, "realtor-data.csv")

# Adjust the data types as needed
data = pd.read_csv(csv_file_path)
data["prev_sold_date"] = pd.to_datetime(data["prev_sold_date"], errors="coerce")

# Relative path to the SQLite database file
sqlite_db_path = os.path.join(current_directory, "real_estate_data.db")

# SQLite Database Connection
engine = create_engine(f"sqlite:///{sqlite_db_path}", echo=False)

# SQL Table Creation (excluding certain columns)
sql_create_table = """
CREATE TABLE IF NOT EXISTS real_estate (
    price DECIMAL(15, 2),
    bed INT,
    bath INT,
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10)
);
"""
with engine.connect() as connection:
    connection.execute(text(sql_create_table))

# Insert data into SQL table (only with the included columns)
included_columns = ["price", "bed", "bath", "city", "state", "zip_code"]
data_included = data[included_columns]
data_included.to_sql("real_estate", engine, if_exists="replace", index=False)

print("Data inserted successfully.")
