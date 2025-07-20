# test_auth_flow.py

import pytest
import os
import sqlite3
import redis
from auth_service import (
    create_user_and_session,
    user_exists_in_db,
    session_exists_in_redis,
    DB_NAME
)

# Determine the Redis host. In GitHub Actions, it's the service name ('redis').
# Locally, it's 'localhost'. We use an environment variable for this.
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """A fixture to ensure a clean state before and after each test."""
    # --- Setup ---
    # Delete the SQLite DB file if it exists.
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    # --- Teardown ---
    yield  # This is where the test runs.
    
    # After the test, clean up the database file again.
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Also, clean up the key in Redis to not affect other tests.
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379)
        r.delete("session:testuser")
    except redis.exceptions.ConnectionError:
        pass # Ignore if Redis isn't running (e.g., in a simple local run)

def test_full_auth_flow():
    """
    The main integration test. It verifies the entire process.
    """
    # 1. ARRANGE: Define our test data.
    username = "testuser"
    
    # 2. ACT: Call the main function that interacts with both services.
    # We pass the REDIS_HOST so the function knows where to connect.
    create_user_and_session(username, redis_host=REDIS_HOST)

    # 3. ASSERT: Verify the outcome in each service independently.
    
    # Check if the user was correctly written to the SQLite database.
    assert user_exists_in_db(username) == True, "User should exist in the database."
    
    # Check if the session was correctly created in the Redis cache.
    assert session_exists_in_redis(username, redis_host=REDIS_HOST) == True, "Session should exist in Redis."