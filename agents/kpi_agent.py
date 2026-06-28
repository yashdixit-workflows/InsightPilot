class KPIAgent:
    def calculate_kpis(self, df):
        total_sales = df["Sales"].sum()
        total_profit = df["Gross Profit"].sum()
        total_units = df["Units"].sum()
        total_orders = df["Order ID"].nunique()

        profit_margin = (total_profit / total_sales) * 100
        avg_order_value = total_sales / total_orders

        return {
            "Total Sales": float(round(total_sales, 2)),
            "Total Profit": float(round(total_profit, 2)),
            "Total Units": int(total_units),
            "Total Orders": int(total_orders),
            "Profit Margin (%)": float(round(profit_margin, 2)),
            "Average Order Value": float(round(avg_order_value, 2))
        }