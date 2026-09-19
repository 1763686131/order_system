import sqlite3

from flask import Flask

from utils.auth import login_session


app = Flask(__name__)
app.secret_key = "session-test"
connection = sqlite3.connect(":memory:")
connection.row_factory = sqlite3.Row
connection.executescript(
    """
    CREATE TABLE auth_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_token_hash TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        device_id TEXT NOT NULL DEFAULT '',
        device_name TEXT NOT NULL DEFAULT '',
        session_kind TEXT NOT NULL DEFAULT 'touch',
        browser TEXT NOT NULL DEFAULT '',
        operating_system TEXT NOT NULL DEFAULT '',
        timezone TEXT NOT NULL DEFAULT '',
        user_agent TEXT NOT NULL DEFAULT '',
        ip_address TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        revoked_by INTEGER
    );
    CREATE UNIQUE INDEX idx_auth_sessions_user_device
    ON auth_sessions(user_id, device_id)
    WHERE device_id != '';
    """
)
user_row = {"id": 1, "permission_version": 1}
user = {"canAccessAdmin": True, "longSession": True}
device = {"id": "same-device", "name": "Windows · Chrome"}

with app.test_request_context("/", headers={"User-Agent": "Chrome/100 Windows"}):
    login_session(connection, user_row, user, device)
    first = connection.execute(
        "SELECT id, session_token_hash FROM auth_sessions"
    ).fetchone()
    login_session(connection, user_row, user, device)
    second = connection.execute(
        "SELECT id, session_token_hash FROM auth_sessions"
    ).fetchone()

row_count = connection.execute(
    "SELECT COUNT(*) FROM auth_sessions"
).fetchone()[0]
assert row_count == 1
assert first["id"] == second["id"]
assert first["session_token_hash"] != second["session_token_hash"]
assert connection.execute(
    "SELECT revoked_at FROM auth_sessions"
).fetchone()["revoked_at"] is None
print("same_device_relogin=passed")
