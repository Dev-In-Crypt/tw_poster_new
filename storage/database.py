import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- Threads ---
    def save_thread(self, topic: str, style: str, tweets: list[str],
                    image_url: str | None = None) -> int:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO threads (topic, style, tweets_json, image_url, status) "
            "VALUES (?, ?, ?, ?, 'draft')",
            (topic, style, json.dumps(tweets), image_url),
        )
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return thread_id

    def mark_posted(self, thread_id: int, twitter_thread_id: str):
        conn = self._conn()
        conn.execute(
            "UPDATE threads SET status='posted', twitter_thread_id=?, "
            "posted_at=? WHERE id=?",
            (twitter_thread_id, datetime.now(timezone.utc).isoformat(), thread_id),
        )
        conn.commit()
        conn.close()

    def get_thread(self, thread_id: int) -> Optional[dict]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM threads WHERE id=?", (thread_id,)
        ).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["tweets"] = json.loads(d["tweets_json"])
            return d
        return None

    def get_pending_threads(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM threads WHERE status='draft' ORDER BY created_at"
        ).fetchall()
        conn.close()
        return [
            {**dict(r), "tweets": json.loads(r["tweets_json"])} for r in rows
        ]

    # --- Topic dedup ---
    def is_topic_used(self, topic_summary: str) -> bool:
        conn = self._conn()
        row = conn.execute(
            "SELECT id FROM topic_history WHERE topic_summary = ?",
            (topic_summary.lower().strip(),),
        ).fetchone()
        conn.close()
        return row is not None

    def get_recent_topics(self, limit: int = 30) -> list[str]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT topic_summary FROM topic_history "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [r["topic_summary"] for r in rows]

    def save_topic(self, topic_summary: str):
        conn = self._conn()
        conn.execute(
            "INSERT INTO topic_history (topic_summary) VALUES (?)",
            (topic_summary.lower().strip(),),
        )
        conn.commit()
        conn.close()

    # --- Schedule ---
    def get_schedules(self) -> list[dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM schedule WHERE enabled=1"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def add_schedule(self, hour: int, minute: int):
        conn = self._conn()
        conn.execute(
            "INSERT INTO schedule (hour, minute) VALUES (?, ?)",
            (hour, minute),
        )
        conn.commit()
        conn.close()

    def remove_schedule(self, schedule_id: int):
        conn = self._conn()
        conn.execute("DELETE FROM schedule WHERE id=?", (schedule_id,))
        conn.commit()
        conn.close()
