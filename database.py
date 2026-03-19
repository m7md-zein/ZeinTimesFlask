import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def init_db():
    conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS zein_times_v2")
    cursor.execute("USE zein_times_v2")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS newspapers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            author_name VARCHAR(255),
            phone VARCHAR(20),
            name VARCHAR(255) NOT NULL,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            frequency VARCHAR(50),
            description TEXT,
            cover_image VARCHAR(500),
            visitor_count INT DEFAULT 0,
            rating FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INT AUTO_INCREMENT PRIMARY KEY,
            newspaper_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            issue_number INT,
            publish_date DATE,
            style VARCHAR(100),
            status VARCHAR(50) DEFAULT 'draft',
            cover_image VARCHAR(500),
            rating FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (newspaper_id) REFERENCES newspapers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            issue_id INT NOT NULL,
            title VARCHAR(255),
            body_text TEXT,
            image_path VARCHAR(500),
            section_order INT,
            FOREIGN KEY (issue_id) REFERENCES issues(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            issue_id INT NOT NULL,
            newspaper_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_like (issue_id, newspaper_id),
            FOREIGN KEY (issue_id) REFERENCES issues(id),
            FOREIGN KEY (newspaper_id) REFERENCES newspapers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            id INT AUTO_INCREMENT PRIMARY KEY,
            follower_id INT NOT NULL,
            following_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_follow (follower_id, following_id),
            FOREIGN KEY (follower_id) REFERENCES newspapers(id),
            FOREIGN KEY (following_id) REFERENCES newspapers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            text_ar TEXT NOT NULL,
            text_en TEXT NOT NULL,
            author VARCHAR(255)
        )
    """)

    cursor.executemany("""
        INSERT IGNORE INTO quotes (id, text_ar, text_en, author) VALUES (%s, %s, %s, %s)
    """, [
        (1, "الكلمة سلاح من لا سلاح له.", "The word is a weapon for those who have none.", "مجهول"),
        (2, "اقرأ لتعيش ألف حياة.", "Read to live a thousand lives.", "مجهول"),
        (3, "الصحافة ضمير الأمة.", "Journalism is the conscience of the nation.", "مجهول"),
        (4, "الحبر أقوى من السيف.", "The pen is mightier than the sword.", "Edward Bulwer-Lytton"),
        (5, "الكتابة هي الطريقة التي يتحدث بها الصامتون.", "Writing is the way the silent speak.", "مجهول"),
    ])

    conn.commit()
    cursor.close()
    conn.close()
    print("Database ready.")

if __name__ == "__main__":
    load_dotenv()
    init_db()