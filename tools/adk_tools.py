import pandas as pd
from agents.data_agent import DataAgent
from agents.kpi_agent import KPIAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent

# Load tools from sub-modules
from tools.csv_tools import load_csv
from tools.excel_tools import load_excel
from tools.json_tools import load_json
from tools.sql_tools import load_sql
from tools.google_sheets_tools import read_sheet_to_df, write_df_to_sheet

# Shared active dataframe state
_active_df = None
_active_datasets = {}


def _resolve_file_path(file_path: str) -> str:
    """
    Finds a file in the workspace or streamlit session state.
    Returns the absolute path if found on disk, or the filename if found in streamlit session state.
    """
    import os
    import sys
    
    # 1. Check Streamlit session state first
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "session_state") and "datasets" in st.session_state:
                filename = os.path.basename(file_path).lower()
                for k in st.session_state.datasets.keys():
                    if k.lower() == filename or k.lower() == file_path.lower():
                        return k  # Return the exact key in session_state.datasets
        except Exception:
            pass

    # 2. Check direct path
    if os.path.exists(file_path):
        return os.path.abspath(file_path)

    # 3. Recursive search in workspace (excluding virtual environments, caches, etc.)
    filename = os.path.basename(file_path).lower()
    exclude_dirs = {".venv", "__pycache__", ".vscode", ".git", ".agents", ".gemini", "node_modules"}
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.lower() == filename:
                return os.path.abspath(os.path.join(root, f))
                
    return None


def consolidate_datasets() -> pd.DataFrame:
    """Consolidates all datasets in _active_datasets by concatenating or merging them."""
    global _active_datasets
    if not _active_datasets:
        return None
        
    dfs = list(_active_datasets.values())
    if len(dfs) == 1:
        return dfs[0]
        
    # Sort dataframes by length descending (fact table first)
    sorted_items = sorted(_active_datasets.items(), key=lambda item: len(item[1]), reverse=True)
    
    # Start with the largest dataset as the base
    base_name, base_df = sorted_items[0]
    consolidated_df = base_df.copy()
    
    for name, df in sorted_items[1:]:
        # 1. Check if schemas are identical (ignore column ordering)
        if set(consolidated_df.columns) == set(df.columns):
            try:
                consolidated_df = pd.concat([consolidated_df, df], ignore_index=True)
                continue
            except Exception:
                pass
                
        # 2. Check for common columns to merge
        common_cols = list(set(consolidated_df.columns) & set(df.columns))
        if common_cols:
            try:
                # Merge lookup/dimension table into the base dataframe
                # Using 'left' join to preserve all records of the base table
                consolidated_df = pd.merge(consolidated_df, df, on=common_cols, how="left")
            except Exception:
                pass
            
    return consolidated_df


def _clean_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    """Helper to clean the dataframe if it contains the sales columns."""
    required_cols = ["Order Date", "Ship Date", "Sales", "Units", "Gross Profit", "Cost"]
    if all(col in df.columns for col in required_cols):
        df = df.copy()
        df.drop_duplicates(inplace=True)
        df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, errors="coerce")
        numeric_cols = ["Sales", "Units", "Gross Profit", "Cost"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=numeric_cols, inplace=True)
    return df


def load_data_from_csv(file_path: str, clear_existing: bool = False) -> str:
    """Loads a CSV dataset (comma-separated lists allowed) into the active workspace."""
    global _active_df, _active_datasets
    import sys
    import os
    
    if clear_existing:
        _active_datasets.clear()
        
    loaded_names = []
    failed_names = []
    
    paths = [p.strip() for p in file_path.split(",") if p.strip()]
    
    for path in paths:
        resolved = _resolve_file_path(path)
        if resolved is None:
            failed_names.append(f"'{path}' (not found)")
            continue
            
        # Streamlit state loading
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state") and "datasets" in st.session_state and resolved in st.session_state.datasets:
                    df = st.session_state.datasets[resolved]
                    _active_datasets[resolved] = df
                    loaded_names.append(resolved)
                    continue
            except Exception:
                pass
                
        try:
            df = load_csv(resolved)
            name = os.path.basename(resolved)
            _active_datasets[name] = df
            loaded_names.append(name)
        except Exception as e:
            failed_names.append(f"'{path}' ({str(e)})")
            
    _active_df = consolidate_datasets()
    
    # Sync to Streamlit session state
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "session_state"):
                if "datasets" not in st.session_state:
                    st.session_state.datasets = {}
                for name, df in _active_datasets.items():
                    st.session_state.datasets[name] = df
                st.session_state.active_names = list(_active_datasets.keys())
                st.session_state.active_name = ", ".join(st.session_state.active_names)
        except Exception:
            pass
            
    status_msg = ""
    if loaded_names:
        status_msg += f"Successfully loaded CSV data from '{', '.join(loaded_names)}'."
    if failed_names:
        status_msg += f" Failed to load: {', '.join(failed_names)}."
    if _active_df is not None:
        status_msg += f" Combined row count: {len(_active_df)}."
    return status_msg


def load_data_from_excel(file_path: str, sheet_name = 0, clear_existing: bool = False) -> str:
    """Loads an Excel dataset into the active workspace."""
    global _active_df, _active_datasets
    import sys
    import os
    
    if clear_existing:
        _active_datasets.clear()
        
    resolved = _resolve_file_path(file_path)
    if resolved is None:
        return f"Failed to load Excel: '{file_path}' not found."
        
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "session_state") and "datasets" in st.session_state and resolved in st.session_state.datasets:
                df = st.session_state.datasets[resolved]
                _active_datasets[resolved] = df
                _active_df = consolidate_datasets()
                st.session_state.active_names = list(_active_datasets.keys())
                st.session_state.active_name = ", ".join(st.session_state.active_names)
                return f"Successfully loaded Excel data from '{resolved}'."
        except Exception:
            pass
            
    try:
        df = load_excel(resolved, sheet_name=sheet_name)
        name = os.path.basename(resolved)
        _active_datasets[name] = df
        _active_df = consolidate_datasets()
        
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "datasets" not in st.session_state:
                        st.session_state.datasets = {}
                    st.session_state.datasets[name] = df
                    st.session_state.active_names = list(_active_datasets.keys())
                    st.session_state.active_name = ", ".join(st.session_state.active_names)
            except Exception:
                pass
                
        return f"Successfully loaded Excel data from '{name}' (sheet: {sheet_name}). Rows: {len(df)}, Columns: {list(df.columns)}"
    except Exception as e:
        return f"Failed to load Excel: {str(e)}"


def load_data_from_json(file_path: str, clear_existing: bool = False) -> str:
    """Loads a JSON dataset into the active workspace."""
    global _active_df, _active_datasets
    import sys
    import os
    
    if clear_existing:
        _active_datasets.clear()
        
    resolved = _resolve_file_path(file_path)
    if resolved is None:
        return f"Failed to load JSON: '{file_path}' not found."
        
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "session_state") and "datasets" in st.session_state and resolved in st.session_state.datasets:
                df = st.session_state.datasets[resolved]
                _active_datasets[resolved] = df
                _active_df = consolidate_datasets()
                st.session_state.active_names = list(_active_datasets.keys())
                st.session_state.active_name = ", ".join(st.session_state.active_names)
                return f"Successfully loaded JSON data from '{resolved}'."
        except Exception:
            pass
            
    try:
        df = load_json(resolved)
        name = os.path.basename(resolved)
        _active_datasets[name] = df
        _active_df = consolidate_datasets()
        
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "datasets" not in st.session_state:
                        st.session_state.datasets = {}
                    st.session_state.datasets[name] = df
                    st.session_state.active_names = list(_active_datasets.keys())
                    st.session_state.active_name = ", ".join(st.session_state.active_names)
            except Exception:
                pass
                
        return f"Successfully loaded JSON data from '{name}'. Rows: {len(df)}, Columns: {list(df.columns)}"
    except Exception as e:
        return f"Failed to load JSON: {str(e)}"


def load_data_from_sql(database_path: str, query: str, clear_existing: bool = False) -> str:
    """Loads data from a SQLite database via SQL query into the active workspace."""
    global _active_df, _active_datasets
    import sys
    import os
    
    if clear_existing:
        _active_datasets.clear()
        
    resolved = _resolve_file_path(database_path)
    if resolved is None:
        return f"Failed to load SQL: Database '{database_path}' not found."
        
    try:
        df = load_sql(resolved, query)
        name = f"SQL: {os.path.basename(resolved)}"
        _active_datasets[name] = df
        _active_df = consolidate_datasets()
        
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "datasets" not in st.session_state:
                        st.session_state.datasets = {}
                    st.session_state.datasets[name] = df
                    st.session_state.active_names = list(_active_datasets.keys())
                    st.session_state.active_name = ", ".join(st.session_state.active_names)
            except Exception:
                pass
                
        return f"Successfully loaded SQL data. Rows: {len(df)}, Columns: {list(df.columns)}"
    except Exception as e:
        return f"Failed to load SQL: {str(e)}"


def load_sales_data():
    """Loads the default sales dataset."""
    global _active_df, _active_datasets
    try:
        resolved = _resolve_file_path("Sales_Data.csv")
        if resolved is None:
            return "Failed to load sales data: Sales_Data.csv not found."
        agent = DataAgent()
        df = agent.load_and_clean(resolved)
        name = "Sales_Data.csv"
        _active_datasets[name] = df
        _active_df = consolidate_datasets()
        
        import sys
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "datasets" not in st.session_state:
                        st.session_state.datasets = {}
                    st.session_state.datasets["Sales_Data.csv (Default)"] = df
                    st.session_state.active_names = ["Sales_Data.csv (Default)"]
                    st.session_state.active_name = "Sales_Data.csv (Default)"
            except Exception:
                pass
                
        return "Sales data loaded successfully."
    except Exception as e:
        return f"Failed to load sales data: {str(e)}"


def calculate_kpis():
    """Calculates Key Performance Indicators (KPIs) from the active data source."""
    global _active_df
    if _active_df is None:
        load_sales_data()
    
    kpi_agent = KPIAgent()
    df_cleaned = _clean_if_needed(_active_df)
    return kpi_agent.calculate_kpis(df_cleaned)


def generate_insights():
    """Generates business insights from the active data source."""
    global _active_df
    if _active_df is None:
        load_sales_data()
    
    insight_agent = InsightAgent()
    df_cleaned = _clean_if_needed(_active_df)
    return insight_agent.generate_insights(df_cleaned)


def generate_recommendations():
    """Generates strategic recommendations from the active data source."""
    global _active_df
    if _active_df is None:
        load_sales_data()
    
    recommendation_agent = RecommendationAgent()
    df_cleaned = _clean_if_needed(_active_df)
    return recommendation_agent.generate_recommendations(df_cleaned)


def load_data_from_google_sheet(spreadsheet_id: str, sheet_name: str = "Sheet1", clear_existing: bool = False) -> str:
    """Loads a dataset from a Google Sheet as the active data source for analysis."""
    global _active_df, _active_datasets
    import sys
    
    if clear_existing:
        _active_datasets.clear()
        
    try:
        df = read_sheet_to_df(spreadsheet_id, sheet_name=sheet_name)
        name = f"Google Sheet: {sheet_name}"
        _active_datasets[name] = df
        _active_df = consolidate_datasets()
        
        if "streamlit" in sys.modules:
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "datasets" not in st.session_state:
                        st.session_state.datasets = {}
                    st.session_state.datasets[name] = df
                    st.session_state.active_names = list(_active_datasets.keys())
                    st.session_state.active_name = ", ".join(st.session_state.active_names)
            except Exception:
                pass
                
        return f"Successfully loaded data from Google Sheet (sheet: {sheet_name}). Rows: {len(df)}, Columns: {list(df.columns)}"
    except Exception as e:
        return f"Failed to load Google Sheet: {str(e)}"


def save_data_to_google_sheet(spreadsheet_id: str, sheet_name: str = "Sheet1") -> str:
    """Saves the currently active dataset to a Google Sheet."""
    global _active_df
    if _active_df is None:
        return "No active data source loaded to save."
    try:
        res = write_df_to_sheet(_active_df, spreadsheet_id, sheet_name=sheet_name)
        return res
    except Exception as e:
        return f"Failed to save to Google Sheet: {str(e)}"


def get_dataset_schema(dataset_name: str = None) -> str:
    """Returns the schema (columns and data types) of the specified dataset, or the active one if none specified."""
    global _active_df, _active_datasets
    
    df = _active_df
    resolved_name = None
    if dataset_name:
        for name in _active_datasets.keys():
            if name.lower() == dataset_name.lower():
                resolved_name = name
                break
        if resolved_name:
            df = _active_datasets[resolved_name]
        else:
            return f"Error: Dataset '{dataset_name}' not found. Available datasets: {list(_active_datasets.keys())}"
            
    if df is None:
        load_sales_data()
        df = _active_df
        
    if df is None:
        return "No dataset loaded."
    
    dtypes_str = "\n".join([f"- {col} ({dtype})" for col, dtype in df.dtypes.items()])
    name_prefix = f"Dataset '{resolved_name}'" if dataset_name and resolved_name else "Active dataset"
    return f"{name_prefix} columns and data types:\n{dtypes_str}"


def get_top_categories(group_by_column: str, metric_column: str, limit: int = 15, dataset_name: str = None) -> str:
    """
    Groups the dataset by a categorical column and aggregates a numeric column.
    Returns the top categories. Specifying dataset_name queries a specific loaded dataset.
    """
    global _active_df, _active_datasets
    
    df = _active_df
    resolved_name = None
    if dataset_name:
        for name in _active_datasets.keys():
            if name.lower() == dataset_name.lower():
                resolved_name = name
                break
        if resolved_name:
            df = _active_datasets[resolved_name]
        else:
            return f"Error: Dataset '{dataset_name}' not found. Available datasets: {list(_active_datasets.keys())}"
            
    if df is None:
        load_sales_data()
        df = _active_df
        
    if df is None:
        return "No dataset loaded."
        
    if group_by_column not in df.columns:
        return f"Error: Grouping column '{group_by_column}' not found. Available columns: {list(df.columns)}"
    if metric_column not in df.columns:
        return f"Error: Metric column '{metric_column}' not found. Available columns: {list(df.columns)}"
        
    try:
        if pd.api.types.is_numeric_dtype(df[metric_column]):
            grouped = df.groupby(group_by_column)[metric_column].sum().reset_index()
        else:
            grouped = df.groupby(group_by_column)[metric_column].count().reset_index()
            
        grouped = grouped.sort_values(by=metric_column, ascending=False).head(limit)
        
        name_prefix = f"Dataset '{resolved_name or 'active'}'"
        res = f"Top {limit} categories of '{group_by_column}' by '{metric_column}' in {name_prefix}:\n"
        for idx, row in grouped.iterrows():
            res += f"- {row[group_by_column]}: {row[metric_column]:,.2f}\n"
        return res
    except Exception as e:
        return f"Error running aggregation: {str(e)}"


def get_product_profit_margins(limit: int = 15, dataset_name: str = None) -> str:
    """
    Calculates sales, units sold, and profit margin per product for the dataset,
    and returns a summary table. Specifying dataset_name queries a specific loaded dataset.
    """
    global _active_df, _active_datasets
    
    df = _active_df
    resolved_name = None
    if dataset_name:
        for name in _active_datasets.keys():
            if name.lower() == dataset_name.lower():
                resolved_name = name
                break
        if resolved_name:
            df = _active_datasets[resolved_name]
        else:
            return f"Error: Dataset '{dataset_name}' not found. Available datasets: {list(_active_datasets.keys())}"
            
    if df is None:
        load_sales_data()
        df = _active_df
        
    if df is None:
        return "No dataset loaded."
        
    prod_col = None
    for col in ["Product Name", "Product", "Item", "Name"]:
        if col in df.columns:
            prod_col = col
            break
    if prod_col is None:
        cat_cols = df.select_dtypes(include=['object']).columns.tolist()
        if cat_cols:
            prod_col = cat_cols[0]
        else:
            return "Error: Could not identify a product or categorical column for margin analysis."
            
    sales_col = None
    for col in ["Sales", "Revenue", "Amount"]:
        if col in df.columns:
            sales_col = col
            break
            
    profit_col = None
    for col in ["Gross Profit", "Profit", "Margin"]:
        if col in df.columns:
            profit_col = col
            break
            
    units_col = None
    for col in ["Units", "Quantity", "Qty"]:
        if col in df.columns:
            units_col = col
            break
            
    if not sales_col or not profit_col:
        return f"Error: Margin analysis requires Sales and Gross Profit columns. Found: {list(df.columns)}"
        
    try:
        agg_dict = {sales_col: "sum", profit_col: "sum"}
        if units_col:
            agg_dict[units_col] = "sum"
            
        grouped = df.groupby(prod_col).agg(agg_dict).reset_index()
        grouped["Margin (%)"] = (grouped[profit_col] / grouped[sales_col]) * 100
        grouped = grouped.sort_values(by=sales_col, ascending=False).head(limit)
        
        res = f"| {prod_col} | Total Sales | Units Sold | Profit Margin (%) |\n"
        res += "|---|---|---|---|\n"
        for _, row in grouped.iterrows():
            units_val = f"{row[units_col]:,}" if units_col in row else "N/A"
            res += f"| {row[prod_col]} | ${row[sales_col]:,.2f} | {units_val} | {row['Margin (%)']:.2f}% |\n"
        return res
    except Exception as e:
        return f"Error calculating margins: {str(e)}"


def get_active_datasets() -> str:
    """Returns the names of all currently loaded and active datasets in the workspace."""
    global _active_datasets, _active_df
    if not _active_datasets:
        return "No datasets are currently loaded in the active workspace."
        
    names = list(_active_datasets.keys())
    res = f"Active datasets loaded in the workspace: {', '.join(names)}.\n"
    if _active_df is not None:
        res += f"Consolidated dataset shape: {_active_df.shape[0]} rows, {_active_df.shape[1]} columns."
    return res