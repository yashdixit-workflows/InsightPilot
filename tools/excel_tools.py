import pandas as pd

def load_excel(file_path: str, sheet_name = 0) -> pd.DataFrame:
    """Loads data from an Excel file into a pandas DataFrame."""
    return pd.read_excel(file_path, sheet_name=sheet_name)
