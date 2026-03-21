from database import get_connection
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE newspapers ADD COLUMN cover_image VARCHAR(500)")
    conn.commit()
    print("Done!")
except Exception as e:
    if "Duplicate column" in str(e):
        print("Column already exists!")
    else:
        print(f"Error: {e}")
cursor.close()
conn.close()
