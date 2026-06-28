import pandas as pd


class DataAgent:
    def load_and_clean(self, file_path):
        df = pd.read_csv(file_path)

        df.drop_duplicates(inplace=True)

        df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], dayfirst=True, errors="coerce")

        numeric_cols = ["Sales", "Units", "Gross Profit", "Cost"]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(inplace=True)

        return df
    