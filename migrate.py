from database import get_connection
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE issues ADD COLUMN layout_template VARCHAR(50) DEFAULT 'template_1'")
    conn.commit()
    print("Done!")
except Exception as e:
    if "Duplicate column" in str(e):
        print("Column already exists!")
    else:
        print(f"Error: {e}")
cursor.close()
conn.close()