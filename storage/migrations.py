import sqlite3

def run_migrations(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            style TEXT NOT NULL,
            tweets_json TEXT NOT NULL,
            image_url TEXT,
            twitter_thread_id TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_summary TEXT NOT NULL,
            topic_embedding_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour INTEGER NOT NULL,
            minute INTEGER NOT NULL,
            enabled INTEGER DEFAULT 1,
            topic_override TEXT
        )
    """)

    conn.commit()
    conn.close()
