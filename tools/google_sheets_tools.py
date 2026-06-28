import os
import json
import pandas as pd
import gspread
from typing import Optional, Dict, Any

# Path to the default local mock storage file
MOCK_FILE_PATH = "mock_google_sheet.csv"

# Global session credentials configured by the Streamlit application
g_creds_dict: Optional[Dict[str, Any]] = None

def get_gspread_client(creds_dict: Optional[Dict[str, Any]] = None) -> gspread.Client:
    """
    Authenticate with Google Sheets API.
    Attempts to use the provided dictionary first, then global g_creds_dict,
    then checks for 'service_account.json' locally in the workspace root.
    """
    creds = creds_dict or g_creds_dict
    if creds:
        return gspread.service_account_from_dict(creds)
    
    # Try looking for default local service account file
    default_path = "service_account.json"
    if os.path.exists(default_path):
        return gspread.service_account(filename=default_path)
        
    raise ValueError("Google Sheets credentials not found. Please provide service account JSON.")

def write_df_to_sheet(
    df: pd.DataFrame,
    spreadsheet_id_or_url: str,
    sheet_name: str = "Sheet1",
    creds_dict: Optional[Dict[str, Any]] = None
) -> str:
    """
    Writes a Pandas DataFrame to a Google Sheet. Clears existing data.
    If credentials are not found, it falls back to saving to a local CSV file.
    """
    # Normalize datetime columns to string format so they can be JSON serialized / written to Sheet
    df_write = df.copy()
    for col in df_write.select_dtypes(include=['datetime', 'datetime64']).columns:
        df_write[col] = df_write[col].astype(str)

    try:
        client = get_gspread_client(creds_dict)
        # Open by URL or ID
        if spreadsheet_id_or_url.startswith("https://"):
            sh = client.open_by_url(spreadsheet_id_or_url)
        else:
            sh = client.open_by_key(spreadsheet_id_or_url)
            
        try:
            worksheet = sh.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows="100", cols="20")
            
        worksheet.clear()
        
        # Prepare data: headers + rows
        headers = df_write.columns.tolist()
        # Convert any remaining non-serializable objects to string
        data = df_write.fillna("").values.tolist()
        
        # Write to sheet
        worksheet.update(range_name='A1', values=[headers] + data)
        return f"Successfully wrote {len(df)} rows to Google Sheet '{sheet_name}' in spreadsheet '{sh.title}'."
        
    except Exception as e:
        # Fallback to Mock / Local CSV simulation
        df_write.to_csv(MOCK_FILE_PATH, index=False)
        return (f"Saved to local simulation sheet (mock_google_sheet.csv). "
                f"Reason for sheet connection bypass: {str(e)}")

def read_sheet_to_df(
    spreadsheet_id_or_url: str,
    sheet_name: str = "Sheet1",
    creds_dict: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Reads a Google Sheet into a Pandas DataFrame.
    If credentials or sheet are not available, falls back to reading the mock local CSV file.
    """
    try:
        client = get_gspread_client(creds_dict)
        if spreadsheet_id_or_url.startswith("https://"):
            sh = client.open_by_url(spreadsheet_id_or_url)
        else:
            sh = client.open_by_key(spreadsheet_id_or_url)
            
        worksheet = sh.worksheet(sheet_name)
        records = worksheet.get_all_records()
        
        if not records:
            # Try raw values read if records are empty (e.g. headers only)
            rows = worksheet.get_all_values()
            if rows:
                return pd.DataFrame(rows[1:], columns=rows[0])
            return pd.DataFrame()
            
        return pd.DataFrame(records)
        
    except Exception as e:
        if os.path.exists(MOCK_FILE_PATH):
            return pd.read_csv(MOCK_FILE_PATH)
        raise ValueError(f"Failed to read from Google Sheet and no local mock data exists. Error: {str(e)}")
