from core.agent_base import BaseAgent
import datetime
import json
import time

class DataCollectionAgent(BaseAgent):
    def __init__(self, agent_id=None):
        super().__init__(agent_id, "data_collection")
        self.collection_frequency = 3600  # Default: collect every hour
    
    def run(self, db_connector):
        self.update_status(db_connector, "active")
        
        while True:
            try:
                # Process any configuration messages
                messages = self.get_messages(db_connector)
                for message in messages:
                    if message["message_type"] == "configuration":
                        config = json.loads(message["content"])
                        if "collection_frequency" in config:
                            self.collection_frequency = config["collection_frequency"]
                            self.logger.info(f"Updated collection frequency to {self.collection_frequency} seconds")
                
                # Get pending tasks
                tasks = self.get_pending_tasks(db_connector)
                for task in tasks:
                    task_data = json.loads(task["task_data"])
                    task_id = task["task_id"]
                    
                    self.update_task_status(db_connector, task_id, "in_progress")
                    
                    if task_data.get("type") == "collect_sales_data":
                        result = self.collect_sales_data(db_connector, task_data.get("date"))
                        self.update_task_status(db_connector, task_id, "completed", result)
                        
                        # Notify analytics agent
                        self.send_message(
                            db_connector, 
                            "analytics_agent", 
                            "data_collected",
                            {"date": task_data.get("date"), "metrics_id": result.get("metrics_id")}
                        )
                
                # Perform regular data collection if no specific tasks
                if not tasks:
                    today = datetime.date.today().isoformat()
                    self.collect_sales_data(db_connector, today)
                
                time.sleep(self.collection_frequency)
                
            except Exception as e:
                self.logger.error(f"Error in data collection agent: {str(e)}")
                self.update_status(db_connector, "error")
                time.sleep(60)  # Wait before retrying
    
    def collect_sales_data(self, db_connector, date):
        """Collect sales data for a specific date and store aggregated metrics"""
        self.logger.info(f"Collecting sales data for {date}")
        
        # Use MCP to query the orders table
        query = """
        SELECT 
            %s as date,
            SUM(amount_total) as total_sales,
            COUNT(*) as total_orders,
            AVG(amount_total) as average_order_value,
            source,
            COUNT(DISTINCT client_id) as unique_customers
        FROM orders
        WHERE DATE(date) = %s
        GROUP BY source
        """
        
        try:
            # Execute the query using MCP
            results = db_connector.query(query, (date, date))
            
            # Store each aggregated record
            metrics_ids = []
            for result in results:
                insert_query = """
                INSERT INTO sales_metrics (
                    date, total_sales, total_orders, 
                    average_order_value, source, created_at
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
                """
                
                metric_id = db_connector.execute(insert_query, (
                    date, 
                    result["total_sales"],
                    result["total_orders"],
                    result["average_order_value"],
                    result["source"]
                ))
                metrics_ids.append(metric_id)
            
            self.logger.info(f"Collected and stored sales data for {date} ({len(metrics_ids)} records)")
            
            return {
                "status": "success",
                "date": date,
                "records_count": len(metrics_ids),
                "metrics_id": metrics_ids
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting sales data for {date}: {str(e)}")
            return {
                "status": "error",
                "date": date,
                "error": str(e)
            }
