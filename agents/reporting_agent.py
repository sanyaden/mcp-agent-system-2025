from core.agent_base import BaseAgent
import json
import time
import datetime
import random
import os

class ReportingAgent(BaseAgent):
    def __init__(self, agent_id=None):
        super().__init__(agent_id, "reporting")
        self.reporting_schedule = {
            "daily": True,
            "weekly": True,
            "monthly": True
        }
        self.report_directory = "reports"
        
        # Ensure report directory exists
        os.makedirs(self.report_directory, exist_ok=True)
        
    def run(self, db_connector):
        self.update_status(db_connector, "active")
        
        last_daily_report = None
        last_weekly_report = None
        last_monthly_report = None
        
        while True:
            try:
                # Process configuration messages
                messages = self.get_messages(db_connector)
                for message in messages:
                    if message["message_type"] == "configuration":
                        config = json.loads(message["content"])
                        if "reporting_schedule" in config:
                            self.reporting_schedule.update(config["reporting_schedule"])
                
                # Check if reports need to be generated
                now = datetime.datetime.now()
                today = now.date()
                
                # Daily report (once per day)
                if (self.reporting_schedule["daily"] and 
                    (last_daily_report is None or last_daily_report < today)):
                    
                    yesterday = (today - datetime.timedelta(days=1)).isoformat()
                    self.generate_daily_report(db_connector, yesterday)
                    last_daily_report = today
                
                # Weekly report (on Mondays)
                if (self.reporting_schedule["weekly"] and now.weekday() == 0 and
                    (last_weekly_report is None or last_weekly_report < today)):
                    
                    week_start = (today - datetime.timedelta(days=7)).isoformat()
                    week_end = (today - datetime.timedelta(days=1)).isoformat()
                    self.generate_weekly_report(db_connector, week_start, week_end)
                    last_weekly_report = today
                
                # Monthly report (on 1st of month)
                if (self.reporting_schedule["monthly"] and now.day == 1 and
                    (last_monthly_report is None or last_monthly_report < today)):
                    
                    # Calculate previous month's date range
                    last_month = now.replace(day=1) - datetime.timedelta(days=1)
                    month_start = last_month.replace(day=1).isoformat()
                    month_end = last_month.isoformat()
                    
                    self.generate_monthly_report(db_connector, month_start, month_end)
                    last_monthly_report = today
                
                # Process specific report requests
                tasks = self.get_pending_tasks(db_connector)
                for task in tasks:
                    task_data = json.loads(task["task_data"])
                    task_id = task["task_id"]
                    
                    self.update_task_status(db_connector, task_id, "in_progress")
                    
                    if task_data.get("type") == "custom_report":
                        start_date = task_data.get("start_date")
                        end_date = task_data.get("end_date")
                        report_type = task_data.get("report_type", "sales_summary")
                        
                        result = self.generate_custom_report(
                            db_connector, start_date, end_date, report_type
                        )
                        
                        self.update_task_status(db_connector, task_id, "completed", result)
                
                # Sleep until next check (every hour)
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Error in reporting agent: {str(e)}")
                self.update_status(db_connector, "error")
                time.sleep(60)  # Wait before retrying
    
    def generate_daily_report(self, db_connector, date):
        """Generate a daily sales report"""
        self.logger.info(f"Generating daily report for {date}")
        
        try:
            # Get sales data
            query = """
            SELECT 
                source,
                total_sales, 
                total_orders,
                average_order_value
            FROM sales_metrics
            WHERE date = %s
            ORDER BY total_sales DESC
            """
            
            sales_data = db_connector.query(query, (date,))
            
            # Get insights for the day
            insights_query = """
            SELECT insight_type, description, severity
            FROM sales_insights
            WHERE date = %s
            ORDER BY severity DESC
            """
            
            insights = db_connector.query(insights_query, (date,))
            
            # Generate report content
            report_data = {
                "date": date,
                "sales_data": sales_data,
                "insights": insights,
                "total_sales": sum(s["total_sales"] for s in sales_data) if sales_data else 0,
                "total_orders": sum(s["total_orders"] for s in sales_data) if sales_data else 0
            }
            
            # Generate report artifact (would use MCP artifacts in a real implementation)
            artifact_id = f"daily_report_{date}_{random.randint(1000, 9999)}"
            
            # Store report reference
            report_id = f"daily_{date}"
            store_query = """
            INSERT INTO report_archive (
                report_id, report_type, title, description, 
                period_start, period_end, artifact_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            archive_id = db_connector.execute(store_query, (
                report_id,
                "daily",
                f"Daily Sales Report for {date}",
                f"Summary of sales performance for {date}",
                date,
                date,
                artifact_id
            ))
            
            self.logger.info(f"Daily report archived with ID: {archive_id}")
            return {
                "status": "success",
                "report_id": report_id,
                "archive_id": archive_id,
                "artifact_id": artifact_id
            }
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {str(e)}")
            return {
                "status": "error",
                "date": date,
                "error": str(e)
            }
    
    def generate_weekly_report(self, db_connector, start_date, end_date):
        """Generate a weekly sales report"""
        self.logger.info(f"Generating weekly report for {start_date} to {end_date}")
        
        try:
            # Get aggregated sales data for the week
            query = """
            SELECT 
                source,
                SUM(total_sales) as weekly_sales, 
                SUM(total_orders) as weekly_orders,
                AVG(average_order_value) as avg_order_value
            FROM sales_metrics
            WHERE date >= %s AND date <= %s
            GROUP BY source
            ORDER BY weekly_sales DESC
            """
            
            sales_data = db_connector.query(query, (start_date, end_date))
            
            # Get top insights for the week
            insights_query = """
            SELECT insight_type, description, severity, date
            FROM sales_insights
            WHERE date >= %s AND date <= %s
            ORDER BY severity DESC, date DESC
            LIMIT 10
            """
            
            insights = db_connector.query(insights_query, (start_date, end_date))
            
            # Generate report content
            report_data = {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "sales_data": sales_data,
                "insights": insights,
                "total_weekly_sales": sum(s["weekly_sales"] for s in sales_data) if sales_data else 0,
                "total_weekly_orders": sum(s["weekly_orders"] for s in sales_data) if sales_data else 0
            }
            
            # Generate report artifact
            artifact_id = f"weekly_report_{start_date}_to_{end_date}_{random.randint(1000, 9999)}"
            
            # Store report reference
            report_id = f"weekly_{start_date}_to_{end_date}"
            store_query = """
            INSERT INTO report_archive (
                report_id, report_type, title, description, 
                period_start, period_end, artifact_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            archive_id = db_connector.execute(store_query, (
                report_id,
                "weekly",
                f"Weekly Sales Report ({start_date} to {end_date})",
                f"Summary of weekly sales performance",
                start_date,
                end_date,
                artifact_id
            ))
            
            self.logger.info(f"Weekly report archived with ID: {archive_id}")
            return {
                "status": "success",
                "report_id": report_id,
                "archive_id": archive_id,
                "artifact_id": artifact_id
            }
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {str(e)}")
            return {
                "status": "error",
                "period": f"{start_date} to {end_date}",
                "error": str(e)
            }
    
    def generate_monthly_report(self, db_connector, start_date, end_date):
        """Generate a monthly sales report with trends and comparisons"""
        self.logger.info(f"Generating monthly report for {start_date} to {end_date}")
        
        try:
            # Get aggregated sales data for the month
            query = """
            SELECT 
                source,
                SUM(total_sales) as monthly_sales, 
                SUM(total_orders) as monthly_orders,
                AVG(average_order_value) as avg_order_value
            FROM sales_metrics
            WHERE date >= %s AND date <= %s
            GROUP BY source
            ORDER BY monthly_sales DESC
            """
            
            sales_data = db_connector.query(query, (start_date, end_date))
            
            # Get daily trends for the month
            trends_query = """
            SELECT 
                date,
                SUM(total_sales) as daily_sales
            FROM sales_metrics
            WHERE date >= %s AND date <= %s
            GROUP BY date
            ORDER BY date
            """
            
            daily_trends = db_connector.query(trends_query, (start_date, end_date))
            
            # Generate report content
            report_data = {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "sales_data": sales_data,
                "daily_trends": daily_trends,
                "total_monthly_sales": sum(s["monthly_sales"] for s in sales_data) if sales_data else 0,
                "total_monthly_orders": sum(s["monthly_orders"] for s in sales_data) if sales_data else 0
            }
            
            # Generate report artifact
            artifact_id = f"monthly_report_{start_date}_to_{end_date}_{random.randint(1000, 9999)}"
            
            # Store report reference
            report_id = f"monthly_{start_date}_to_{end_date}"
            store_query = """
            INSERT INTO report_archive (
                report_id, report_type, title, description, 
                period_start, period_end, artifact_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            archive_id = db_connector.execute(store_query, (
                report_id,
                "monthly",
                f"Monthly Sales Report ({start_date} to {end_date})",
                f"Comprehensive monthly sales analysis with trends",
                start_date,
                end_date,
                artifact_id
            ))
            
            self.logger.info(f"Monthly report archived with ID: {archive_id}")
            return {
                "status": "success",
                "report_id": report_id,
                "archive_id": archive_id,
                "artifact_id": artifact_id
            }
            
        except Exception as e:
            self.logger.error(f"Error generating monthly report: {str(e)}")
            return {
                "status": "error",
                "period": f"{start_date} to {end_date}",
                "error": str(e)
            }
    
    def generate_custom_report(self, db_connector, start_date, end_date, report_type):
        """Generate a custom report based on specified parameters"""
        self.logger.info(f"Generating custom {report_type} report for {start_date} to {end_date}")
    
    def _collect_report_data(self, report_type, time_range, sources):
        """
        Collect data needed for the report.
        
        Args:
            report_type (str): Type of report
            time_range (tuple): Time range for the report
            sources (list): Data sources to include
            
        Returns:
            dict: Collected data for the report
        """
        report_data = {
            'metadata': {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'time_range': time_range,
                'sources': sources
            },
            'data': {}
        }
        
        # Collect data for each source
        for source in sources:
            source_data = self.db_connector.retrieve_data(
                source=source,
                time_range=time_range
            )
            
            report_data['data'][source] = source_data
            
        # If this is an analysis report, also get analysis results
        if report_type in ['analysis', 'insights']:
            analysis_results = self.db_connector.retrieve_analysis_results(
                time_range=time_range,
                sources=sources
            )
            
            report_data['analysis'] = analysis_results
            
        # If this is an alert report, get alert history
        if report_type in ['alerts', 'incidents']:
            alert_history = self.db_connector.retrieve_alerts(
                time_range=time_range,
                sources=sources
            )
            
            report_data['alerts'] = alert_history
            
        return report_data
    
    def _format_report(self, report_data, report_type, output_format):
        """
        Format the report data according to the specified output format.
        
        Args:
            report_data (dict): Data to include in the report
            report_type (str): Type of report
            output_format (str): Output format
            
        Returns:
            str: Formatted report content
        """
        if output_format == 'json':
            return json.dumps(report_data, indent=2)
            
        elif output_format == 'csv':
            # This is a placeholder for CSV formatting logic
            # In a real implementation, this would convert the data to CSV format
            return "CSV formatting not implemented"
            
        elif output_format == 'html':
            # This is a placeholder for HTML report generation
            # In a real implementation, this would generate an HTML report
            html_content = f"""
            <html>
                <head>
                    <title>{report_type.capitalize()} Report</title>
                </head>
                <body>
                    <h1>{report_type.capitalize()} Report</h1>
                    <p>Generated at: {report_data['metadata']['generated_at']}</p>
                    <pre>{json.dumps(report_data, indent=2)}</pre>
                </body>
            </html>
            """
            return html_content
            
        elif output_format == 'pdf':
            # This is a placeholder for PDF report generation
            # In a real implementation, this would generate a PDF report
            return "PDF formatting not implemented"
            
        else:
            self.logger.warning(f"Unsupported output format: {output_format}, defaulting to JSON")
            return json.dumps(report_data, indent=2)
    
    def _generate_report_filename(self, report_type, output_format):
        """
        Generate a filename for the report.
        
        Args:
            report_type (str): Type of report
            output_format (str): Output format
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{report_type}_report_{timestamp}.{output_format}"
    
    def _save_report(self, report_content, report_path, output_format):
        """
        Save the report content to a file.
        
        Args:
            report_content (str): Content of the report
            report_path (str): Path to save the report to
            output_format (str): Output format
        """
        mode = 'w'
        if output_format in ['pdf']:
            mode = 'wb'  # Binary mode for certain formats
            
        with open(report_path, mode) as f:
            f.write(report_content)
            
        self.logger.info(f"Report saved to {report_path}")
        
    def list_reports(self, report_type=None):
        """
        List available reports.
        
        Args:
            report_type (str, optional): Filter by report type
            
        Returns:
            list: Available reports
        """
        reports = []
        
        try:
            for filename in os.listdir(self.report_directory):
                file_path = os.path.join(self.report_directory, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                    
                # Filter by report type if specified
                if report_type and not filename.startswith(f"{report_type}_report_"):
                    continue
                    
                file_stats = os.stat(file_path)
                
                reports.append({
                    'filename': filename,
                    'path': file_path,
                    'size': file_stats.st_size,
                    'created_at': datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                })
                
        except Exception as e:
            self.logger.error(f"Error listing reports: {str(e)}")
            
        return reports
