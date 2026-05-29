import psycopg2

try:
    conn = psycopg2.connect(
        dbname="asha_db",
        user="postgres",
        password="Jiya@664",
        host="localhost"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    for table in tables:
        print(f"Dropping {table[0]}...")
        cur.execute(f"DROP TABLE IF EXISTS \"{table[0]}\" CASCADE")
        
    print("Database cleared.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
