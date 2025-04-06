-- MCP Agent System Database Schema

-- Create database (run this separately if needed)
-- CREATE DATABASE mcp_agent_system;

-- Agent registry table
CREATE TABLE agent_registry (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent messages table
CREATE TABLE agent_messages (
    id SERIAL PRIMARY KEY,
    sender_id VARCHAR(255) NOT NULL,
    recipient_id VARCHAR(255) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent tasks table
CREATE TABLE agent_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    task_data JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Sales metrics table
CREATE TABLE sales_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_sales NUMERIC(15,2) NOT NULL,
    total_orders INTEGER NOT NULL,
    average_order_value NUMERIC(15,2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales insights table
CREATE TABLE sales_insights (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    insight_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System notifications table
CREATE TABLE system_notifications (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Report archive table
CREATE TABLE report_archive (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(255) UNIQUE NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    period_start DATE,
    period_end DATE,
    artifact_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_id VARCHAR(100) NOT NULL,
    amount_total NUMERIC(15,2) NOT NULL,
    source VARCHAR(100) NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_agent_messages_recipient ON agent_messages(recipient_id, is_read);
CREATE INDEX idx_agent_tasks_agent_status ON agent_tasks(agent_id, status);
CREATE INDEX idx_sales_metrics_date ON sales_metrics(date);
CREATE INDEX idx_sales_insights_date ON sales_insights(date, severity);
CREATE INDEX idx_system_notifications_type ON system_notifications(notification_type, is_read);
CREATE INDEX idx_report_archive_type_date ON report_archive(report_type, period_start, period_end);
