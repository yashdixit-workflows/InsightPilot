from agents.kpi_agent import KPIAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent


def run_analysis(df):
    kpi_agent = KPIAgent()
    insight_agent = InsightAgent()
    recommendation_agent = RecommendationAgent()

    kpis = kpi_agent.calculate_kpis(df)
    insights = insight_agent.generate_insights(df)
    recommendations = recommendation_agent.generate_recommendations(df)

    charts = [
        "sales_by_region",
        "profit_by_region"
    ]

    return {
        "kpis": kpis,
        "charts": charts,
        "insights": insights,
        "recommendations": recommendations
    }