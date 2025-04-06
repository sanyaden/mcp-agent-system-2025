import psycopg2
import psycopg2.extras
import logging
from config.settings import DATABASE_CONFIG

class DBConnector:
    def __init__(self):
        self.connection_params = DATABASE_CONFIG
        self.logger = logging.getLogger("agent.db_connector")
        self.connection = None
        
    def connect(self):
        """Establish a database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.connection_params["host"],
                port=self.connection_params["port"],
                dbname=self.connection_params["database"],
                user=self.connection_params["user"],
                password=self.connection_params["password"]
            )
            self.logger.info("Database connection established")
            return True
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")
    
    def execute(self, query, params=None):
        """Execute a query and return inserted ID if applicable"""
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                
                if query.strip().upper().startswith("INSERT") and "RETURNING" in query.upper():
                    return cursor.fetchone()[0]
                return True
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            self.connection.rollback()
            return None
    
    def query(self, query, params=None):
        """Execute a query and return results as a list of dictionaries"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return list(results)
        except Exception as e:
            self.logger.error(f"Query error: {str(e)}")
            return []
            
    def retrieve_data(self, source=None, time_range=None):
        """Retrieve data with filters - interface used by AnalyticsAgent"""
        query_params = []
        query = "SELECT * FROM sales_metrics WHERE 1=1"
        
        if source:
            query += " AND source = %s"
            query_params.append(source)
            
        if time_range and len(time_range) == 2:
            query += " AND date >= %s AND date <= %s"
            query_params.extend(time_range)
            
        query += " ORDER BY date DESC"
        
        return self.query(query, tuple(query_params))
        
    def store_analysis_results(self, results):
        """Store analysis results - interface used by AnalyticsAgent"""
        query = """
        INSERT INTO sales_insights (
            date, insight_type, description, severity, metrics
        ) VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            date = results.get("date") or results.get("timestamp").split("T")[0]
            insight_type = results.get("analysis_method", "basic_analysis")
            description = results.get("insights", ["No insights generated"])[0]
            severity = "medium"  # Default severity
            metrics = results.get("metrics", {})
            
            return self.execute(query, (date, insight_type, description, severity, psycopg2.extras.Json(metrics)))
        except Exception as e:
            self.logger.error(f"Error storing analysis results: {str(e)}")
            return None
