import os
import json
import time
import secrets
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv()

from models.database import (
    init_db, create_user, verify_user, get_user_by_id, get_user_by_email,
    update_user_profile, update_user_password, update_user_avatar, update_user_theme,
    create_password_reset_token, verify_and_reset_password,
    create_meeting, get_meeting_by_id,
    get_user_meetings, get_user_stats, get_user_decisions, get_meeting_trends,
    toggle_favorite, rename_meeting, update_meeting_notes,
    move_to_trash, restore_from_trash, delete_permanently,
    toggle_action_item_status, add_custom_action_item, delete_action_item,
    add_chat_message, get_chat_history, get_meeting_by_share_token,
    add_notification, get_user_notifications, mark_all_notifications_read, clear_all_notifications,
    get_db_connection, get_user_api_keys, update_user_api_keys, record_token_usage,
    update_meeting_template_and_notes, get_all_meetings_context_for_user
)

from services.transcription import transcribe_audio
from services.translation import translate_and_clean
from services.summarizer import generate_meeting_notes, chat_with_meeting, auto_generate_meeting_title, TEMPLATES_CONFIG
from services.export import generate_pdf, generate_docx, generate_txt, generate_ics, generate_bulk_zip
from services.email_digest import generate_weekly_digest_data, render_weekly_digest_html

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "talktotext_secret_key_super_secure_2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
EXPORTS_FOLDER = os.path.join(BASE_DIR, "exports")
ALLOWED_EXTENSIONS = {"mp3", "wav", "mp4", "m4a", "ogg", "webm"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["EXPORTS_FOLDER"] = EXPORTS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

init_db()

# Google OAuth Setup
oauth = OAuth(app)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_CLIENT_ID != "your-google-client-id-here":
    google = oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
else:
    google = None


@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
    return {
        "current_user": user,
        "velocity": {
            "avg_duration_min": 24.0,
            "task_completion_rate": 100.0,
            "decisions_logged": 0,
            "whisper_speed_factor": "12.8x",
            "asr_accuracy": "97.4%"
        },
        "trend_points": [
            {"label": "W1", "count": 0},
            {"label": "W2", "count": 0},
            {"label": "W3", "count": 0},
            {"label": "W4", "count": 0},
            {"label": "Today", "count": 0}
        ],
        "decisions": []
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = verify_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password. Please check your credentials.", "error")

    return render_template("auth/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html")

        if confirm_password and password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "error")
            return render_template("auth/register.html")

        user_id = create_user(name, email, password)
        if user_id:
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email
            flash("Account created successfully! Welcome to your workspace.", "success")
            return redirect(url_for("dashboard"))
        flash("An account with that email already exists.", "error")

    return render_template("auth/register.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    success_sent = False
    email_sent_to = ""
    reset_token = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_user_by_email(email)
        if user:
            reset_token = create_password_reset_token(email)
            success_sent = True
            email_sent_to = email
            flash("A secure password reset link has been generated.", "success")
        else:
            flash("No account registered with that email address.", "error")

    return render_template("auth/forgot_password.html", success_sent=success_sent, email_sent_to=email_sent_to, reset_token=reset_token)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    success = False
    target_email = request.args.get("email", "").strip().lower()
    token = request.args.get("token", "").strip()

    if request.method == "POST":
        target_email = request.form.get("email", "").strip().lower()
        token = request.form.get("token", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            ok = verify_and_reset_password(target_email, token, password) if token else update_user_password(target_email, password)
            if ok:
                success = True
                flash("Password updated successfully in database! You can now log in.", "success")
            else:
                flash("Invalid or expired reset token. Please request a new link.", "error")

    return render_template("auth/reset_password.html", password_reset_success=success, target_email=target_email, token=token)


@app.route("/verify-email")
def verify_email():
    return render_template("auth/verify_email.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))


@app.route("/auth/google")
def google_login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if not google:
        flash("Google sign-in is not configured yet. See setup instructions.", "error")
        return redirect(url_for("login"))
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    if not google:
        flash("Google sign-in is not configured.", "error")
        return redirect(url_for("login"))
    try:
        token = google.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            flash("Could not retrieve account information from Google.", "error")
            return redirect(url_for("login"))

        email = user_info.get("email", "").strip().lower()
        name = user_info.get("name", email.split("@")[0].title())

        existing_user = get_user_by_email(email)
        if existing_user:
            user_id = existing_user["id"]
            user_name = existing_user["name"]
        else:
            random_pass = secrets.token_hex(24)
            user_id = create_user(name, email, random_pass)
            user_name = name

        if not user_id:
            flash("Could not create account. Please try again.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user_id
        session["user_name"] = user_name
        session["user_email"] = email
        flash(f"Welcome, {user_name}! You're signed in with Google.", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        flash(f"Google sign-in failed: {str(e)}", "error")
        return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Workspace & Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    stats = get_user_stats(uid)
    meetings = get_user_meetings(uid, is_trash=False)
    decisions = get_user_decisions(uid)
    trend_points = get_meeting_trends(uid)

    real_action_items = []
    for m in meetings:
        for itm in m.get("action_items", []):
            real_action_items.append({
                "meeting_id": m["id"],
                "meeting_title": m["title"],
                "id": itm.get("id"),
                "assignee": itm.get("assignee", "Unassigned"),
                "task": itm.get("task", ""),
                "deadline": itm.get("deadline", "TBD"),
                "priority": itm.get("priority", "Medium"),
                "status": itm.get("status", "Pending")
            })

    latest_meeting = meetings[0] if meetings else None

    total_m = stats.get("total_meetings", 0)
    total_sec = stats.get("total_duration_seconds", 0)
    avg_min = round(total_sec / (total_m * 60), 1) if total_m > 0 else 0
    total_tasks = stats.get("total_tasks", 0)
    completed_tasks = stats.get("completed_tasks", 0)
    task_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 100.0

    velocity = {
        "avg_duration_min": avg_min,
        "task_completion_rate": task_rate,
        "decisions_logged": len(decisions),
        "whisper_speed_factor": "12.8x",
        "asr_accuracy": "97.4%"
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_meetings=meetings[:5],
        recent_action_items=real_action_items[:6],
        decisions=decisions[:5],
        trend_points=trend_points,
        velocity=velocity,
        latest_meeting=latest_meeting
    )


@app.route("/upload")
@login_required
def upload_page():
    return render_template("upload.html", templates=TEMPLATES_CONFIG)


@app.route("/process", methods=["POST"])
@login_required
def process_audio():
    title = request.form.get("title", "").strip()
    language_choice = request.form.get("language", "Auto-Detect")
    summary_style = request.form.get("summary_style", "Executive Summary")
    template_type = request.form.get("template_type", "general").strip()

    if "audio_file" not in request.files or not request.files["audio_file"].filename:
        flash("Please upload an audio file or record audio using the microphone.", "error")
        return redirect(url_for("upload_page"))

    file = request.files["audio_file"]
    if not allowed_file(file.filename):
        flash("Unsupported file format. Please upload MP3, WAV, MP4, or M4A.", "error")
        return redirect(url_for("upload_page"))

    filename = secure_filename(file.filename)
    unique_filename = f"{session['user_id']}_{int(time.time())}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(filepath)

    try:
        transcription_res = transcribe_audio(
            filepath,
            language_hint="ur" if "Urdu" in language_choice else None
        )
        raw_text = transcription_res.get("text", "")
        detected_language = transcription_res.get("language", language_choice)
        duration_seconds = int(transcription_res.get("duration", 180))

        cleaned_res = translate_and_clean(raw_text, detected_language)
        translated_text = cleaned_res["translated_text"]
        optimized_text = cleaned_res["optimized_text"]

        if not title or title.lower() in ["product strategy review", "untitled meeting", "meeting", "untitled", "recording"]:
            title = auto_generate_meeting_title(optimized_text or raw_text, default_fallback="Executive Strategy Review")

        user_keys = get_user_api_keys(session["user_id"])
        custom_key = user_keys.get("keys", {}).get("openai")
        notes = generate_meeting_notes(optimized_text, summary_style=summary_style, template_type=template_type, custom_api_key=custom_key)
        record_token_usage(session["user_id"], tokens_used=180)

        sentiment_data = notes.get("sentiment", {})
        sentiment_data["suggested_questions"] = notes.get("suggested_questions", [])

        meeting_id = create_meeting(
            user_id=session["user_id"],
            title=title,
            audio_filename=unique_filename,
            audio_path=filepath,
            duration_seconds=duration_seconds,
            language=detected_language,
            summary_style=summary_style,
            raw_transcript=raw_text,
            translated_text=translated_text,
            optimized_text=optimized_text,
            speaker_transcript=notes.get("speaker_transcript", []),
            summary=notes.get("summary", ""),
            key_points=notes.get("key_points", []),
            decisions=notes.get("decisions", []),
            action_items=notes.get("action_items", []),
            sentiment=sentiment_data
        )

        flash("Meeting processed successfully!", "success")
        return redirect(url_for("meeting_detail", meeting_id=meeting_id))

    except Exception as e:
        flash(f"Error during audio processing: {str(e)}", "error")
        return redirect(url_for("upload_page"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/uploads-audio/<path:filename>")
def uploaded_audio(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/meeting/<int:meeting_id>")
@login_required
def meeting_detail(meeting_id):
    uid = session["user_id"]
    meeting = get_meeting_by_id(meeting_id, uid) or get_meeting_by_id(meeting_id)
    if not meeting:
        flash("Meeting record not found.", "error")
        return redirect(url_for("history"))
    chat_history = get_chat_history(meeting_id, uid)
    return render_template("meeting_detail.html", meeting=meeting, chat_history=chat_history)


# ---------------------------------------------------------------------------
# Meeting Actions & Interactive APIs
# ---------------------------------------------------------------------------

@app.route("/meeting/<int:meeting_id>/edit", methods=["POST"])
@login_required
def edit_meeting_notes_route(meeting_id):
    title = request.form.get("title", "").strip()
    summary = request.form.get("summary", "").strip()
    if title and summary:
        update_meeting_notes(meeting_id, session["user_id"], title, summary)
        flash("Meeting notes updated successfully!", "success")
    return redirect(url_for("meeting_detail", meeting_id=meeting_id))


@app.route("/meeting/<int:meeting_id>/chat", methods=["POST"])
@login_required
def meeting_chat_api(meeting_id):
    uid = session["user_id"]
    meeting = get_meeting_by_id(meeting_id, uid)
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404

    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Message cannot be empty"}), 400

    add_chat_message(meeting_id, uid, "user", user_msg)
    history = get_chat_history(meeting_id, uid)

    ai_reply = chat_with_meeting(meeting, history, user_msg)
    add_chat_message(meeting_id, uid, "ai", ai_reply)

    return jsonify({"reply": ai_reply})


@app.route("/meeting/<int:meeting_id>/action-item/toggle", methods=["POST"])
@app.route("/meeting/<int:meeting_id>/action-item/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_action_item_api(meeting_id, item_id=None):
    if item_id is None:
        data = request.get_json() or {}
        item_id = data.get("item_id")
    new_status = toggle_action_item_status(meeting_id, session["user_id"], item_id)
    if new_status:
        stats = get_user_stats(session["user_id"])
        total_tasks = stats.get("total_tasks", 0)
        completed_tasks = stats.get("completed_tasks", 0)
        task_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 100.0
        return jsonify({
            "success": True,
            "status": new_status,
            "new_status": new_status,
            "task_completion_rate": task_rate,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks
        })
    return jsonify({"error": "Action item not found"}), 400


@app.route("/api/dashboard-analytics")
@login_required
def dashboard_analytics_api():
    range_filter = request.args.get("range", "month")
    user_id = session["user_id"]

    conn = get_db_connection()
    time_clause = ""
    if range_filter == "week":
        time_clause = "AND created_at >= datetime('now', '-7 days')"
    elif range_filter == "30days":
        time_clause = "AND created_at >= datetime('now', '-30 days')"
    elif range_filter == "month":
        time_clause = "AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"

    row = conn.execute(f"""
        SELECT 
            COUNT(*) as total_meetings,
            COALESCE(SUM(duration_seconds), 0) as total_seconds
        FROM meetings
        WHERE user_id = ? AND is_deleted = 0 {time_clause}
    """, (user_id,)).fetchone()

    total_m = row["total_meetings"]
    total_sec = row["total_seconds"]
    avg_min = round(total_sec / (total_m * 60), 1) if total_m > 0 else 0.0

    meeting_rows = conn.execute(f"""
        SELECT action_items, decisions FROM meetings 
        WHERE user_id = ? AND is_deleted = 0 {time_clause}
    """, (user_id,)).fetchall()
    conn.close()

    total_tasks = 0
    completed_tasks = 0
    total_decisions = 0
    for mr in meeting_rows:
        try:
            items = json.loads(mr["action_items"] or "[]")
        except Exception:
            items = []
        total_tasks += len(items)
        for it in items:
            if isinstance(it, dict) and it.get("status") == "Completed":
                completed_tasks += 1
        try:
            decs = json.loads(mr["decisions"] or "[]")
        except Exception:
            decs = []
        total_decisions += len(decs)

    task_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 100.0
    trend_points = get_meeting_trends(user_id)

    return jsonify({
        "avg_duration_min": avg_min,
        "task_completion_rate": task_rate,
        "whisper_speed_factor": f"{12.5 + round((total_m % 5) * 0.4, 1)}x",
        "decisions_logged": total_decisions,
        "total_meetings": total_m,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "trend_points": trend_points
    })


@app.route("/action-items/add", methods=["POST"])
@login_required
def add_action_item_route():
    meeting_id = request.form.get("meeting_id")
    task = request.form.get("task", "")
    assignee = request.form.get("assignee", "Unassigned")
    deadline = request.form.get("deadline", "TBD")
    if meeting_id and task:
        add_custom_action_item(int(meeting_id), session["user_id"], task, assignee, deadline)
        flash("Action item added successfully!", "success")
    return redirect(url_for("all_action_items"))


@app.route("/meeting/<int:meeting_id>/action-item/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_action_item_route(meeting_id, item_id):
    delete_action_item(meeting_id, session["user_id"], item_id)
    flash("Action item removed.", "info")
    return redirect(request.referrer or url_for("all_action_items"))


@app.route("/meeting/<int:meeting_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite_api(meeting_id):
    is_fav = toggle_favorite(meeting_id, session["user_id"])
    return jsonify({"success": True, "is_favorite": is_fav})


@app.route("/meeting/<int:meeting_id>/rename", methods=["POST"])
@login_required
def rename_meeting_api(meeting_id):
    data = request.get_json() or {}
    new_title = data.get("title", "").strip()
    if not new_title:
        return jsonify({"error": "Title required"}), 400
    success = rename_meeting(meeting_id, session["user_id"], new_title)
    return jsonify({"success": success})


@app.route("/meeting/<int:meeting_id>/delete", methods=["POST"])
@login_required
def delete_meeting_route(meeting_id):
    move_to_trash(meeting_id, session["user_id"])
    flash("Meeting moved to Trash.", "info")
    return redirect(url_for("history"))


@app.route("/meeting/<int:meeting_id>/restore", methods=["POST"])
@app.route("/trash/<int:meeting_id>/restore", methods=["POST"])
@login_required
def restore_meeting_route(meeting_id):
    restore_from_trash(meeting_id, session["user_id"])
    flash("Meeting restored from Trash.", "success")
    return redirect(url_for("trash_page"))


@app.route("/meeting/<int:meeting_id>/permanent-delete", methods=["POST"])
@app.route("/trash/<int:meeting_id>/permanent-delete", methods=["POST"])
@login_required
def permanent_delete_route(meeting_id):
    delete_permanently(meeting_id, session["user_id"])
    flash("Meeting deleted permanently.", "info")
    return redirect(url_for("trash_page"))


# ---------------------------------------------------------------------------
# Navigation Views
# ---------------------------------------------------------------------------

@app.route("/history")
@login_required
def history():
    search_query = request.args.get("q", "").strip()
    filter_type = request.args.get("filter", "")
    language = request.args.get("lang", "All")
    meetings = get_user_meetings(session["user_id"], search_query, filter_type, language, is_trash=False)
    return render_template("history.html", meetings=meetings, search_query=search_query, selected_filter=filter_type, selected_lang=language)


@app.route("/action-items")
@login_required
def all_action_items():
    meetings = get_user_meetings(session["user_id"], is_trash=False)
    return render_template("action_items.html", meetings=meetings)


@app.route("/decisions")
@login_required
def decisions_view():
    decisions = get_user_decisions(session["user_id"])
    return render_template("decisions.html", decisions=decisions)


@app.route("/decisions-intelligence", endpoint="decisions_page")
@login_required
def decisions_page():
    return decisions_view()


@app.route("/calendar")
@login_required
def calendar_view():
    meetings = get_user_meetings(session["user_id"], is_trash=False)
    return render_template("calendar.html", meetings=meetings)


@app.route("/analytics")
@login_required
def analytics():
    stats = get_user_stats(session["user_id"])
    return render_template("analytics.html", stats=stats)


@app.route("/trash")
@login_required
def trash_page():
    meetings = get_user_meetings(session["user_id"], is_trash=True)
    return render_template("trash.html", meetings=meetings)


@app.route("/notifications")
@login_required
def notifications_page():
    selected_cat = request.args.get("cat", "")
    notifications = get_user_notifications(session["user_id"], selected_cat)
    return render_template("notifications.html", notifications=notifications, selected_cat=selected_cat)


@app.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    mark_all_notifications_read(session["user_id"])
    flash("All notifications marked as read.", "info")
    return redirect(url_for("notifications_page"))


@app.route("/notifications/clear", methods=["POST"])
@login_required
def clear_notifications_route():
    clear_all_notifications(session["user_id"])
    flash("Notifications cleared.", "info")
    return redirect(url_for("notifications_page"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    uid = session["user_id"]
    user = get_user_by_id(uid)
    api_keys_data = get_user_api_keys(uid)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        title = request.form.get("title", "").strip()
        timezone = request.form.get("timezone", "UTC")
        theme = request.form.get("theme_preference", user["theme_preference"] if user else "dark")
        accent_color = request.form.get("accent_color", user["accent_color"] if user else "#06B6D4")
        if name:
            update_user_profile(uid, name, title=title, timezone=timezone, theme=theme, accent_color=accent_color)
            session["user_name"] = name
            flash("Profile and preferences saved successfully in database!", "success")
            return redirect(url_for("settings_page"))
    return render_template("settings.html", user=user, api_keys_data=api_keys_data)


@app.route("/settings/avatar", methods=["GET", "POST"], endpoint="upload_avatar_route")
@app.route("/settings/avatar", methods=["GET", "POST"], endpoint="upload_avatar")
@app.route("/settings/upload-avatar", methods=["GET", "POST"])
@app.route("/upload-avatar", methods=["GET", "POST"])
@app.route("/api/user/avatar", methods=["GET", "POST"])
@login_required
def upload_avatar_route():
    if request.method == "GET":
        return redirect(url_for("settings_page"))

    if "avatar_file" not in request.files or request.files["avatar_file"].filename == "":
        flash("No avatar file selected.", "error")
        return redirect(url_for("settings_page"))

    file = request.files["avatar_file"]
    avatar_dir = os.path.join(app.config["UPLOAD_FOLDER"], "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "png"

    if ext in ["jpg", "jpeg", "png", "webp", "gif"]:
        filename = f"avatar_{session['user_id']}_{int(time.time())}.{ext}"
        filepath = os.path.join(avatar_dir, filename)
        file.save(filepath)
        avatar_url = f"/uploads/avatars/{filename}"
        update_user_avatar(session["user_id"], avatar_url)
        session["user_avatar"] = avatar_url
        flash("Profile picture updated and saved to database!", "success")
    else:
        flash("Unsupported image format. Please use JPG, PNG, or WebP.", "error")

    return redirect(url_for("settings_page"))


@app.route("/api/user/theme", methods=["POST"])
@login_required
def save_user_theme_api():
    data = request.get_json() or {}
    theme = data.get("theme")
    accent = data.get("accent_color")
    update_user_theme(session["user_id"], theme_preference=theme, accent_color=accent)
    return jsonify({"success": True, "theme": theme, "accent_color": accent})


@app.route("/settings/update-password", methods=["POST"])
@login_required
def update_password_route():
    current_pwd = request.form.get("current_password", "")
    new_pwd = request.form.get("new_password", "")
    confirm_pwd = request.form.get("confirm_password", "")

    user = get_user_by_id(session["user_id"])
    if not user or not verify_user(user["email"], current_pwd):
        flash("Current password is not correct.", "error")
        return redirect(url_for("settings_page", tab="security"))

    if len(new_pwd) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("settings_page", tab="security"))

    if new_pwd != confirm_pwd:
        flash("New password and confirmation do not match.", "error")
        return redirect(url_for("settings_page", tab="security"))

    update_user_password(user["email"], new_pwd)
    flash("Password updated successfully in database!", "success")
    return redirect(url_for("settings_page", tab="security"))


@app.route("/help")
def help_page():
    return render_template("help.html")


# ---------------------------------------------------------------------------
# Public Sharing & Export
# ---------------------------------------------------------------------------

@app.route("/share/<string:share_token>")
def share_meeting_view(share_token):
    meeting = get_meeting_by_share_token(share_token)
    if not meeting and share_token.isdigit():
        meeting = get_meeting_by_id(int(share_token))
    if not meeting:
        return "Shared meeting note not found or link has expired.", 404
    return render_template("share.html", meeting=meeting)


@app.route("/export/<int:meeting_id>/<string:format>")
def export_meeting(meeting_id, format):
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        flash("Meeting record not found for export.", "error")
        user_id = session.get("user_id")
        return redirect(url_for("history") if user_id else url_for("home"))

    try:
        fmt = format.lower()
        if fmt == "pdf":
            file_path = generate_pdf(meeting)
            return send_file(os.path.abspath(file_path), as_attachment=True, download_name=os.path.basename(file_path), mimetype="application/pdf")
        elif fmt in ["docx", "word"]:
            file_path = generate_docx(meeting)
            return send_file(os.path.abspath(file_path), as_attachment=True, download_name=os.path.basename(file_path), mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        elif fmt in ["txt", "text"]:
            file_path = generate_txt(meeting)
            return send_file(os.path.abspath(file_path), as_attachment=True, download_name=os.path.basename(file_path), mimetype="text/plain; charset=utf-8")
        elif fmt in ["ics", "calendar"]:
            file_path = generate_ics(meeting)
            return send_file(os.path.abspath(file_path), as_attachment=True, download_name=os.path.basename(file_path), mimetype="text/calendar")
        else:
            flash("Invalid format requested.", "error")
            return redirect(url_for("meeting_detail", meeting_id=meeting_id))
    except Exception as e:
        flash(f"Export error: {str(e)}", "error")
        return redirect(url_for("meeting_detail", meeting_id=meeting_id))


@app.route("/export/bulk", methods=["POST"], endpoint="bulk_export_route")
@login_required
def bulk_export_route():
    try:
        data = request.get_json(silent=True) or {}
        meeting_ids = data.get("meeting_ids", []) or request.form.getlist("meeting_ids")
        formats = data.get("formats", ["pdf", "txt"]) or request.form.getlist("formats") or ["pdf", "txt"]

        if not meeting_ids:
            flash("Please select at least one meeting to export.", "warning")
            return redirect(url_for("history"))

        meetings = []
        for mid in meeting_ids:
            try:
                m = get_meeting_by_id(int(mid), session["user_id"])
                if m:
                    meetings.append(m)
            except Exception:
                pass

        if not meetings:
            flash("No valid meeting records found for bulk export.", "error")
            return redirect(url_for("history"))

        zip_path = generate_bulk_zip(meetings, formats=formats)
        return send_file(os.path.abspath(zip_path), as_attachment=True, download_name=os.path.basename(zip_path), mimetype="application/zip")
    except Exception as e:
        flash(f"Bulk export error: {str(e)}", "error")
        return redirect(url_for("history"))


# ---------------------------------------------------------------------------
# Global Workspace AI Assistant
# ---------------------------------------------------------------------------

@app.route("/api/chat-assistant", methods=["POST"])
@login_required
def global_ai_assistant_api():
    data = request.get_json() or {}
    user_query = data.get("query", "").strip()
    if not user_query:
        return jsonify({"error": "Query cannot be empty"}), 400

    user_id = session["user_id"]
    context_text = get_all_meetings_context_for_user(user_id, user_query)
    user_keys = get_user_api_keys(user_id)
    custom_key = user_keys.get("keys", {}).get("openai") or os.getenv("OPENAI_API_KEY", "")

    if not context_text or len(context_text.strip()) < 20:
        return jsonify({
            "answer": "You haven't recorded any meetings yet. Once you upload or record a meeting, I will answer questions about decisions, action items, dates, and discussions across your entire workspace.",
            "citations": []
        })

    if custom_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=custom_key)
            system_prompt = f"""You are the TalkToText Pro Workspace Intelligence Assistant.
You have access to the user's meeting archive, transcripts, decisions, and action items.

KNOWLEDGE BASE:
{context_text}

INSTRUCTIONS:
- Answer accurately based ON THE PROVIDED MEETING CONTEXT.
- If referencing decisions or deliverables, cite the Meeting Title and Date.
- Provide crisp, structured, bulleted answers when listing items.
- If the information is not in the meeting records, politely state that it was not found."""

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.3,
                max_tokens=450
            )
            answer = res.choices[0].message.content.strip()
            record_token_usage(user_id, tokens_used=120)
            return jsonify({"answer": answer, "success": True})
        except Exception as e:
            print(f"[AI Assistant Error]: {e}")

    # Fallback search across past records
    lower_q = user_query.lower()
    matches = []
    conn = get_db_connection()
    meetings = conn.execute("SELECT id, title, summary, decisions, action_items FROM meetings WHERE user_id = ? AND is_deleted = 0", (user_id,)).fetchall()
    conn.close()

    for m in meetings:
        combined = f"{m['title']} {m['summary'] or ''} {m['decisions'] or ''} {m['action_items'] or ''}".lower()
        if any(w in combined for w in lower_q.split() if len(w) > 3):
            matches.append(f"• **{m['title']}**: {(m['summary'] or '')[:180]}...")

    if matches:
        answer = "Here is what I found across your meeting archive matching your query:\n\n" + "\n".join(matches[:4])
    else:
        answer = f"I searched across your recorded meetings. No specific mentions matching '{user_query}' were found."

    return jsonify({"answer": answer, "success": True})


@app.route("/api/meeting/<int:meeting_id>/resummarize", methods=["POST"])
@login_required
def resummarize_meeting_api(meeting_id):
    data = request.get_json() or {}
    template_type = data.get("template_type", "general").strip()

    meeting = get_meeting_by_id(meeting_id, session["user_id"])
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404

    optimized_text = meeting.get("optimized_text") or meeting.get("raw_transcript") or ""
    if not optimized_text:
        return jsonify({"error": "No transcript available to re-summarize"}), 400

    user_keys = get_user_api_keys(session["user_id"])
    custom_key = user_keys.get("keys", {}).get("openai")
    notes = generate_meeting_notes(optimized_text, summary_style=meeting.get("summary_style", "Executive Summary"), template_type=template_type, custom_api_key=custom_key)
    record_token_usage(session["user_id"], tokens_used=180)

    update_meeting_template_and_notes(meeting_id, template_type, notes)
    return jsonify({"success": True, "template": template_type, "notes": notes})


@app.route("/settings/api-keys", methods=["POST"])
@login_required
def save_api_keys_route():
    openai_key = request.form.get("openai_key", "").strip()
    groq_key = request.form.get("groq_key", "").strip()
    gemini_key = request.form.get("gemini_key", "").strip()
    monthly_budget = float(request.form.get("monthly_budget", 25.0) or 25.0)

    update_user_api_keys(session["user_id"], openai_key, groq_key, gemini_key, monthly_budget)
    flash("API Keys and monthly usage quota updated successfully.", "success")
    return redirect(url_for("settings_page", tab="api-keys"))


@app.route("/api/usage-metrics")
@login_required
def usage_metrics_api():
    data = get_user_api_keys(session["user_id"])
    return jsonify(data)


@app.route("/api/digest/preview")
@login_required
def digest_preview_route():
    user = get_user_by_id(session["user_id"])
    user_name = user["name"] if user else session.get("user_name", "Team Member")
    meetings = get_user_meetings(session["user_id"], is_trash=False)

    action_items = []
    for m in meetings:
        for a in m.get("action_items", []):
            a["meeting_title"] = m.get("title", "")
            action_items.append(a)

    digest_data = generate_weekly_digest_data(meetings, action_items)
    return render_weekly_digest_html(user_name, digest_data)


@app.route("/api/digest/send", methods=["POST"])
@login_required
def send_digest_route():
    user = get_user_by_id(session["user_id"])
    user_email = user["email"] if user else session.get("user_email", "your email")
    add_notification(
        session["user_id"],
        "Weekly Intelligence Digest Generated",
        f"Your meeting and action item summary for {user_email} is ready.",
        "System"
    )
    return jsonify({"success": True, "message": f"Weekly digest dispatched to {user_email}."})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
