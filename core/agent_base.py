import json
import uuid
import datetime
import logging
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, agent_id=None, agent_type=None):
        self.agent_id = agent_id or f"{agent_type}_{uuid.uuid4()}"
        self.agent_type = agent_type
        self.status = "inactive"
        self.logger = logging.getLogger(f"agent.{self.agent_type}")
        
    def register(self, db_connector):
        """Register agent in the agent_registry table"""
        query = """
        INSERT INTO agent_registry (agent_id, agent_type, status)
        VALUES (%s, %s, %s)
        ON CONFLICT (agent_id) DO UPDATE 
        SET status = %s, last_active = CURRENT_TIMESTAMP
        """
        db_connector.execute(query, (self.agent_id, self.agent_type, self.status, self.status))
        self.logger.info(f"Agent {self.agent_id} registered successfully")
        
    def update_status(self, db_connector, status):
        """Update agent status in the registry"""
        self.status = status
        query = """
        UPDATE agent_registry 
        SET status = %s, last_active = CURRENT_TIMESTAMP
        WHERE agent_id = %s
        """
        db_connector.execute(query, (status, self.agent_id))
        self.logger.info(f"Agent {self.agent_id} status updated to {status}")
    
    def send_message(self, db_connector, recipient_id, message_type, content):
        """Send a message to another agent"""
        query = """
        INSERT INTO agent_messages (sender_id, recipient_id, message_type, content)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        message_id = db_connector.execute(query, (
            self.agent_id, recipient_id, message_type, json.dumps(content)
        ))
        self.logger.info(f"Message sent to {recipient_id}, type: {message_type}, id: {message_id}")
        return message_id
    
    def get_messages(self, db_connector, mark_as_read=True):
        """Get messages sent to this agent"""
        query = """
        SELECT id, sender_id, message_type, content, created_at
        FROM agent_messages
        WHERE recipient_id = %s AND is_read = FALSE
        ORDER BY created_at ASC
        """
        messages = db_connector.query(query, (self.agent_id,))
        
        if mark_as_read and messages:
            message_ids = [m["id"] for m in messages]
            update_query = """
            UPDATE agent_messages
            SET is_read = TRUE
            WHERE id IN (%s)
            """
            placeholders = ", ".join(["%s"] * len(message_ids))
            db_connector.execute(update_query % placeholders, tuple(message_ids))
            
        return messages
    
    def create_task(self, db_connector, task_data, priority=5):
        """Create a new task for this agent"""
        task_id = f"task_{uuid.uuid4()}"
        query = """
        INSERT INTO agent_tasks (task_id, agent_id, status, priority, task_data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        task_db_id = db_connector.execute(query, (
            task_id, self.agent_id, "pending", priority, json.dumps(task_data)
        ))
        self.logger.info(f"Task created: {task_id} with priority {priority}")
        return task_id
    
    def get_pending_tasks(self, db_connector):
        """Get pending tasks for this agent"""
        query = """
        SELECT id, task_id, priority, task_data, created_at
        FROM agent_tasks
        WHERE agent_id = %s AND status = 'pending'
        ORDER BY priority DESC, created_at ASC
        """
        return db_connector.query(query, (self.agent_id,))
    
    def update_task_status(self, db_connector, task_id, status, result=None):
        """Update task status and optionally add result"""
        query = """
        UPDATE agent_tasks
        SET status = %s, result = %s
        """
        params = [status, json.dumps(result) if result else None]
        
        if status == "in_progress":
            query += ", started_at = CURRENT_TIMESTAMP"
        elif status in ["completed", "failed"]:
            query += ", completed_at = CURRENT_TIMESTAMP"
            
        query += " WHERE task_id = %s"
        params.append(task_id)
        
        db_connector.execute(query, tuple(params))
        self.logger.info(f"Task {task_id} status updated to {status}")
    
    @abstractmethod
    def run(self, db_connector):
        """Main agent execution method, must be implemented by subclasses"""
        pass
