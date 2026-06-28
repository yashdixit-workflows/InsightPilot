import pandas as pd

def load_json(file_path: str) -> pd.DataFrame:
    """Loads data from a JSON file into a pandas DataFrame."""
    return pd.read_json(file_path)
