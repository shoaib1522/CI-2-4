# test_auth_flow.py

import pytest
import os
import redis
from auth_service import (
    create_user_and_session,
    user_exists_in_db,
    session_exists_in_redis,
    DB_NAME
)

# This is the key. It reads the environment variable set by the CI workflow.
# If the variable is not set (like in a local run), it defaults to 'localhost'.
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = 6379

@pytest.fixture(scope="module", autouse=True)
def redis_connection():
    """A module-scoped fixture to check Redis connection once."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        r.ping()
        print(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return r
    except redis.exceptions.ConnectionError as e:
        pytest.fail(f"Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Error: {e}")

@pytest.fixture(autouse=True)
def setup_and_teardown(redis_connection):
    """A fixture to ensure a clean state before and after each test."""
    # --- Setup ---
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    # Clean up keys from previous runs, just in case
    for key in redis_connection.scan_iter("session:*"):
        redis_connection.delete(key)
    
    yield  # This is where the test runs.
    
    # --- Teardown ---
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    for key in redis_connection.scan_iter("session:*"):
        redis_connection.delete(key)


def test_full_auth_flow():
    """The main integration test. It verifies the entire process."""
    username = "testuser"
    
    # ACT: Call the main function that interacts with both services.
    create_user_and_session(username, redis_host=REDIS_HOST, redis_port=REDIS_PORT)

    # ASSERT: Verify the outcome in each service independently.
    assert user_exists_in_db(username), "User should exist in the database."
    assert session_exists_in_redis(username, redis_host=REDIS_HOST, redis_port=REDIS_PORT), "Session should exist in Redis."