import psycopg2

try:
    conn = psycopg2.connect(
        dbname="asha_db",
        user="postgres",
        password="Jiya@664",
        host="localhost"
    )
    cur = conn.cursor()
    
    table_name = 'users'
    print(f"Schema for {table_name}:")
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
    """)
    for col in cur.fetchall():
        print(col)
        
    print("\nConstraints:")
    cur.execute(f"""
        SELECT conname, contype
        FROM pg_constraint
        JOIN pg_class ON pg_class.oid = pg_constraint.conrelid
        WHERE relname = '{table_name}'
    """)
    for con in cur.fetchall():
        print(con)
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
