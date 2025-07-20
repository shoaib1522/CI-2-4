# auth_service.py

import sqlite3
import redis
import os

DB_NAME = 'users.db'

def create_user_and_session(username: str, redis_host: str = 'localhost', redis_port: int = 6379):
    """
    Coordinates creating a user in the SQLite database and their session in Redis.
    """
    # --- Step 1: Write user to the SQLite database ---
    # Using 'with' handles connection opening/closing and transactions automatically.
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Ensure the table exists before trying to insert into it.
        cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT NOT NULL UNIQUE)')
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        # The 'with' block automatically commits on success.

    # --- Step 2: Add a session key to the Redis cache ---
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        # Check if the connection is alive.
        r.ping()
        # Set a simple key-value pair. e.g., 'session:testuser' -> 'active'
        r.set(f'session:{username}', 'active', ex=3600) # ex=3600 sets a 1-hour expiry.
    except redis.exceptions.ConnectionError as e:
        # Provide a helpful error message if Redis isn't available.
        print(f"Error connecting to Redis: {e}")
        raise

def user_exists_in_db(username: str) -> bool:
    """Checks if a user exists in the SQLite database."""
    if not os.path.exists(DB_NAME):
        return False
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username=?', (username,))
        result = cursor.fetchone()
    return result is not None

def session_exists_in_redis(username: str, redis_host: str = 'localhost', redis_port: int = 6379) -> bool:
    """Checks if a user's session key exists in Redis."""
    try:
        r = redis.Redis(host=redis_host, port=redis_port)
        r.ping()
        return r.exists(f'session:{username}') == 1
    except redis.exceptions.ConnectionError:
        return False