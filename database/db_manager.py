import sqlite3
import os
import pg8000.dbapi
import ssl
from urllib.parse import urlparse

DB_PATH = os.environ.get("AGENT_DB_PATH", "agent_customizations.db")
DEPLOYMENT_ENV = os.environ.get("DEPLOYMENT_ENV", "local")

def get_connection():
    """Establishes and returns a connection to the database (SQLite locally, PostgreSQL/Supabase in cloud)."""
    if DEPLOYMENT_ENV == "cloud":
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required in cloud mode.")
        parsed = urlparse(db_url)
        username = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        hostname = parsed.hostname
        port = parsed.port or 5432
        
        ssl_ctx = None
        if hostname not in ("localhost", "127.0.0.1"):
            ssl_ctx = ssl.create_default_context()
            
        return pg8000.dbapi.connect(
            user=username,
            password=password,
            host=hostname,
            port=port,
            database=database,
            ssl_context=ssl_ctx
        )
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enables accessing columns by name
        return conn

def execute_query(cursor, sql, params=()):
    """Executes a SQL query, adapting placeholders between SQLite (?) and PostgreSQL (%s)."""
    if DEPLOYMENT_ENV == "cloud":
        sql = sql.replace("?", "%s")
    cursor.execute(sql, params)

def map_rows(cursor):
    """Maps cursor fetch results to a list of dicts dynamically."""
    if DEPLOYMENT_ENV == "cloud":
        desc = cursor.description
        if desc is None:
            return []
        columns = [col[0] for col in desc]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        return [dict(row) for row in cursor.fetchall()]

def map_row(cursor):
    """Maps a single cursor fetch result to a dict dynamically."""
    if DEPLOYMENT_ENV == "cloud":
        desc = cursor.description
        if desc is None:
            return None
        row = cursor.fetchone()
        if not row:
            return None
        columns = [col[0] for col in desc]
        return dict(zip(columns, row))
    else:
        row = cursor.fetchone()
        return dict(row) if row else None

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if DEPLOYMENT_ENV == "cloud":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customizations (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL,       -- skills, rules, workflows, mcp, plugins, hooks
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,           -- 'file', 'markdown', 'bookmark'
                    content TEXT,                 -- Stores raw text, markdown content, or URL bookmark
                    file_blob BYTEA,              -- Binary field to store real file uploads if needed
                    file_name TEXT,               -- The original file name
                    description TEXT,
                    tags TEXT,                    -- Comma-separated strings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
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
        sql = """
            INSERT INTO customizations (category, name, type, content, file_blob, file_name, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        if DEPLOYMENT_ENV == "cloud":
            sql = sql.replace("?", "%s") + " RETURNING id"
            cursor.execute(sql, (category, name, type_val, content, file_blob, file_name, description, tags))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id
        else:
            cursor.execute(sql, (category, name, type_val, content, file_blob, file_name, description, tags))
            conn.commit()
            return cursor.lastrowid

def get_customizations(category=None):
    """Retrieves records, optionally filtered by a specific category."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            sql = "SELECT * FROM customizations WHERE category = ?"
            execute_query(cursor, sql, (category,))
        else:
            sql = "SELECT * FROM customizations"
            execute_query(cursor, sql)
        return map_rows(cursor)

def delete_customization(item_id):
    """Removes a customization by its primary ID key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        sql = "DELETE FROM customizations WHERE id = ?"
        execute_query(cursor, sql, (item_id,))
        conn.commit()

def update_customization(item_id, name, content, description, tags, file_blob=None, file_name=None):
    """Updates an existing agent customization record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if file_blob is not None or file_name is not None:
            sql = """
                UPDATE customizations 
                SET name = ?, content = ?, description = ?, tags = ?, file_blob = ?, file_name = ?
                WHERE id = ?
            """
            params = (name, content, description, tags, file_blob, file_name, item_id)
        else:
            sql = """
                UPDATE customizations 
                SET name = ?, content = ?, description = ?, tags = ?
                WHERE id = ?
            """
            params = (name, content, description, tags, item_id)
        execute_query(cursor, sql, params)
        conn.commit()

def get_customization_by_id(item_id):
    """Retrieves a single customization record by its ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM customizations WHERE id = ?"
        execute_query(cursor, sql, (item_id,))
        return map_row(cursor)
