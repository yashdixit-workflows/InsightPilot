class RecommendationAgent:
    def generate_recommendations(self, df):
        recommendations = []

        region_sales = df.groupby("Region")["Sales"].sum()
        region_profit = df.groupby("Region")["Gross Profit"].sum()

        lowest_sales_region = region_sales.idxmin()
        highest_sales_region = region_sales.idxmax()

        lowest_profit_region = region_profit.idxmin()
        highest_profit_region = region_profit.idxmax()

        recommendations.append(
            f"Increase sales efforts in {lowest_sales_region} region, as it has the lowest sales performance."
        )

        recommendations.append(
            f"Study business strategies in {highest_sales_region} region since it generates the highest sales."
        )

        recommendations.append(
            f"Improve profitability in {lowest_profit_region} region by reducing costs or improving pricing."
        )

        recommendations.append(
            f"Expand successful profit strategies from {highest_profit_region} region to other regions."
        )

        return recommendations