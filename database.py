
import sqlite3
from pathlib import Path

# Store the database in the project directory
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leads.db"


def initialize_database():
    """Create the leads table if it does not already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                platform TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email)
            )
        """)


def save_lead(name: str, email: str, platform: str) -> dict:
    """Save a lead and report whether it was stored successfully."""
    initialize_database()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO leads (name, email, platform)
                VALUES (?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    platform = excluded.platform
                """,
                (name.strip(), email.strip(), platform.strip()),
            )

        return {"status": "success"}

    except sqlite3.Error as error:
        print(f"Database error while saving lead: {error}")
        return {"status": "error"}
