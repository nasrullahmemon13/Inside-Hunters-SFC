import os
import json
import uuid
import sqlite3
import threading
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("NOW_REGION"))

if IS_SERVERLESS:
    import shutil
    DB_DIR = "/tmp/database"
    DB_PATH = os.path.join(DB_DIR, "app.db")
    orig_db = os.path.join(BASE_DIR, "database", "app.db")
    os.makedirs(DB_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH) and os.path.exists(orig_db):
        try:
            shutil.copy2(orig_db, DB_PATH)
        except Exception:
            pass
else:
    DB_DIR = os.path.join(BASE_DIR, "database")
    DB_PATH = os.path.join(DB_DIR, "app.db")
    os.makedirs(DB_DIR, exist_ok=True)

MONGO_URI = os.getenv("MONGO_URI", "").strip()
_mongo_client = None
_mongo_db = None


def get_mongo_db():
    """Returns the MongoDB database instance if configured, or None."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    if MONGO_URI:
        try:
            _mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
            _mongo_db = _mongo_client.get_database("talktotext_pro")
            return _mongo_db
        except Exception as err:
            print(f"[MongoDB connection notice]: {err}")
            _mongo_db = None
    return None


def _sync_mongo_safe(collection_name, operation, *args, **kwargs):
    """Executes a MongoDB operation safely in a background or inline block without failing main flow."""
    try:
        db = get_mongo_db()
        if db is not None:
            col = getattr(db, collection_name)
            op = getattr(col, operation)
            op(*args, **kwargs)
    except Exception as err:
        print(f"[MongoDB sync notice on {collection_name}.{operation}]: {err}")


def _run_mongo_sync_worker():
    """Performs a full sync of all local SQLite users and active meetings to MongoDB Atlas."""
    db = get_mongo_db()
    if db is None:
        return

    try:
        conn = get_db_connection()

        users = [dict(u) for u in conn.execute("SELECT * FROM users").fetchall()]
        for u in users:
            uid = u["id"]
            db.users.update_one(
                {"sqlite_id": uid},
                {"$set": {
                    "sqlite_id": uid,
                    "name": u.get("name"),
                    "email": u.get("email"),
                    "password_hash": u.get("password_hash"),
                    "title": u.get("title"),
                    "timezone": u.get("timezone"),
                    "theme_preference": u.get("theme_preference", "dark"),
                    "accent_color": u.get("accent_color", "#06B6D4"),
                    "avatar_url": u.get("avatar_url", ""),
                    "reset_token": u.get("reset_token", ""),
                    "created_at": u.get("created_at")
                }},
                upsert=True
            )

        meetings = [dict(m) for m in conn.execute("SELECT * FROM meetings WHERE is_deleted = 0").fetchall()]
        for m in meetings:
            mid = m["id"]
            db.meetings.update_one(
                {"sqlite_id": mid},
                {"$set": {
                    "sqlite_id": mid,
                    "user_id": m.get("user_id"),
                    "title": m.get("title"),
                    "audio_filename": m.get("audio_filename"),
                    "duration_seconds": m.get("duration_seconds"),
                    "language": m.get("language"),
                    "summary_style": m.get("summary_style"),
                    "summary": m.get("summary"),
                    "key_points": m.get("key_points"),
                    "decisions": m.get("decisions"),
                    "action_items": m.get("action_items"),
                    "sentiment": m.get("sentiment"),
                    "status": m.get("status"),
                    "is_favorite": m.get("is_favorite"),
                    "share_token": m.get("share_token"),
                    "created_at": m.get("created_at")
                }},
                upsert=True
            )

        conn.close()
    except Exception as err:
        print(f"[MongoDB full sync notice]: {err}")


def sync_sqlite_to_mongodb():
    """Launches full synchronization to MongoDB in a daemon thread."""
    threading.Thread(target=_run_mongo_sync_worker, daemon=True).start()


def get_db_connection():
    """Creates and returns a connection to SQLite with row factory enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables, applies schema migrations, and creates indices."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        title TEXT DEFAULT 'Product Team',
        timezone TEXT DEFAULT 'UTC',
        theme_preference TEXT DEFAULT 'light',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        audio_filename TEXT,
        audio_path TEXT,
        duration_seconds INTEGER DEFAULT 0,
        language TEXT DEFAULT 'English',
        summary_style TEXT DEFAULT 'Executive Summary',
        raw_transcript TEXT,
        translated_text TEXT,
        optimized_text TEXT,
        speaker_transcript TEXT,
        summary TEXT,
        key_points TEXT,
        decisions TEXT,
        action_items TEXT,
        sentiment TEXT,
        is_favorite INTEGER DEFAULT 0,
        is_archived INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        share_token TEXT UNIQUE,
        status TEXT DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT DEFAULT 'Meetings',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # User schema migrations
    user_cols = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    user_migrations = [
        ("title", "TEXT DEFAULT 'Product Team'"),
        ("timezone", "TEXT DEFAULT 'UTC'"),
        ("theme_preference", "TEXT DEFAULT 'dark'"),
        ("accent_color", "TEXT DEFAULT '#06B6D4'"),
        ("avatar_url", "TEXT DEFAULT ''"),
        ("reset_token", "TEXT DEFAULT ''"),
        ("custom_api_keys", "TEXT DEFAULT '{}'"),
        ("token_usage", "INTEGER DEFAULT 0"),
        ("monthly_budget", "REAL DEFAULT 25.0")
    ]
    for col_name, col_def in user_migrations:
        if col_name not in user_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

    # Meeting schema migrations
    meeting_cols = [row[1] for row in cursor.execute("PRAGMA table_info(meetings)").fetchall()]
    meeting_migrations = [
        ("duration_seconds", "INTEGER DEFAULT 0"),
        ("summary_style", "TEXT DEFAULT 'Executive Summary'"),
        ("template_type", "TEXT DEFAULT 'general'"),
        ("speaker_transcript", "TEXT"),
        ("is_favorite", "INTEGER DEFAULT 0"),
        ("is_archived", "INTEGER DEFAULT 0"),
        ("is_deleted", "INTEGER DEFAULT 0"),
        ("share_token", "TEXT")
    ]
    for col_name, col_def in meeting_migrations:
        if col_name not in meeting_cols:
            cursor.execute(f"ALTER TABLE meetings ADD COLUMN {col_name} {col_def}")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_user_del ON meetings(user_id, is_deleted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_share ON meetings(share_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read)")

    conn.commit()
    conn.close()

    sync_sqlite_to_mongodb()


# ---------------------------------------------------------------------------
# User Management & Profile
# ---------------------------------------------------------------------------

def create_user(name, email, password):
    """Creates a new user with hashed password and default preferences."""
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    clean_email = email.strip().lower()
    clean_name = name.strip()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, theme_preference, accent_color, avatar_url) VALUES (?, ?, ?, 'dark', '#06B6D4', '')",
            (clean_name, clean_email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        add_notification(user_id, "Welcome to TalkToText Pro", "Your account has been created. Create or record your first meeting.", "System")

        _sync_mongo_safe("users", "update_one",
            {"email": clean_email},
            {"$set": {
                "sqlite_id": user_id,
                "name": clean_name,
                "email": clean_email,
                "password_hash": password_hash,
                "title": "Product Team",
                "timezone": "UTC",
                "theme_preference": "dark",
                "accent_color": "#06B6D4",
                "avatar_url": "",
                "reset_token": "",
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }},
            upsert=True
        )
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user_by_email(email):
    """Retrieves user by email address."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Retrieves user by primary key ID."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def verify_user(email, password):
    """Verifies user credentials and returns user record on match."""
    user = get_user_by_email(email)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def create_password_reset_token(email):
    """Generates a secure password reset token and stores it on the user record."""
    token = secrets.token_urlsafe(24)
    clean_email = email.strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, clean_email))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected > 0:
        _sync_mongo_safe("users", "update_one", {"email": clean_email}, {"$set": {"reset_token": token}})
        return token
    return None


def verify_and_reset_password(email, token, new_password):
    """Resets password if reset token matches the user record."""
    clean_email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE email = ? AND reset_token = ?", (clean_email, token.strip())).fetchone()
    if not user:
        conn.close()
        return False

    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, reset_token = '' WHERE email = ?", (password_hash, clean_email))
    conn.commit()
    conn.close()

    _sync_mongo_safe("users", "update_one", {"email": clean_email}, {"$set": {"password_hash": password_hash, "reset_token": ""}})
    return True


def update_user_password(email, new_password):
    """Updates password directly for an authenticated user."""
    clean_email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, clean_email))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("users", "update_one", {"email": clean_email}, {"$set": {"password_hash": password_hash}})
    return affected > 0


def update_user_avatar(user_id, avatar_url):
    """Updates the user's avatar image URL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (avatar_url, user_id))
    conn.commit()
    conn.close()

    _sync_mongo_safe("users", "update_one", {"sqlite_id": user_id}, {"$set": {"avatar_url": avatar_url}})


def update_user_theme(user_id, theme_preference=None, accent_color=None):
    """Updates the user's theme mode and accent color preference."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET theme_preference = COALESCE(?, theme_preference),
            accent_color = COALESCE(?, accent_color)
        WHERE id = ?
    """, (theme_preference, accent_color, user_id))
    conn.commit()
    conn.close()

    updates = {}
    if theme_preference:
        updates["theme_preference"] = theme_preference
    if accent_color:
        updates["accent_color"] = accent_color
    if updates:
        _sync_mongo_safe("users", "update_one", {"sqlite_id": user_id}, {"$set": updates})


def update_user_profile(user_id, name=None, title=None, timezone=None, theme=None, accent_color=None, avatar_url=None):
    """Updates full user profile information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET name = COALESCE(?, name),
            title = COALESCE(?, title),
            timezone = COALESCE(?, timezone),
            theme_preference = COALESCE(?, theme_preference),
            accent_color = COALESCE(?, accent_color),
            avatar_url = COALESCE(?, avatar_url)
        WHERE id = ?
    """, (name, title, timezone, theme, accent_color, avatar_url, user_id))
    conn.commit()
    conn.close()

    updates = {}
    if name: updates["name"] = name
    if title: updates["title"] = title
    if timezone: updates["timezone"] = timezone
    if theme: updates["theme_preference"] = theme
    if accent_color: updates["accent_color"] = accent_color
    if avatar_url: updates["avatar_url"] = avatar_url
    if updates:
        _sync_mongo_safe("users", "update_one", {"sqlite_id": user_id}, {"$set": updates})


def get_user_api_keys(user_id):
    """Retrieves custom API keys, budget settings, and token usage for the user."""
    conn = get_db_connection()
    user = conn.execute("SELECT custom_api_keys, token_usage, monthly_budget FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        try:
            keys = json.loads(user["custom_api_keys"] or "{}")
        except Exception:
            keys = {}
        usage = user["token_usage"] or 0
        budget = user["monthly_budget"] or 25.0
        return {
            "keys": keys,
            "token_usage": usage,
            "monthly_budget": budget,
            "estimated_cost": round(usage * 0.00000015, 4)
        }
    return {"keys": {}, "token_usage": 0, "monthly_budget": 25.0, "estimated_cost": 0.0}


def update_user_api_keys(user_id, openai_key="", groq_key="", gemini_key="", monthly_budget=25.0):
    """Updates user-specific custom API keys and monthly budget."""
    conn = get_db_connection()
    keys_dict = {
        "openai": openai_key.strip(),
        "groq": groq_key.strip(),
        "gemini": gemini_key.strip()
    }
    conn.execute(
        "UPDATE users SET custom_api_keys = ?, monthly_budget = ? WHERE id = ?",
        (json.dumps(keys_dict), float(monthly_budget), user_id)
    )
    conn.commit()
    conn.close()
    sync_sqlite_to_mongodb()
    return True


def record_token_usage(user_id, tokens_used=150):
    """Increments the token usage count for the given user."""
    try:
        conn = get_db_connection()
        conn.execute("UPDATE users SET token_usage = COALESCE(token_usage, 0) + ? WHERE id = ?", (int(tokens_used), user_id))
        conn.commit()
        conn.close()
    except Exception as err:
        print(f"[Token record error]: {err}")


# ---------------------------------------------------------------------------
# Meeting Management & Data Access
# ---------------------------------------------------------------------------

def create_meeting(user_id, title, audio_filename, audio_path, duration_seconds=180,
                   language="English", summary_style="Executive Summary",
                   raw_transcript="", translated_text="", optimized_text="",
                   speaker_transcript=None, summary="", key_points=None,
                   decisions=None, action_items=None, sentiment=None, status="completed"):
    """Persists a new meeting record with parsed transcript and intelligence fields."""
    conn = get_db_connection()
    cursor = conn.cursor()

    key_points_str = json.dumps(key_points or [])
    decisions_str = json.dumps(decisions or [])

    items_with_ids = []
    for idx, item in enumerate(action_items or []):
        if isinstance(item, dict):
            items_with_ids.append({
                "id": idx + 1,
                "assignee": item.get("assignee", "Unassigned"),
                "task": item.get("task", ""),
                "deadline": item.get("deadline", "TBD"),
                "priority": item.get("priority", "Medium"),
                "status": item.get("status", "Pending")
            })
        elif isinstance(item, str):
            items_with_ids.append({
                "id": idx + 1,
                "assignee": "Unassigned",
                "task": item,
                "deadline": "TBD",
                "priority": "Medium",
                "status": "Pending"
            })
    action_items_str = json.dumps(items_with_ids)
    speaker_transcript_str = json.dumps(speaker_transcript or [])
    sentiment_str = json.dumps(sentiment or {
        "overall": "Positive", "score": 85,
        "positive_pct": 75, "neutral_pct": 20, "negative_pct": 5,
        "tone": "Constructive & Aligned", "insights": "Clear alignment."
    })
    share_token = str(uuid.uuid4())[:12]

    cursor.execute("""
        INSERT INTO meetings (
            user_id, title, audio_filename, audio_path, duration_seconds, language,
            summary_style, raw_transcript, translated_text, optimized_text,
            speaker_transcript, summary, key_points, decisions, action_items,
            sentiment, is_favorite, is_archived, is_deleted, share_token, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
    """, (
        user_id, title, audio_filename, audio_path, duration_seconds, language,
        summary_style, raw_transcript, translated_text, optimized_text,
        speaker_transcript_str, summary, key_points_str, decisions_str, action_items_str,
        sentiment_str, share_token, status
    ))
    conn.commit()
    meeting_id = cursor.lastrowid
    conn.close()

    add_notification(user_id, "Meeting notes ready", f"Notes for '{title}' have been generated successfully.", "Meetings")

    _sync_mongo_safe("meetings", "insert_one", {
        "sqlite_id": meeting_id,
        "user_id": user_id,
        "title": title,
        "audio_filename": audio_filename,
        "audio_path": audio_path,
        "duration_seconds": duration_seconds,
        "language": language,
        "summary_style": summary_style,
        "raw_transcript": raw_transcript,
        "translated_text": translated_text,
        "optimized_text": optimized_text,
        "speaker_transcript": speaker_transcript or [],
        "summary": summary,
        "key_points": key_points or [],
        "decisions": decisions or [],
        "action_items": items_with_ids,
        "sentiment": sentiment or {},
        "is_favorite": 0,
        "is_archived": 0,
        "is_deleted": 0,
        "share_token": share_token,
        "status": status,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    return meeting_id


def parse_meeting_row(meeting):
    """Converts SQLite meeting Row into structured Python dictionary with decoded JSON fields."""
    if not meeting:
        return None
    m = dict(meeting)
    try:
        m["key_points"] = json.loads(m.get("key_points") or "[]")
    except Exception:
        m["key_points"] = []

    try:
        m["decisions"] = json.loads(m.get("decisions") or "[]")
    except Exception:
        m["decisions"] = []

    try:
        raw_items = json.loads(m.get("action_items") or "[]")
    except Exception:
        raw_items = []

    parsed_items = []
    for idx, itm in enumerate(raw_items):
        if isinstance(itm, dict):
            item_id = itm.get("id")
            if item_id is None:
                item_id = idx + 1
            parsed_items.append({
                "id": int(item_id) if str(item_id).isdigit() else (idx + 1),
                "task": itm.get("task", ""),
                "assignee": itm.get("assignee", "Unassigned"),
                "deadline": itm.get("deadline", "TBD"),
                "priority": itm.get("priority", "Medium"),
                "status": itm.get("status", "Pending")
            })
        elif isinstance(itm, str):
            parsed_items.append({
                "id": idx + 1,
                "task": itm,
                "assignee": "Unassigned",
                "deadline": "TBD",
                "priority": "Medium",
                "status": "Pending"
            })
    m["action_items"] = parsed_items

    try:
        m["sentiment"] = json.loads(m.get("sentiment") or "{}")
    except Exception:
        m["sentiment"] = {}

    try:
        m["speaker_transcript"] = json.loads(m.get("speaker_transcript") or "[]")
    except Exception:
        m["speaker_transcript"] = []

    sq = m["sentiment"].get("suggested_questions") if isinstance(m["sentiment"], dict) else []
    if not sq:
        sq = [
            f"What was the main outcome of {m.get('title', 'this meeting')}?",
            "What are the assigned action items and deadlines?",
            "What decisions were confirmed during the discussion?",
            "What was the overall voice mood, tone, and slang usage?"
        ]
    m["suggested_questions"] = sq
    return m


def get_meeting_by_id(meeting_id, user_id=None):
    """Retrieves a single meeting by ID, optionally filtered by user_id."""
    conn = get_db_connection()
    query = "SELECT * FROM meetings WHERE id = ?"
    params = [meeting_id]
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    meeting = conn.execute(query, tuple(params)).fetchone()
    conn.close()
    return parse_meeting_row(meeting)


def get_meeting_by_share_token(token):
    """Retrieves an active public meeting record by its unique share token."""
    conn = get_db_connection()
    meeting = conn.execute("SELECT * FROM meetings WHERE share_token = ? AND is_deleted = 0", (token,)).fetchone()
    conn.close()
    return parse_meeting_row(meeting)


def get_user_meetings(user_id, search_query=None, filter_type=None, language=None, is_trash=False):
    """Retrieves a filtered list of meeting records for the user."""
    conn = get_db_connection()
    query = "SELECT * FROM meetings WHERE user_id = ?"
    params = [user_id]

    if is_trash:
        query += " AND is_deleted = 1"
    else:
        query += " AND is_deleted = 0"
        if filter_type == "favorites":
            query += " AND is_favorite = 1"
        elif filter_type in ("today", "recent"):
            query += " AND (DATE(created_at) = DATE('now') OR created_at >= datetime('now', '-7 days'))"
        elif filter_type == "shared":
            query += " AND (share_token IS NOT NULL AND share_token != '')"
        elif filter_type == "week":
            query += " AND created_at >= datetime('now', '-7 days')"
        elif filter_type == "month":
            query += " AND created_at >= datetime('now', '-30 days')"

    if language and language != "All":
        query += " AND language LIKE ?"
        params.append(f"%{language}%")

    if search_query:
        query += " AND (title LIKE ? OR summary LIKE ? OR raw_transcript LIKE ? OR speaker_transcript LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY created_at DESC"
    meetings = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return [parse_meeting_row(m) for m in meetings]


def get_user_decisions(user_id):
    """Aggregates all recorded decisions across the user's active meetings."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, title, created_at, decisions FROM meetings WHERE user_id = ? AND is_deleted = 0 ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    all_decisions = []
    for r in rows:
        try:
            decisions_list = json.loads(r["decisions"] or "[]")
        except Exception:
            decisions_list = []

        for d in decisions_list:
            if isinstance(d, dict):
                all_decisions.append({
                    "meeting_id": r["id"],
                    "meeting_title": r["title"],
                    "created_at": r["created_at"],
                    "decision": d.get("decision", ""),
                    "category": d.get("category", "Strategy"),
                    "impact": d.get("impact", "High")
                })
            elif isinstance(d, str) and d.strip():
                all_decisions.append({
                    "meeting_id": r["id"],
                    "meeting_title": r["title"],
                    "created_at": r["created_at"],
                    "decision": d.strip(),
                    "category": "Strategy",
                    "impact": "High"
                })
    return all_decisions


def get_user_stats(user_id):
    """Calculates summary metrics including total meetings, duration, tasks, and recent records."""
    conn = get_db_connection()
    stats = conn.execute("""
        SELECT 
            COUNT(CASE WHEN is_deleted = 0 THEN 1 END) as total_meetings,
            COUNT(CASE WHEN is_deleted = 0 AND created_at >= datetime('now', '-7 days') THEN 1 END) as week_meetings,
            COALESCE(SUM(CASE WHEN is_deleted = 0 THEN duration_seconds ELSE 0 END), 0) as total_seconds,
            COUNT(CASE WHEN is_deleted = 0 AND is_favorite = 1 THEN 1 END) as favorites_count,
            COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as trash_count
        FROM meetings
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    all_user_meetings = conn.execute(
        "SELECT action_items FROM meetings WHERE user_id = ? AND is_deleted = 0", (user_id,)
    ).fetchall()

    total_tasks = 0
    completed_tasks = 0
    for row in all_user_meetings:
        try:
            items = json.loads(row["action_items"] or "[]")
        except Exception:
            items = []
        total_tasks += len(items)
        for i in items:
            if isinstance(i, dict) and i.get("status") == "Completed":
                completed_tasks += 1

    recent_meetings = conn.execute(
        "SELECT * FROM meetings WHERE user_id = ? AND is_deleted = 0 ORDER BY created_at DESC LIMIT 5", (user_id,)
    ).fetchall()
    conn.close()

    total_meetings = stats["total_meetings"]
    week_meetings = stats["week_meetings"]
    total_seconds = stats["total_seconds"]
    favorites_count = stats["favorites_count"]
    trash_count = stats["trash_count"]

    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    dur_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

    return {
        "total_meetings": total_meetings,
        "week_meetings": week_meetings,
        "total_duration_str": dur_str,
        "total_duration_seconds": total_seconds,
        "favorites_count": favorites_count,
        "trash_count": trash_count,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": total_tasks - completed_tasks,
        "recent_meetings": [parse_meeting_row(m) for m in recent_meetings]
    }


def get_meeting_trends(user_id):
    """Returns meeting frequency trend data points grouped by date."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT strftime('%m/%d', created_at) as day_date, COUNT(*) as count
        FROM meetings
        WHERE user_id = ? AND is_deleted = 0
        GROUP BY day_date
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id,)).fetchall()
    conn.close()

    points = [{"label": r["day_date"], "count": r["count"]} for r in reversed(rows)]
    if len(points) < 5:
        dummy_labels = ["W1", "W2", "W3", "W4", "Current"]
        pad_needed = 5 - len(points)
        padded = [{"label": dummy_labels[i], "count": 0} for i in range(pad_needed)] + points
        return padded
    return points


def toggle_favorite(meeting_id, user_id):
    """Toggles favorite status on a meeting and returns the new boolean state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE meetings
        SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND user_id = ?
    """, (meeting_id, user_id))
    conn.commit()
    new_val = conn.execute("SELECT is_favorite FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()

    val = bool(new_val["is_favorite"]) if new_val else False
    _sync_mongo_safe("meetings", "update_one",
        {"sqlite_id": meeting_id, "user_id": user_id},
        {"$set": {"is_favorite": 1 if val else 0}}
    )
    return val


def rename_meeting(meeting_id, user_id, new_title):
    """Renames meeting title."""
    clean_title = new_title.strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET title = ? WHERE id = ? AND user_id = ?", (clean_title, meeting_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one",
        {"sqlite_id": meeting_id, "user_id": user_id},
        {"$set": {"title": clean_title}}
    )
    return affected > 0


def update_meeting_notes(meeting_id, user_id, title, summary, key_points=None, decisions=None):
    """Updates editable notes fields for a meeting record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    params = [title.strip(), summary.strip()]
    updates = ["title = ?", "summary = ?"]
    if key_points is not None:
        updates.append("key_points = ?")
        params.append(json.dumps(key_points))
    if decisions is not None:
        updates.append("decisions = ?")
        params.append(json.dumps(decisions))
    params.extend([meeting_id, user_id])

    cursor.execute(f"UPDATE meetings SET {', '.join(updates)} WHERE id = ? AND user_id = ?", tuple(params))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    mongo_update = {"title": title.strip(), "summary": summary.strip()}
    if key_points is not None:
        mongo_update["key_points"] = key_points
    if decisions is not None:
        mongo_update["decisions"] = decisions
    _sync_mongo_safe("meetings", "update_one", {"sqlite_id": meeting_id, "user_id": user_id}, {"$set": mongo_update})
    return affected > 0


def update_meeting_template_and_notes(meeting_id, template_type, notes_dict):
    """Updates template classification and regenerated intelligence data for a meeting."""
    conn = get_db_connection()
    conn.execute("""
        UPDATE meetings 
        SET template_type = ?,
            summary = ?,
            key_points = ?,
            decisions = ?,
            action_items = ?,
            sentiment = ?
        WHERE id = ?
    """, (
        template_type,
        notes_dict.get('summary', ''),
        json.dumps(notes_dict.get('key_points', [])),
        json.dumps(notes_dict.get('decisions', [])),
        json.dumps(notes_dict.get('action_items', [])),
        json.dumps(notes_dict.get('sentiment', {})),
        meeting_id
    ))
    conn.commit()
    conn.close()
    sync_sqlite_to_mongodb()
    return True


def move_to_trash(meeting_id, user_id):
    """Flags a meeting as deleted (soft delete)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET is_deleted = 1 WHERE id = ? AND user_id = ?", (meeting_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one", {"sqlite_id": meeting_id, "user_id": user_id}, {"$set": {"is_deleted": 1}})
    return affected > 0


def restore_from_trash(meeting_id, user_id):
    """Restores a soft-deleted meeting from trash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET is_deleted = 0 WHERE id = ? AND user_id = ?", (meeting_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one", {"sqlite_id": meeting_id, "user_id": user_id}, {"$set": {"is_deleted": 0}})
    return affected > 0


def delete_permanently(meeting_id, user_id):
    """Permanently deletes a meeting record from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meetings WHERE id = ? AND user_id = ?", (meeting_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "delete_one", {"sqlite_id": meeting_id, "user_id": user_id})
    return affected > 0


# ---------------------------------------------------------------------------
# Action Items Operations
# ---------------------------------------------------------------------------

def toggle_action_item_status(meeting_id, user_id, item_id):
    """Toggles completion status of a specific action item within a meeting."""
    conn = get_db_connection()
    meeting = get_meeting_by_id(meeting_id, user_id) or get_meeting_by_id(meeting_id)
    if not meeting:
        conn.close()
        return None

    items = meeting["action_items"]
    updated_status = "Pending"
    for item in items:
        if str(item.get("id")) == str(item_id):
            item["status"] = "Completed" if item.get("status") != "Completed" else "Pending"
            updated_status = item["status"]
            break

    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET action_items = ? WHERE id = ? AND user_id = ?", (json.dumps(items), meeting_id, user_id))
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one",
        {"sqlite_id": meeting_id, "user_id": user_id},
        {"$set": {"action_items": items}}
    )
    return updated_status


def add_custom_action_item(meeting_id, user_id, task, assignee, deadline, priority="Medium"):
    """Appends a new manually entered action item to an existing meeting."""
    conn = get_db_connection()
    meeting = get_meeting_by_id(meeting_id, user_id)
    if not meeting:
        conn.close()
        return None

    items = meeting["action_items"]
    new_id = len(items) + 1
    new_item = {
        "id": new_id,
        "task": task.strip(),
        "assignee": assignee.strip() or "Unassigned",
        "deadline": deadline.strip() or "TBD",
        "priority": priority,
        "status": "Pending"
    }
    items.append(new_item)

    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET action_items = ? WHERE id = ? AND user_id = ?", (json.dumps(items), meeting_id, user_id))
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one",
        {"sqlite_id": meeting_id, "user_id": user_id},
        {"$set": {"action_items": items}}
    )
    return new_item


def delete_action_item(meeting_id, user_id, item_id):
    """Deletes an action item from a meeting's action item list."""
    conn = get_db_connection()
    meeting = get_meeting_by_id(meeting_id, user_id)
    if not meeting:
        conn.close()
        return False

    items = meeting["action_items"]
    filtered_items = [i for i in items if str(i.get("id")) != str(item_id)]
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET action_items = ? WHERE id = ? AND user_id = ?", (json.dumps(filtered_items), meeting_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    _sync_mongo_safe("meetings", "update_one",
        {"sqlite_id": meeting_id, "user_id": user_id},
        {"$set": {"action_items": filtered_items}}
    )
    return affected > 0


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def add_notification(user_id, title, message, category="Meetings"):
    """Inserts a system or meeting notification for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notifications (user_id, title, message, category) VALUES (?, ?, ?, ?)",
                   (user_id, title, message, category))
    conn.commit()
    conn.close()

    _sync_mongo_safe("notifications", "insert_one", {
        "user_id": user_id,
        "title": title,
        "message": message,
        "category": category,
        "is_read": 0,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })


def get_user_notifications(user_id, category=None):
    """Retrieves up to 30 recent notifications for the user."""
    conn = get_db_connection()
    if category and category != "All":
        notes = conn.execute("SELECT * FROM notifications WHERE user_id = ? AND category = ? ORDER BY created_at DESC LIMIT 30", (user_id, category)).fetchall()
    else:
        notes = conn.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 30", (user_id,)).fetchall()
    conn.close()
    return [dict(n) for n in notes]


def mark_all_notifications_read(user_id):
    """Marks all unread notifications as read for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    _sync_mongo_safe("notifications", "update_many", {"user_id": user_id}, {"$set": {"is_read": 1}})


def clear_all_notifications(user_id):
    """Deletes all notifications for the specified user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    _sync_mongo_safe("notifications", "delete_many", {"user_id": user_id})


# ---------------------------------------------------------------------------
# Meeting Chat & AI Assistant Context
# ---------------------------------------------------------------------------

def add_chat_message(meeting_id, user_id, sender, message):
    """Logs a user or assistant chat message for meeting Q&A."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO meeting_chats (meeting_id, user_id, sender, message) VALUES (?, ?, ?, ?)",
                   (meeting_id, user_id, sender, message))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()

    _sync_mongo_safe("meeting_chats", "insert_one", {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "sender": sender,
        "message": message,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    return msg_id


def get_chat_history(meeting_id, user_id):
    """Retrieves chat thread for a meeting."""
    conn = get_db_connection()
    chats = conn.execute("SELECT * FROM meeting_chats WHERE meeting_id = ? AND user_id = ? ORDER BY created_at ASC", (meeting_id, user_id)).fetchall()
    conn.close()
    return [dict(c) for c in chats]


def get_all_meetings_context_for_user(user_id, query_text=""):
    """Compiles structured contextual knowledge across past meetings for global workspace assistant queries."""
    conn = get_db_connection()
    meetings = conn.execute("""
        SELECT id, title, created_at, language, summary, key_points, decisions, action_items, sentiment, template_type
        FROM meetings
        WHERE user_id = ? AND is_deleted = 0
        ORDER BY created_at DESC
        LIMIT 25
    """, (user_id,)).fetchall()
    conn.close()

    context_blocks = []
    for m in meetings:
        m_dict = dict(m)
        try:
            kps = json.loads(m_dict.get('key_points') or '[]')
        except Exception:
            kps = []
        try:
            decs = json.loads(m_dict.get('decisions') or '[]')
        except Exception:
            decs = []
        try:
            acts = json.loads(m_dict.get('action_items') or '[]')
        except Exception:
            acts = []

        date_str = m_dict.get('created_at', '')[:10]
        template = m_dict.get('template_type', 'general')
        block = f"--- MEETING #{m_dict['id']}: {m_dict['title']} (Date: {date_str}, Template: {template}) ---\n"
        block += f"SUMMARY: {m_dict.get('summary', '')}\n"
        if decs:
            block += f"DECISIONS: {', '.join(decs)}\n"
        if acts:
            tasks_str = "; ".join([f"{a.get('task', '')} (Assignee: {a.get('assignee', 'Team')}, Due: {a.get('deadline', 'TBD')})" for a in acts])
            block += f"ACTION ITEMS: {tasks_str}\n"
        if kps:
            block += f"KEY POINTS: {', '.join(kps[:4])}\n"
        context_blocks.append(block)

    return "\n".join(context_blocks)
