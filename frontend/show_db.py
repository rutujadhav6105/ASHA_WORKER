import psycopg2
import sys

try:
    conn = psycopg2.connect(
        dbname="asha_db",
        user="postgres",
        password="Jiya@664",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    
    print("Database: asha_db")
    print("-" * 40)
    
    if not tables:
        print("No tables found in public schema.")
    
    for table in tables:
        table_name = table[0]
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"Table: {table_name} | Row Count: {count}")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error connecting to database: {e}")
