#!/usr/bin/env python3
"""
Database initialization script for MCP Agent System.
This script creates all necessary tables in the PostgreSQL database.
"""
import os
import sys
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Initialize MCP Agent System database')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', help='Database password')
    parser.add_argument('--dbname', default='mcp_agent_system', help='Database name')
    parser.add_argument('--create-db', action='store_true', help='Create database if it does not exist')
    parser.add_argument('--sample-data', action='store_true', help='Insert sample data')
    return parser.parse_args()

def create_database(args):
    """Create database if it does not exist."""
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (args.dbname,))
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating database '{args.dbname}'...")
        cursor.execute(f"CREATE DATABASE {args.dbname}")
        print(f"Database '{args.dbname}' created successfully.")
    else:
        print(f"Database '{args.dbname}' already exists.")
    
    cursor.close()
    conn.close()

def init_tables(args):
    """Initialize database tables."""
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname=args.dbname
    )
    cursor = conn.cursor()
    
    # Read schema.sql file
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    print("Creating tables...")
    cursor.execute(schema_sql)
    conn.commit()
    print("Tables created successfully.")
    
    cursor.close()
    conn.close()

def insert_sample_data(args):
    """Insert sample data into the database."""
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname=args.dbname
    )
    cursor = conn.cursor()
    
    # Insert sample agents
    print("Inserting sample agents...")
    agents = [
        ('data_collection_agent_1', 'data_collection', 'inactive'),
        ('analytics_agent_1', 'analytics', 'inactive'),
        ('alert_agent_1', 'alert', 'inactive'),
        ('reporting_agent_1', 'reporting', 'inactive')
    ]
    
    for agent in agents:
        cursor.execute(
            "INSERT INTO agent_registry (agent_id, agent_type, status) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id) DO NOTHING",
            agent
        )
    
    # Insert sample orders
    print("Inserting sample orders...")
    orders = [
        ('2025-04-01', 'client_1', 150.00, 'web'),
        ('2025-04-01', 'client_2', 250.00, 'mobile'),
        ('2025-04-01', 'client_3', 350.00, 'store'),
        ('2025-04-02', 'client_4', 450.00, 'web'),
        ('2025-04-02', 'client_5', 550.00, 'mobile'),
        ('2025-04-03', 'client_6', 650.00, 'store'),
        ('2025-04-03', 'client_7', 750.00, 'web'),
        ('2025-04-04', 'client_8', 850.00, 'mobile'),
        ('2025-04-04', 'client_9', 950.00, 'store'),
        ('2025-04-05', 'client_10', 1050.00, 'web')
    ]
    
    for order in orders:
        cursor.execute(
            "INSERT INTO orders (date, client_id, amount_total, source) VALUES (%s, %s, %s, %s)",
            order
        )
    
    conn.commit()
    print("Sample data inserted successfully.")
    
    cursor.close()
    conn.close()

def main():
    """Main function."""
    args = parse_args()
    
    if args.create_db:
        create_database(args)
    
    init_tables(args)
    
    if args.sample_data:
        insert_sample_data(args)
    
    print("Database initialization completed successfully.")

if __name__ == '__main__':
    main()
