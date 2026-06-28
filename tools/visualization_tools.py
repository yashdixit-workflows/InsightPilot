import plotly.express as px
import pandas as pd


def render_chart(chart_type, df):

    if chart_type == "sales_by_region":
        region_sales = df.groupby("Region")["Sales"].sum().reset_index()

        fig = px.bar(
            region_sales,
            x="Region",
            y="Sales",
            title="Sales by Region"
        )
        return fig

    elif chart_type == "profit_by_region":
        region_profit = df.groupby("Region")["Gross Profit"].sum().reset_index()

        fig = px.bar(
            region_profit,
            x="Region",
            y="Gross Profit",
            title="Profit by Region"
        )
        return fig

    elif chart_type == "monthly_sales_trend":
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
        df["Month"] = df["Order Date"].dt.to_period("M").astype(str)

        monthly_sales = df.groupby("Month")["Sales"].sum().reset_index()

        fig = px.line(
            monthly_sales,
            x="Month",
            y="Sales",
            title="Monthly Sales Trend"
        )
        return fig

    return None