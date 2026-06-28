from agents.kpi_agent import KPIAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent


from agents.kpi_agent import KPIAgent
from agents.insight_agent import InsightAgent
from agents.recommendation_agent import RecommendationAgent


def analyze_query(df, query):
    query = query.lower()

    kpi_agent = KPIAgent()
    insight_agent = InsightAgent()
    recommendation_agent = RecommendationAgent()

    response = {
        "kpis": None,
        "insights": None,
        "recommendations": None
    }

    if "kpi" in query or "sales summary" in query:
        response["kpis"] = kpi_agent.calculate_kpis(df)

    elif "insight" in query or "sales low" in query or "region" in query:
        response["insights"] = insight_agent.generate_insights(df)

    elif "recommend" in query or "strategy" in query:
        response["recommendations"] = recommendation_agent.generate_recommendations(df)

    else:
        response["kpis"] = kpi_agent.calculate_kpis(df)
        response["insights"] = insight_agent.generate_insights(df)
        response["recommendations"] = recommendation_agent.generate_recommendations(df)

    return response