# Insightpilot
this is a ai agent for data intelligence which supports user interaction 
# 🧠 InsightPilot
### AI-Powered Business Analytics Agent for Sales Intelligence

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python"/>
  <img src="https://img.shields.io/badge/Google%20ADK-Powered-orange?style=for-the-badge&logo=google"/>
  <img src="https://img.shields.io/badge/Antigravity%20IDE-Built%20With-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Kaggle-Capstone%20Project-20BEFF?style=for-the-badge&logo=kaggle"/>
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge"/>
</p>

---

> **InsightPilot** is an AI-driven multi-agent business analytics system that automates sales data analysis, KPI calculation, trend detection, and strategic recommendations — helping businesses make faster, smarter decisions.

---

## 📌 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Architecture](#-architecture)
- [Agent Breakdown](#-agent-breakdown)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Usage Examples](#-usage-examples)
- [Security](#-security)
- [Future Roadmap](#-future-roadmap)
- [Capstone Outcome](#-capstone-outcome)

---

## 🚨 Problem Statement

Businesses generate massive volumes of sales data daily, yet extracting meaningful insights remains slow, manual, and error-prone.

Traditional analytics workflows demand:
- ⏳ Manual KPI calculation
- 🧹 Repetitive data cleaning
- 📉 Time-consuming trend analysis
- 🤔 Subjective strategic interpretation

**Result:** Delayed decisions, missed opportunities, and wasted analyst hours.

---

## 💡 Solution

**InsightPilot** eliminates this bottleneck by deploying a multi-agent AI system that automates the entire analytics pipeline — from raw CSV data to boardroom-ready strategic recommendations.

| Without InsightPilot | With InsightPilot |
|---|---|
| Hours of manual analysis | Seconds via AI agents |
| Excel formulas & pivot tables | Natural language queries |
| Static reports | Dynamic business insights |
| Human interpretation | AI-powered recommendations |

---

## 🏗️ Architecture

```
User Query (Natural Language)
        ↓
 ┌──────────────────────────┐
 │  Antigravity / ADK Root  │  ← Orchestration Layer
 └──────────┬───────────────┘
            ↓
 ┌──────────────────────────────────────────┐
 │                                          │
 │  ┌─────────────┐   ┌─────────────────┐  │
 │  │  Data Agent │   │    KPI Agent    │  │
 │  │  (Load &    │   │  (Metrics &     │  │
 │  │   Clean)    │   │   Calculation)  │  │
 │  └─────────────┘   └─────────────────┘  │
 │                                          │
 │  ┌─────────────┐   ┌─────────────────┐  │
 │  │Insight Agent│   │ Recommendation  │  │
 │  │  (Trends &  │   │     Agent       │  │
 │  │  Patterns)  │   │  (Strategy)     │  │
 │  └─────────────┘   └─────────────────┘  │
 │                                          │
 └──────────────────────────────────────────┘
            ↓
   Business Intelligence Response
```

The root agent orchestrates all sub-agents, routing each user query to the appropriate specialist agent based on intent.

---

## 🤖 Agent Breakdown

### 1. 📦 Data Agent — `agents/data_agent.py`
The foundation of the pipeline. Handles all data ingestion and preprocessing.

**Responsibilities:**
- Load CSV sales datasets
- Handle missing/null values
- Parse and normalize date fields
- Prepare clean data for downstream agents

---

### 2. 📊 KPI Agent — `agents/kpi_agent.py`
Calculates core business performance metrics from clean data.

**KPIs Calculated:**

| Metric | Description |
|---|---|
| Total Sales | Gross revenue across all orders |
| Total Profit | Net profit after costs |
| Total Orders | Number of transactions |
| Profit Margin | Profit as % of revenue |
| Average Order Value | Mean revenue per order |
| Units Sold | Total product volume |

---

### 3. 🔍 Insight Agent — `agents/insight_agent.py`
Detects patterns and extracts business intelligence from processed data.

**Capabilities:**
- Identify top & lowest performing regions
- Detect most profitable customer segments
- Analyze sales trends over time
- Surface anomalies and performance gaps

---

### 4. 🎯 Recommendation Agent — `agents/recommendation_agent.py`
Translates insights into actionable strategic recommendations.

**Output Examples:**
- Prioritize investment in high-performing regions
- Optimize pricing strategies for low-margin segments
- Reduce operational inefficiencies in underperforming areas
- Reallocate resources based on profitability analysis

---

## ✨ Features

- 🗣️ **Natural Language Interface** — Ask business questions in plain English
- 🧹 **Auto Data Cleaning** — No manual preprocessing required
- 📈 **Automated KPI Dashboard** — Instant metric calculation
- 🔍 **Trend & Pattern Detection** — AI-powered insight generation
- 🎯 **Strategic Recommendations** — Actionable decision support
- 🔒 **Topic-Restricted Agent** — Focused only on business analytics
- 🛡️ **Read-Only Access** — No data modification risk

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| AI Orchestration | Google ADK (Agent Development Kit) |
| IDE & Agent Runtime | Antigravity IDE |
| Data Processing | Pandas |
| Data Format | CSV |
| Interface | CLI Chatbot (`chatbot.py`) |

---

## 📁 Project Structure

```
agy-cli-projects/
│
├── agents/
│   ├── data_agent.py           # Data loading & cleaning
│   ├── kpi_agent.py            # KPI calculation
│   ├── insight_agent.py        # Trend & pattern analysis
│   └── recommendation_agent.py # Strategic recommendations
│
├── tools/
│   ├── __init__.py
│   ├── adk_tools.py            # ADK tool definitions
│   ├── csv_tool.py             # CSV utilities
│   ├── csv_tools.py
│   ├── excel_tools.py          # Excel support (WIP)
│   ├── json_tools.py           # JSON data handling
│   └── sql_tools.py            # SQL integration (WIP)
│
├── Sales_Data.csv              # Sample business dataset
├── adk_root.py                 # Root agent orchestrator
├── chatbot.py                  # Main entry point
├── maintest_pipeline.py        # Testing pipeline
├── .env                        # Environment variables
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- Google ADK access
- Antigravity IDE (optional, recommended)

### 1. Clone the Repository
```bash
git clone <repository_url>
cd agy-cli-projects
```

### 2. Install Dependencies
```bash
pip install pandas google-adk
```

### 3. Configure Environment
```bash
# Add your API keys to .env
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Run InsightPilot
```bash
python chatbot.py
```

---

## 💬 Usage Examples

Once running, you can ask InsightPilot natural language business questions:

```
> Calculate KPIs
> Show business insights
> Which region performs best?
> Which region has the weakest sales?
> What is our profit margin?
> Give strategic recommendations
> Analyze overall business performance
> Which customer segment is most profitable?
```

**Example Output:**
```
📊 KPI Summary:
   Total Sales     : $1,245,320
   Total Profit    : $372,450
   Profit Margin   : 29.9%
   Total Orders    : 3,214
   Avg Order Value : $387.5
   Units Sold      : 18,420

🔍 Top Insight:
   West region outperforms all others with 34% of total revenue.
   Corporate segment yields the highest profit margin at 32%.

🎯 Recommendation:
   Increase marketing spend in West region.
   Focus on Corporate segment expansion for profitability growth.
```

---

## 🔒 Security

InsightPilot is designed with enterprise data safety in mind:

- **Topic Restriction** — Agent responds only to business analytics queries
- **Read-Only Access** — Cannot modify, delete, or overwrite any data files
- **No External Data Leakage** — All processing is local
- **Customer Privacy Protection** — No PII is exposed in responses

---

## 🔮 Future Roadmap

| Feature | Status |
|---|---|
| Excel (.xlsx) Support | 🔄 In Progress |
| SQL Database Integration | 🔄 In Progress |
| Interactive Dashboard UI | 📅 Planned |
| Forecasting Agent | 📅 Planned |
| Risk Detection Agent | 📅 Planned |
| Power BI Integration | 📅 Planned |
| n8n Workflow Automation | 📅 Planned |
| PDF Report Generation | 📅 Planned |

---

## 🏆 Capstone Outcome

InsightPilot was built as part of the **Kaggle AI Agents: Intensive Vibe Coding Capstone Project** under the **Agents for Business** track.

It demonstrates how multi-agent AI systems can:
- **Automate** repetitive business analytics workflows
- **Democratize** data insights for non-technical users
- **Accelerate** strategic decision-making with AI
- **Scale** analytics without growing analyst headcount

> Built with ❤️ using Google ADK + Antigravity IDE

---

## 👤 Author

**Yash Dixit**
- Kaggle: [@yashdixit](https://www.kaggle.com)
- Email: yash.dixit007@gmail.com

---

*InsightPilot — Turning raw sales data into business intelligence, automatically.*
