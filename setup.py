from setuptools import setup, find_packages

setup(
    name="mcp-agent-system",
    version="0.1.0",
    description="Multi-agent system for data collection, analytics, alerting, and reporting",
    author="MCP Team",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9.9",
        "python-dateutil>=2.8.2",
        "schedule>=1.2.0",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
)
