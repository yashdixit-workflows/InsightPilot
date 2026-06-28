class InsightAgent:
    def generate_insights(self, df):
        region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        region_profit = df.groupby("Region")["Gross Profit"].sum().sort_values(ascending=False)

        top_region = region_sales.index[0]
        top_region_sales = region_sales.iloc[0]

        lowest_region = region_sales.index[-1]
        lowest_region_sales = region_sales.iloc[-1]

        top_profit_region = region_profit.index[0]

        insights = {
            "Top Sales Region": f"{top_region} ({round(top_region_sales, 2)})",
            "Lowest Sales Region": f"{lowest_region} ({round(lowest_region_sales, 2)})",
            "Most Profitable Region": top_profit_region
        }

        return insights