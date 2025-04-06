# MCP Agent System

A multi-agent system for data collection, analytics, alerting, and reporting.

## Project Structure

```
mcp-agent-system/
├── agents/
│   ├── __init__.py
│   ├── data_collection_agent.py
│   ├── analytics_agent.py
│   ├── alert_agent.py
│   └── reporting_agent.py
├── core/
│   ├── __init__.py
│   ├── agent_base.py
│   ├── db_connector.py
│   ├── agent_scheduler.py
│   └── message_broker.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── utils/
│   ├── __init__.py
│   └── logging_utils.py
├── requirements.txt
├── setup.py
└── README.md
```

## Agents

### BaseAgent
The abstract base class for all agents in the system, providing common functionality:
- Agent registration and status management
- Message passing between agents
- Task creation and management

### DataCollectionAgent
Responsible for collecting data from various sources and storing it in the database.

### AnalyticsAgent
Analyzes collected data to identify trends, patterns, and anomalies.

### AlertAgent
Monitors data and analytics results to generate alerts based on predefined conditions.

### ReportingAgent
Generates reports based on collected and analyzed data, including daily, weekly, and monthly reports.

## Setup and Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure database connection in `config/settings.py`
4. Run the agents using the agent scheduler

## Usage

```python
from core.agent_scheduler import AgentScheduler
from core.db_connector import DBConnector

# Initialize database connector
db_connector = DBConnector()

# Initialize and start agent scheduler
scheduler = AgentScheduler(db_connector)
scheduler.start_agents()
```
