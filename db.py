import sqlite3
from flask import g, current_app
from werkzeug.security import generate_password_hash
from pathlib import Path
from config import *



def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cursor = db.cursor()

    schema_path = Path(current_app.root_path) / "schema.sql"
    with open(schema_path, encoding="utf-8") as f:
        cursor.executescript(f.read())

    # --- seed expense types ---
    default_types = [
        ("מזון", "#FF6384"),
        ("תחבורה", "#36A2EB"),
        ("דיור", "#FFCE56"),
        ("בידור", "#4BC0C0"),
        ("אחר", "#9966FF"),
    ]

    for name, color in default_types:
        cursor.execute(
            "INSERT OR IGNORE INTO expense_types (name, color) VALUES (?, ?)",
            (name, color)
        )

    # --- seed admin ---
    cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, email, is_admin, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin@example.com",
            1
        ))

    db.commit()
    db.close()
