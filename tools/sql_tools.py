import sqlite3
import pandas as pd

def load_sql(database_path: str, query: str) -> pd.DataFrame:
    """Loads data from a SQLite database via SQL query into a pandas DataFrame.
    
    Args:
        database_path: The file path to the SQLite database file.
        query: The SQL query string to select the data.
    """
    conn = sqlite3.connect(database_path)
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df
