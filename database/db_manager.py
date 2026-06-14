import sqlite3
import os

DB_PATH = os.environ.get("AGENT_DB_PATH", "agent_customizations.db")

def get_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables accessing columns by name
    return conn

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,       -- skills, rules, workflows, mcp, plugins, hooks
                name TEXT NOT NULL,
                type TEXT NOT NULL,           -- 'file', 'markdown', 'bookmark'
                content TEXT,                 -- Stores raw text, markdown content, or URL bookmark
                file_blob BLOB,               -- Binary field to store real file uploads if needed
                file_name TEXT,               -- The original file name
                description TEXT,
                tags TEXT,                    -- Comma-separated strings
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_customization(category, name, type_val, content, file_blob, file_name, description, tags):
    """Inserts or updates an agent customization record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customizations (category, name, type, content, file_blob, file_name, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (category, name, type_val, content, file_blob, file_name, description, tags))
        conn.commit()
        return cursor.lastrowid

def get_customizations(category=None):
    """Retrieves records, optionally filtered by a specific category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM customizations WHERE category = ?", (category,))
        else:
            cursor.execute("SELECT * FROM customizations")
        return [dict(row) for row in cursor.fetchall()]

def delete_customization(item_id):
    """Removes a customization by its primary ID key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customizations WHERE id = ?", (item_id,))
        conn.commit()

def update_customization(item_id, name, content, description, tags, file_blob=None, file_name=None):
    """Updates an existing agent customization record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if file_blob is not None or file_name is not None:
            cursor.execute("""
                UPDATE customizations 
                SET name = ?, content = ?, description = ?, tags = ?, file_blob = ?, file_name = ?
                WHERE id = ?
            """, (name, content, description, tags, file_blob, file_name, item_id))
        else:
            cursor.execute("""
                UPDATE customizations 
                SET name = ?, content = ?, description = ?, tags = ?
                WHERE id = ?
            """, (name, content, description, tags, item_id))
        conn.commit()

def get_customization_by_id(item_id):
    """Retrieves a single customization record by its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customizations WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


