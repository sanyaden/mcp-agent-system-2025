# test_data.py
from core.db_connector import DBConnector
import datetime
import random

def create_test_data():
    db = DBConnector()
    
    # Create some test orders
    sources = ["web", "mobile", "in_store", "phone"]
    
    for i in range(100):
        days_ago = random.randint(0, 30)
        date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        source = random.choice(sources)
        client_id = f"client_{random.randint(1000, 9999)}"
        amount = random.uniform(50, 500)
        
        query = """
        INSERT INTO orders (date, client_id, amount_total, source)
        VALUES (%s, %s, %s, %s)
        """
        
        db.execute(query, (date, client_id, amount, source))
    
    print("Created 100 test orders")

if __name__ == "__main__":
    create_test_data()
