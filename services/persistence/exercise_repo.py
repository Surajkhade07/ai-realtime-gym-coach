import sqlite3
import hashlib
import secrets
import streamlit as st
from pathlib import Path


_DB_PATH = str(Path(__file__).parent.parent.parent / "data.db")


@st.cache_resource
def _get_connection():
    conn = sqlite3.connect(
        _DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()

    with conn:

        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                salt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Auto-migrate table if password_hash or salt is missing
        cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "password_hash" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        if "salt" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN salt TEXT")

        # Exercise logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercise_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exercise_name TEXT NOT NULL,
                reps INTEGER NOT NULL DEFAULT 0,
                sets INTEGER NOT NULL DEFAULT 0,
                time INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return pwd_hash, salt


def _verify_password_hash(password: str, stored_hash: str, salt: str) -> bool:
    if not stored_hash or not salt:
        return False
    computed_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)


def register_user(username: str, password: str):
    username = username.strip()
    if not username or not password:
        return None

    pwd_hash, salt = _hash_password(password)
    conn = _get_connection()

    try:
        with conn:
            cursor = conn.execute("""
                INSERT INTO users(username, password_hash, salt)
                VALUES(?, ?, ?)
            """, (username, pwd_hash, salt))
            user_id = cursor.lastrowid
            return {"id": user_id, "username": username}
    except sqlite3.IntegrityError:
        return None


def verify_user(username: str, password: str):
    username = username.strip()
    if not username or not password:
        return None

    user = get_user(username)
    if not user:
        return None

    cols = user.keys() if hasattr(user, "keys") else []
    stored_hash = user["password_hash"] if "password_hash" in cols else None
    salt = user["salt"] if "salt" in cols else None

    if stored_hash and salt:
        if _verify_password_hash(password, stored_hash, salt):
            return {"id": user["id"], "username": user["username"]}
        return None

    # Legacy fallback: if user had no password yet, set it now
    if stored_hash is None:
        pwd_hash, new_salt = _hash_password(password)
        conn = _get_connection()
        with conn:
            conn.execute("""
                UPDATE users SET password_hash = ?, salt = ? WHERE id = ?
            """, (pwd_hash, new_salt, user["id"]))
        return {"id": user["id"], "username": user["username"]}

    return None


def get_user(username):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM users
        WHERE username = ?
    """, (username,)).fetchone()


def create_user(username):
    conn = _get_connection()

    with conn:
        conn.execute("""
            INSERT INTO users(username)
            VALUES(?)
        """, (username,))

    return get_user(username)


def get_or_create_user(username):
    user = get_user(username)

    if user is None:
        user = create_user(username)

    return user


def add_exercise(userid, exercise_name, reps, sets, time):
    conn = _get_connection()

    with conn:

        existing = conn.execute("""
            SELECT * FROM exercise_logs
            WHERE user_id = ?
            AND exercise_name = ?
            AND DATE(created_at) = DATE('now')
        """, (userid, exercise_name)).fetchone()

        if existing:
            conn.execute("""
                UPDATE exercise_logs
                SET reps = reps + ?,
                    sets = sets + ?,
                    time = time + ?
                WHERE id = ?
            """, (
                reps,
                sets,
                time,
                existing["id"]
            ))

        else:
            conn.execute("""
                INSERT INTO exercise_logs(
                    user_id,
                    exercise_name,
                    reps,
                    sets,
                    time
                )
                VALUES(?,?,?,?,?)
            """, (
                userid,
                exercise_name,
                reps,
                sets,
                time
            ))


def get_users_exercises(user_id):
    conn = _get_connection()

    return conn.execute("""
        SELECT * FROM exercise_logs
        WHERE user_id = ?
    """, (user_id,)).fetchall()