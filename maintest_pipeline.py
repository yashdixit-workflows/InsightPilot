from agents.data_agent import DataAgent
from agents.kpi_agent import KPIAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent

agent = DataAgent()
kpi_agent = KPIAgent()
insight_agent = InsightAgent()
recommendation_agent = RecommendationAgent()

file_path = "Sales_Data.csv"

df = agent.load_and_clean(file_path)

print(df.head())
print(df.info())

kpis = kpi_agent.calculate_kpis(df)
print("\nBusiness KPIs:")
print(kpis)

insights = insight_agent.generate_insights(df)
print("\nBusiness Insights:")
print(insights)

recommendations = recommendation_agent.generate_recommendations(df)
print("\nRecommendations:")
for rec in recommendations:
    print("-", rec)