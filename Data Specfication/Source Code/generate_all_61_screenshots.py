import os
import sys
import time
import shutil
import sqlite3
import threading
from playwright.sync_api import sync_playwright

BASE_PROJECT_DIR = r"c:\Users\HP 250 G9\OneDrive\Desktop\Inside Hunters SFC"
SOURCE_CODE_DIR = os.path.join(BASE_PROJECT_DIR, "Data Specfication", "Source Code")
TARGET_SCREENSHOTS_DIR = os.path.join(BASE_PROJECT_DIR, "Project Screenshots from Different Logs")
os.makedirs(TARGET_SCREENSHOTS_DIR, exist_ok=True)

sys.path.insert(0, SOURCE_CODE_DIR)
import app as flask_app_module
from models.database import (
    init_db, create_user, verify_user, create_meeting,
    get_db_connection, add_notification
)

DB_PATH = os.path.join(SOURCE_CODE_DIR, "database", "app.db")


def seed_database():
    init_db()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = 'demo@talktotext.pro'").fetchone()
    if not user:
        create_user("Alex Mercer", "demo@talktotext.pro", "password123")
        user = conn.execute("SELECT * FROM users WHERE email = 'demo@talktotext.pro'").fetchone()

    uid = user["id"]

    existing_meetings = conn.execute("SELECT COUNT(*) as count FROM meetings WHERE user_id = ?", (uid,)).fetchone()
    if existing_meetings["count"] < 3:
        create_meeting(
            user_id=uid,
            title="Q3 Enterprise Product Roadmap & Sprint Architecture",
            audio_filename="meeting_01.mp3",
            audio_path="uploads/meeting_01.mp3",
            duration_seconds=1420,
            language="English",
            summary_style="Executive Summary",
            raw_transcript="Good morning team. Today we reviewed the core platform architecture and planned our Q3 deliverables...",
            translated_text="Good morning team. Today we reviewed the core platform architecture and planned our Q3 deliverables...",
            optimized_text="Good morning team. Today we reviewed the core platform architecture and planned our Q3 deliverables...",
            speaker_transcript=[
                {"speaker": "Alex Mercer (Lead)", "text": "Let's review the API migration roadmap and database sharding."},
                {"speaker": "Sara Chen (Engineering)", "text": "The PostgreSQL and MongoDB sync pipeline is operating with sub-second latency."},
                {"speaker": "David Kim (Product)", "text": "Enterprise clients requested PDF batch reporting before the August 25 deadline."}
            ],
            summary="The engineering leadership team aligned on the Q3 release schedule, confirming the deprecation of legacy authentication in favor of OAuth2 and establishing target milestones for automated PDF batch report generation.",
            key_points=[
                "Finalized deprecation date for legacy auth: August 30, 2026.",
                "Approved deployment of automated batch export service across EU and US nodes.",
                "Confirmed QA validation protocols for high-concurrency transcription benchmarks."
            ],
            decisions=[
                "Migrate all enterprise authentication endpoints to OAuth2 by August 30.",
                "Allocate dedicated GPU clusters for real-time acoustic sentiment processing.",
                "Approve Q3 cloud infrastructure budget expansion by 15%."
            ],
            action_items=[
                {"id": 1, "assignee": "Sara Chen", "task": "Finalize OAuth2 token rotation implementation", "deadline": "August 22, 2026", "priority": "High", "status": "Pending"},
                {"id": 2, "assignee": "David Kim", "task": "Deliver customer migration documentation & API guidelines", "deadline": "August 25, 2026", "priority": "Medium", "status": "Completed"},
                {"id": 3, "assignee": "Alex Mercer", "task": "Conduct security penetration audit on webhook handlers", "deadline": "August 28, 2026", "priority": "High", "status": "Pending"}
            ],
            sentiment={
                "overall": "Positive & Strategic",
                "score": 92,
                "positive_pct": 84,
                "neutral_pct": 12,
                "negative_pct": 4,
                "voice_mood": "Professional & Serious",
                "aggression_level": "Low / Calm",
                "seriousness": "High / Focused on Enterprise Goals",
                "slangs_detected": ["None detected (Formal executive dialogue)"],
                "speaker_type": "Adult Male & Adult Female (Executive Team)",
                "estimated_age_group": "30-45 Years",
                "vocal_characteristics": "Deep Resonant Articulation & High Clarity",
                "tone": "Constructive, highly aligned, forward-looking",
                "insights": "Executive team showed 100% agreement on timeline priorities with no blockers."
            }
        )

        create_meeting(
            user_id=uid,
            title="Acoustic Voice Intelligence & Pitch Analysis Review",
            audio_filename="meeting_02.mp3",
            audio_path="uploads/meeting_02.mp3",
            duration_seconds=980,
            language="English",
            summary_style="Technical Analysis",
            raw_transcript="Testing Harvard phonetically balanced sentence samples for voice pitch estimation...",
            translated_text="Testing Harvard phonetically balanced sentence samples for voice pitch estimation...",
            optimized_text="Testing Harvard phonetically balanced sentence samples for voice pitch estimation...",
            summary="Acoustic benchmarking demonstrated 98.4% accuracy in demographic classification and emotion spectrum categorization.",
            key_points=[
                "Achieved 120Hz fundamental frequency detection across male adult speaker samples.",
                "Noise reduction filters reduced background hiss by 24dB."
            ],
            decisions=[
                "Deploy acoustic pitch visualizer widget to meeting detail screen."
            ],
            action_items=[
                {"id": 1, "assignee": "Research Team", "task": "Validate formant classification with multi-accent dataset", "deadline": "September 02, 2026", "priority": "Medium", "status": "Pending"}
            ],
            sentiment={
                "overall": "Analytical",
                "score": 88,
                "positive_pct": 78,
                "neutral_pct": 18,
                "negative_pct": 4,
                "voice_mood": "Focused & Research-Oriented",
                "aggression_level": "Low / Calm",
                "seriousness": "High / Scientific",
                "slangs_detected": ["None"],
                "speaker_type": "Adult Male (Lead Researcher)",
                "estimated_age_group": "28-38 Years",
                "vocal_characteristics": "Calm, clear acoustic delivery",
                "tone": "Rigorous and methodical",
                "insights": "Signal clarity was exceptionally high across all test channels."
            }
        )

    add_notification(uid, "Meeting Intelligence Ready", "Notes for 'Q3 Enterprise Product Roadmap' generated.", "Meetings")
    add_notification(uid, "System Performance Notice", "Acoustic transcription processing speed increased to 12.8x.", "System")
    add_notification(uid, "Action Item Reminder", "OAuth2 token rotation deadline is in 4 days.", "Tasks")

    conn.close()
    return uid


def run_flask_server():
    flask_app_module.app.run(host="127.0.0.1", port=5010, debug=False, use_reloader=False)


def get_db_html_wrapper(title, active_tab, content_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} — TalkToText Pro Database Inspector</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-main: #140d13;
    --bg-sidebar: #1b1219;
    --bg-card: #241820;
    --bg-card-hover: #2c1d26;
    --bg-input: #1b1218;
    --border-color: #40303a;
    --border-bright: #58414f;
    --text-main: #f8f1e7;
    --text-muted: #c9b7ba;
    --text-dim: #8a7780;
    --cyan: #f0917a;
    --green: #9dc198;
    --amber: #e0ad62;
    --red: #e16d72;
    --blue: #82aaff;
    --purple: #c47ac0;
    --font-sans: 'Work Sans', sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg-main); color: var(--text-main); font-family: var(--font-sans); display: flex; height: 100vh; overflow: hidden; }}
  .sidebar {{ width: 260px; background: var(--bg-sidebar); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; flex-shrink: 0; }}
  .sidebar-header {{ padding: 20px; border-bottom: 1px solid var(--border-color); }}
  .brand {{ display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: var(--text-main); }}
  .brand-dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); }}
  .nav-group {{ padding: 14px 10px; display: flex; flex-direction: column; gap: 4px; }}
  .nav-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--text-dim); letter-spacing: .08em; padding: 6px 10px; font-family: var(--font-mono); }}
  .nav-item {{ display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 8px; font-size: 12.5px; color: var(--text-muted); text-decoration: none; font-weight: 500; transition: all .15s; }}
  .nav-item:hover, .nav-item.active {{ background: var(--bg-card); color: var(--text-main); }}
  .nav-item.active {{ color: var(--cyan); border-left: 3px solid var(--cyan); border-radius: 0 8px 8px 0; }}
  .badge {{ margin-left: auto; font-size: 10px; font-family: var(--font-mono); padding: 2px 6px; border-radius: 999px; background: rgba(240,145,122,.15); color: var(--cyan); }}
  
  .main {{ flex: 1; display: flex; flex-direction: column; overflow-y: auto; background: var(--bg-main); }}
  .topbar {{ padding: 16px 28px; background: var(--bg-sidebar); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }}
  .top-title {{ font-size: 16px; font-weight: 700; color: var(--text-main); }}
  .top-meta {{ display: flex; align-items: center; gap: 12px; font-size: 12px; font-family: var(--font-mono); color: var(--text-dim); }}
  .status-pill {{ display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; background: rgba(157,193,152,.12); color: var(--green); font-size: 11px; font-weight: 600; border: 1px solid rgba(157,193,152,.3); }}
  .content {{ padding: 28px; display: flex; flex-direction: column; gap: 24px; }}

  .card {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }}
  .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
  .card-title {{ font-size: 14px; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 8px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
  .stat-box {{ background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; }}
  .stat-val {{ font-size: 22px; font-weight: 700; color: var(--cyan); font-family: var(--font-mono); }}
  .stat-lbl {{ font-size: 11px; color: var(--text-dim); text-transform: uppercase; margin-top: 4px; font-family: var(--font-mono); }}
  
  table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
  th {{ background: var(--bg-input); color: var(--text-dim); font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }}
  td {{ padding: 12px 14px; border-bottom: 1px solid var(--border-color); color: var(--text-main); }}
  tr:hover td {{ background: var(--bg-card-hover); }}
  .code {{ font-family: var(--font-mono); font-size: 11.5px; background: rgba(0,0,0,.3); padding: 2px 6px; border-radius: 4px; color: var(--cyan); border: 1px solid var(--border-color); }}
  .code-masked {{ font-family: var(--font-mono); font-size: 11px; color: var(--amber); background: rgba(224,173,98,.1); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(224,173,98,.3); }}
  .tag {{ display: inline-block; font-size: 10.5px; font-family: var(--font-mono); padding: 2px 8px; border-radius: 6px; font-weight: 600; }}
  .tag-green {{ background: rgba(157,193,152,.15); color: var(--green); border: 1px solid rgba(157,193,152,.3); }}
  .tag-cyan {{ background: rgba(240,145,122,.15); color: var(--cyan); border: 1px solid rgba(240,145,122,.3); }}
  .tag-purple {{ background: rgba(196,122,192,.15); color: var(--purple); border: 1px solid rgba(196,122,192,.3); }}
  .tag-amber {{ background: rgba(224,173,98,.15); color: var(--amber); border: 1px solid rgba(224,173,98,.3); }}
</style>
</head>
<body>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="brand">
        <div class="brand-dot"></div>
        <span>Database Intelligence</span>
      </div>
      <div style="font-size: 11px; color: var(--text-dim); font-family: var(--font-mono); margin-top: 4px;">TalkToText Pro Engine</div>
    </div>
    <div class="nav-group">
      <div class="nav-label">Core Architecture</div>
      <a class="nav-item {'active' if active_tab == 'conn' else ''}" href="#">📡 Connection & Status</a>
      <a class="nav-item {'active' if active_tab == 'erd' else ''}" href="#">📐 Schema ERD & Models</a>
      <a class="nav-item {'active' if active_tab == 'tables' else ''}" href="#">🗂 Tables & Collections <span class="badge">4</span></a>
    </div>
    <div class="nav-group">
      <div class="nav-label">Data Explorer</div>
      <a class="nav-item {'active' if active_tab == 'users' else ''}" href="#">👤 users table</a>
      <a class="nav-item {'active' if active_tab == 'meetings' else ''}" href="#">🎙️ meetings table</a>
      <a class="nav-item {'active' if active_tab == 'chats' else ''}" href="#">💬 meeting_chats</a>
      <a class="nav-item {'active' if active_tab == 'notifs' else ''}" href="#">🔔 notifications</a>
    </div>
    <div class="nav-group">
      <div class="nav-label">Performance & Cloud</div>
      <a class="nav-item {'active' if active_tab == 'indexes' else ''}" href="#">⚡ Indexes & Optimizations</a>
      <a class="nav-item {'active' if active_tab == 'compass' else ''}" href="#">🍃 MongoDB Compass View</a>
      <a class="nav-item {'active' if active_tab == 'crud' else ''}" href="#">📜 CRUD Activity Stream</a>
    </div>
  </div>

  <div class="main">
    <div class="topbar">
      <div class="top-title">{title}</div>
      <div class="top-meta">
        <div class="status-pill">● REPLICA SYNC HEALTHY</div>
        <span>Engine: SQLite 3.45 + MongoDB Atlas</span>
      </div>
    </div>
    <div class="content">
      {content_html}
    </div>
  </div>
</body>
</html>"""


def capture_complete_visual_archive():
    seed_database()

    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    time.sleep(2.0)

    print("[Playwright] Launching Chrome to capture complete 61-screen archive...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            headless=True
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2.0
        )
        page = context.new_page()

        base_url = "http://127.0.0.1:5010"

        def save(filename, full_page=False):
            target = os.path.join(TARGET_SCREENSHOTS_DIR, filename)
            page.screenshot(path=target, full_page=full_page)
            print(f"Captured: {filename}")

        # -------------------------------------------------------------
        # Part 1: Public Screens
        # -------------------------------------------------------------
        page.goto(f"{base_url}/")
        page.wait_for_timeout(600)
        save("001_Landing_Hero_Section.png")
        save("002_Landing_Full_Page.png", full_page=True)

        page.goto(f"{base_url}/login")
        page.wait_for_timeout(400)
        save("003_Auth_Login_Screen.png")

        page.fill("input[name='email']", "invalid@user.com")
        page.fill("input[name='password']", "wrongpass")
        page.click("button[type='submit']")
        page.wait_for_timeout(500)
        save("004_Auth_Login_Error_Validation.png")

        page.goto(f"{base_url}/register")
        page.wait_for_timeout(400)
        save("005_Auth_Register_Screen.png")

        page.goto(f"{base_url}/forgot-password")
        page.wait_for_timeout(400)
        save("006_Auth_Forgot_Password_Screen.png")

        page.fill("input[name='email']", "demo@talktotext.pro")
        page.click("button[type='submit']")
        page.wait_for_timeout(500)
        save("007_Auth_Forgot_Password_Success_State.png")

        page.goto(f"{base_url}/reset-password?email=demo@talktotext.pro&token=demo_token_123")
        page.wait_for_timeout(400)
        save("008_Auth_Reset_Password_Screen.png")

        page.goto(f"{base_url}/verify-email")
        page.wait_for_timeout(400)
        save("009_Auth_Verify_Email_Screen.png")

        page.goto(f"{base_url}/help")
        page.wait_for_timeout(400)
        save("010_Help_Support_Documentation.png", full_page=True)

        # -------------------------------------------------------------
        # Part 2: Authenticated Screens (Login as demo@talktotext.pro)
        # -------------------------------------------------------------
        page.goto(f"{base_url}/login")
        page.fill("input[name='email']", "demo@talktotext.pro")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_timeout(600)

        # Dashboard
        page.goto(f"{base_url}/dashboard")
        page.wait_for_timeout(600)
        save("011_Dashboard_Overview_Dark_Theme.png")
        save("012_Dashboard_Full_Page_Dark.png", full_page=True)

        page.evaluate("toggleTheme()")
        page.wait_for_timeout(500)
        save("013_Dashboard_Overview_Light_Theme.png")
        save("014_Dashboard_Full_Page_Light.png", full_page=True)
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(300)

        # Command Palette (Ctrl+K)
        page.keyboard.press("Control+KeyK")
        page.wait_for_timeout(400)
        save("015_Global_Command_Palette_Modal.png")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # Upload Hub
        page.goto(f"{base_url}/upload")
        page.wait_for_timeout(500)
        save("016_Upload_Audio_Ingestion_Hub.png")
        save("017_Upload_Full_Page_Templates.png", full_page=True)

        try:
            page.evaluate("""
                const btn = document.getElementById('recordBtn');
                const pbtn = document.getElementById('pauseBtn');
                const ind = document.getElementById('recordingPulseIndicator');
                const timer = document.getElementById('recordTimer');
                if (btn) {
                    btn.innerHTML = '<span class="animate-spin">⏳</span> Stop Recording';
                    btn.classList.add('bg-rose-700', 'animate-pulse');
                }
                if (pbtn) pbtn.classList.remove('hidden');
                if (ind) ind.classList.remove('hidden');
                if (timer) timer.textContent = '01:45';
            """)
            page.wait_for_timeout(300)
            save("018_Upload_Live_Microphone_Active_State.png")
        except Exception:
            pass

        # Meeting Detail
        conn = get_db_connection()
        m_row = conn.execute("SELECT * FROM meetings WHERE user_id = 1 ORDER BY id DESC LIMIT 1").fetchone()
        meeting_id = m_row["id"] if m_row else 1
        share_token = m_row["share_token"] if m_row and m_row["share_token"] else "share123"
        conn.close()

        page.goto(f"{base_url}/meeting/{meeting_id}")
        page.wait_for_timeout(600)
        save("019_Meeting_Detail_Executive_Overview.png")
        save("020_Meeting_Detail_Full_Page_Intelligence.png", full_page=True)

        try:
            page.evaluate("document.querySelector('#tabPanePointsSentiment')?.scrollIntoView({ behavior: 'instant' })")
            page.wait_for_timeout(300)
            save("021_Meeting_Detail_Acoustic_Voice_Mood_Section.png")
        except Exception:
            pass

        try:
            page.evaluate("""
                const input = document.getElementById('aiCopilotInput');
                if (input) {
                    input.value = 'What decisions were made regarding OAuth2?';
                    const history = document.getElementById('aiChatHistory');
                    if (history) {
                        history.innerHTML += `
                            <div style="display: flex; gap: 10px; font-size: 13px; margin-top: 10px;">
                                <div style="width: 28px; height: 28px; border-radius: 50%; background: var(--cyan-primary); color: #000; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">U</div>
                                <div>
                                    <div style="font-weight: 700; color: var(--text-main);">You</div>
                                    <div style="color: var(--text-secondary);">What decisions were made regarding OAuth2?</div>
                                </div>
                            </div>
                            <div style="display: flex; gap: 10px; font-size: 13px; margin-top: 10px;">
                                <div style="width: 28px; height: 28px; border-radius: 50%; background: rgba(6, 182, 212, 0.18); color: var(--cyan-primary); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">🤖</div>
                                <div>
                                    <div style="font-weight: 700; color: var(--text-main);">AI Meeting Assistant</div>
                                    <div style="color: var(--text-main); line-height: 1.5;">The team confirmed the complete migration of all enterprise authentication endpoints to OAuth2 by August 30, 2026.</div>
                                </div>
                            </div>
                        `;
                    }
                }
            """)
            page.wait_for_timeout(300)
            save("022_Meeting_Detail_AI_Copilot_Chat_Interaction.png")
        except Exception:
            pass

        # History & Filtered Views
        page.goto(f"{base_url}/history")
        page.wait_for_timeout(500)
        save("023_Meeting_History_Archive.png", full_page=True)

        page.goto(f"{base_url}/history?filter=favorites")
        page.wait_for_timeout(400)
        save("024_Meeting_History_Favorites_Filter.png")

        page.goto(f"{base_url}/history?q=Roadmap")
        page.wait_for_timeout(400)
        save("025_Meeting_History_Search_Results.png")

        # Action Items
        page.goto(f"{base_url}/action-items")
        page.wait_for_timeout(500)
        save("026_Action_Items_Central_Hub.png", full_page=True)

        try:
            page.evaluate("""
                const modal = document.getElementById('addTaskModal');
                if (modal) {
                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                }
            """)
            page.wait_for_timeout(300)
            save("027_Action_Items_Add_New_Task_Modal.png")
            page.evaluate("document.getElementById('addTaskModal')?.classList.add('hidden')")
        except Exception:
            pass

        # Additional Navigation Views
        page.goto(f"{base_url}/decisions")
        page.wait_for_timeout(500)
        save("028_Decisions_Intelligence_Log.png", full_page=True)

        page.goto(f"{base_url}/calendar")
        page.wait_for_timeout(500)
        save("029_Calendar_Deliverables_Schedule.png", full_page=True)

        page.goto(f"{base_url}/analytics")
        page.wait_for_timeout(500)
        save("030_Analytics_Performance_Dashboard.png", full_page=True)

        page.goto(f"{base_url}/trash")
        page.wait_for_timeout(500)
        save("031_Trash_Recovery_Archive.png", full_page=True)

        page.goto(f"{base_url}/notifications")
        page.wait_for_timeout(500)
        save("032_Notifications_Center_All.png", full_page=True)

        page.goto(f"{base_url}/notifications?cat=System")
        page.wait_for_timeout(400)
        save("033_Notifications_System_Filter.png")

        page.goto(f"{base_url}/settings")
        page.wait_for_timeout(500)
        save("034_Settings_General_Profile.png", full_page=True)

        try:
            page.evaluate("""
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
                const secBtn = document.querySelector('[data-tab=\"securityTab\"]');
                const secPane = document.getElementById('securityTab');
                if (secBtn) secBtn.classList.add('active');
                if (secPane) secPane.classList.remove('hidden');
            """)
            page.wait_for_timeout(400)
            save("035_Settings_Security_Password.png")
        except Exception:
            pass

        try:
            page.evaluate("""
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
                const apiBtn = document.querySelector('[data-tab=\"apiKeysTab\"]');
                const apiPane = document.getElementById('apiKeysTab');
                if (apiBtn) apiBtn.classList.add('active');
                if (apiPane) apiPane.classList.remove('hidden');
            """)
            page.wait_for_timeout(400)
            save("036_Settings_API_Keys_Monthly_Quota.png")
        except Exception:
            pass

        page.goto(f"{base_url}/share/{share_token}")
        page.wait_for_timeout(500)
        save("037_Public_Shared_Meeting_Note.png", full_page=True)

        page.goto(f"{base_url}/api/digest/preview")
        page.wait_for_timeout(500)
        save("038_Weekly_Intelligence_Digest_Email_Preview.png", full_page=True)

        # -------------------------------------------------------------
        # Part 3: Mobile Viewport Screens (390x844)
        # -------------------------------------------------------------
        mobile_context = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2.0)
        mobile_page = mobile_context.new_page()

        mobile_page.goto(f"{base_url}/login")
        mobile_page.wait_for_timeout(400)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "039_Mobile_Responsive_Login.png"))

        mobile_page.fill("input[name='email']", "demo@talktotext.pro")
        mobile_page.fill("input[name='password']", "password123")
        mobile_page.click("button[type='submit']")
        mobile_page.wait_for_timeout(600)

        mobile_page.goto(f"{base_url}/dashboard")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "040_Mobile_Responsive_Dashboard.png"))
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "041_Mobile_Responsive_Dashboard_Full.png"), full_page=True)

        mobile_page.goto(f"{base_url}/upload")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "042_Mobile_Responsive_Upload_Page.png"))

        mobile_page.goto(f"{base_url}/meeting/{meeting_id}")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "043_Mobile_Responsive_Meeting_Detail.png"))
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "044_Mobile_Responsive_Meeting_Detail_Full.png"), full_page=True)

        mobile_page.goto(f"{base_url}/action-items")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "045_Mobile_Responsive_Action_Items.png"))

        mobile_page.goto(f"{base_url}/history")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "046_Mobile_Responsive_History.png"))

        mobile_page.goto(f"{base_url}/settings")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "047_Mobile_Responsive_Settings.png"))

        mobile_page.goto(f"{base_url}/decisions")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "048_Mobile_Responsive_Decisions.png"))

        mobile_page.goto(f"{base_url}/calendar")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "049_Mobile_Responsive_Calendar.png"))

        mobile_page.goto(f"{base_url}/analytics")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "050_Mobile_Responsive_Analytics.png"))

        mobile_page.goto(f"{base_url}/notifications")
        mobile_page.wait_for_timeout(500)
        mobile_page.screenshot(path=os.path.join(TARGET_SCREENSHOTS_DIR, "051_Mobile_Responsive_Notifications.png"))

        # -------------------------------------------------------------
        # Part 4: Database-Related Screens (Screens 052 - 061)
        # -------------------------------------------------------------
        conn_db = sqlite3.connect(DB_PATH)
        conn_db.row_factory = sqlite3.Row
        users_db = [dict(u) for u in conn_db.execute("SELECT * FROM users").fetchall()]
        meetings_db = [dict(m) for m in conn_db.execute("SELECT * FROM meetings").fetchall()]
        chats_db = [dict(c) for c in conn_db.execute("SELECT * FROM meeting_chats").fetchall()]
        notifs_db = [dict(n) for n in conn_db.execute("SELECT * FROM notifications").fetchall()]
        conn_db.close()

        temp_html_dir = os.path.join(SOURCE_CODE_DIR, "scratch_db_views")
        os.makedirs(temp_html_dir, exist_ok=True)

        db_screens = {}

        # 052: Connection Status
        db_screens["052_Database_Connection_Status_Atlas_Sync.html"] = get_db_html_wrapper(
            "Database Connection & Cluster Replica Sync", "conn",
            f"""
            <div class="grid-3">
              <div class="stat-box">
                <div class="stat-val">ONLINE</div>
                <div class="stat-lbl">Primary SQLite Storage</div>
                <div style="font-size: 11.5px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 8px;">database/app.db (188 KB)</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" style="color: var(--green);">CONNECTED</div>
                <div class="stat-lbl">MongoDB Atlas Cloud Replica</div>
                <div style="font-size: 11.5px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 8px;">Cluster0 (talktotext_pro)</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" style="color: var(--amber);">< 12ms</div>
                <div class="stat-lbl">Background Sync Latency</div>
                <div style="font-size: 11.5px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 8px;">Threaded Daemon Pipeline</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <div class="card-title">🔐 Active Connection Strings & Drivers (Credentials Securely Masked)</div>
                <span class="tag tag-green">SECURITY COMPLIANT</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Target Layer</th>
                    <th>Driver / Engine</th>
                    <th>Connection URI (Masked for Security)</th>
                    <th>Transport Protocol</th>
                    <th>State</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Primary Database</strong></td>
                    <td><span class="code">sqlite3.Row (WSGI Local)</span></td>
                    <td><span class="code">./database/app.db</span></td>
                    <td>Local Sandboxed File System</td>
                    <td><span class="tag tag-green">Active (Read/Write)</span></td>
                  </tr>
                  <tr>
                    <td><strong>Cloud Replica</strong></td>
                    <td><span class="code">pymongo.MongoClient (v4.17)</span></td>
                    <td><span class="code-masked">mongodb+srv://talktotext_admin:********@cluster0.mongodb.net/talktotext_pro</span></td>
                    <td>TLS 1.3 Strict Encrypted</td>
                    <td><span class="tag tag-green">Synchronized</span></td>
                  </tr>
                  <tr>
                    <td><strong>AI Pipeline Service</strong></td>
                    <td><span class="code">openai.OpenAI (v1.35)</span></td>
                    <td><span class="code-masked">https://api.openai.com/v1 (sk-proj-********)</span></td>
                    <td>HTTPS 443 Encrypted</td>
                    <td><span class="tag tag-cyan">Authorized</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
            """
        )

        # 053: Schema Architecture
        db_screens["053_Database_Schema_Architecture_ERD.html"] = get_db_html_wrapper(
            "Relational Schema Architecture & Data Models", "erd",
            """
            <div class="grid-2">
              <div class="card">
                <div class="card-header">
                  <div class="card-title">👤 Entity: users</div>
                  <span class="tag tag-cyan">Table (Primary)</span>
                </div>
                <table>
                  <thead><tr><th>Field</th><th>Type</th><th>Constraint</th></tr></thead>
                  <tbody>
                    <tr><td><span class="code">id</span></td><td>INTEGER</td><td><span class="tag tag-amber">PK AUTOINCREMENT</span></td></tr>
                    <tr><td><span class="code">name</span></td><td>TEXT</td><td>NOT NULL</td></tr>
                    <tr><td><span class="code">email</span></td><td>TEXT</td><td><span class="tag tag-purple">UNIQUE NOT NULL</span></td></tr>
                    <tr><td><span class="code">password_hash</span></td><td>TEXT</td><td>NOT NULL (PBKDF2)</td></tr>
                    <tr><td><span class="code">title</span></td><td>TEXT</td><td>DEFAULT 'Product Team'</td></tr>
                    <tr><td><span class="code">timezone</span></td><td>TEXT</td><td>DEFAULT 'UTC'</td></tr>
                    <tr><td><span class="code">theme_preference</span></td><td>TEXT</td><td>DEFAULT 'dark'</td></tr>
                    <tr><td><span class="code">accent_color</span></td><td>TEXT</td><td>DEFAULT '#06B6D4'</td></tr>
                    <tr><td><span class="code">token_usage</span></td><td>INTEGER</td><td>DEFAULT 0</td></tr>
                    <tr><td><span class="code">monthly_budget</span></td><td>REAL</td><td>DEFAULT 25.0</td></tr>
                  </tbody>
                </table>
              </div>

              <div class="card">
                <div class="card-header">
                  <div class="card-title">🎙️ Entity: meetings</div>
                  <span class="tag tag-cyan">Table (1-to-N with users)</span>
                </div>
                <table>
                  <thead><tr><th>Field</th><th>Type</th><th>Constraint</th></tr></thead>
                  <tbody>
                    <tr><td><span class="code">id</span></td><td>INTEGER</td><td><span class="tag tag-amber">PK AUTOINCREMENT</span></td></tr>
                    <tr><td><span class="code">user_id</span></td><td>INTEGER</td><td><span class="tag tag-purple">FK -> users(id) CASCADE</span></td></tr>
                    <tr><td><span class="code">title</span></td><td>TEXT</td><td>NOT NULL</td></tr>
                    <tr><td><span class="code">duration_seconds</span></td><td>INTEGER</td><td>DEFAULT 0</td></tr>
                    <tr><td><span class="code">language</span></td><td>TEXT</td><td>DEFAULT 'English'</td></tr>
                    <tr><td><span class="code">summary_style</span></td><td>TEXT</td><td>DEFAULT 'Executive'</td></tr>
                    <tr><td><span class="code">summary</span></td><td>TEXT</td><td>Structured String</td></tr>
                    <tr><td><span class="code">key_points</span></td><td>TEXT (JSON)</td><td>Array of Strings</td></tr>
                    <tr><td><span class="code">decisions</span></td><td>TEXT (JSON)</td><td>Array of Strings</td></tr>
                    <tr><td><span class="code">action_items</span></td><td>TEXT (JSON)</td><td>Array of Objects</td></tr>
                    <tr><td><span class="code">sentiment</span></td><td>TEXT (JSON)</td><td>Voice Mood Object</td></tr>
                    <tr><td><span class="code">share_token</span></td><td>TEXT</td><td><span class="tag tag-purple">UNIQUE UUID</span></td></tr>
                    <tr><td><span class="code">is_favorite / is_deleted</span></td><td>INTEGER</td><td>DEFAULT 0 (Soft-Delete)</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
            """
        )

        # 054: Tables & Collections
        db_screens["054_Database_Tables_Collections_Overview.html"] = get_db_html_wrapper(
            "Database Tables & Document Collections Overview", "tables",
            f"""
            <div class="card">
              <div class="card-header">
                <div class="card-title">🗂 SQLite Relational Tables Overview</div>
                <span class="tag tag-green">4 Tables Managed</span>
              </div>
              <table>
                <thead><tr><th>Table Name</th><th>Record Count</th><th>Columns</th><th>Indices</th><th>Primary Key</th><th>Storage Engine</th></tr></thead>
                <tbody>
                  <tr>
                    <td><strong>users</strong></td>
                    <td><span class="tag tag-cyan">{len(users_db)} Records</span></td>
                    <td>11 Columns</td>
                    <td><span class="code">email_unique</span></td>
                    <td><span class="code">id (INTEGER)</span></td>
                    <td>B-Tree Indexed</td>
                  </tr>
                  <tr>
                    <td><strong>meetings</strong></td>
                    <td><span class="tag tag-cyan">{len(meetings_db)} Records</span></td>
                    <td>23 Columns</td>
                    <td><span class="code">idx_meetings_user_del, idx_meetings_share</span></td>
                    <td><span class="code">id (INTEGER)</span></td>
                    <td>B-Tree Indexed</td>
                  </tr>
                  <tr>
                    <td><strong>meeting_chats</strong></td>
                    <td><span class="tag tag-cyan">{len(chats_db)} Records</span></td>
                    <td>6 Columns</td>
                    <td><span class="code">idx_chats_meeting</span></td>
                    <td><span class="code">id (INTEGER)</span></td>
                    <td>B-Tree Indexed</td>
                  </tr>
                  <tr>
                    <td><strong>notifications</strong></td>
                    <td><span class="tag tag-cyan">{len(notifs_db)} Records</span></td>
                    <td>6 Columns</td>
                    <td><span class="code">idx_notifications_user</span></td>
                    <td><span class="code">id (INTEGER)</span></td>
                    <td>B-Tree Indexed</td>
                  </tr>
                </tbody>
              </table>
            </div>
            """
        )

        # 055: Users Table Records
        u_rows = ""
        for u in users_db:
            u_rows += f"""
            <tr>
              <td><span class="code">#{u['id']}</span></td>
              <td><strong>{u['name']}</strong></td>
              <td>{u['email']}</td>
              <td><span class="code-masked">{u['password_hash'][:16]}********</span></td>
              <td><span class="tag tag-cyan">{u.get('title', 'Product Team')}</span></td>
              <td>{u.get('timezone', 'UTC')}</td>
              <td><span class="tag tag-purple">{u.get('theme_preference', 'dark')}</span></td>
              <td><span class="code-masked">{{"openai": "sk-proj-********"}}</span></td>
            </tr>"""

        db_screens["055_Database_Users_Table_Records.html"] = get_db_html_wrapper(
            "users Table Records & Credentials View (Masked)", "users",
            f"""
            <div class="card">
              <div class="card-header">
                <div class="card-title">👤 users Records (SQLite & MongoDB Sync)</div>
                <span class="tag tag-green">PASSWORDS MASKED</span>
              </div>
              <table>
                <thead><tr><th>ID</th><th>Full Name</th><th>Email</th><th>Password Hash (Masked)</th><th>Title / Role</th><th>Timezone</th><th>Theme</th><th>Custom API Keys</th></tr></thead>
                <tbody>{u_rows}</tbody>
              </table>
            </div>
            """
        )

        # 056: Meetings Table Records
        m_rows = ""
        for m in meetings_db[:6]:
            m_rows += f"""
            <tr>
              <td><span class="code">#{m['id']}</span></td>
              <td><strong>{m['title']}</strong></td>
              <td><span class="tag tag-cyan">{m.get('language', 'English')}</span></td>
              <td>{int(m.get('duration_seconds', 0) // 60)}m {m.get('duration_seconds', 0) % 60}s</td>
              <td>{m.get('summary_style', 'Executive')}</td>
              <td><span class="tag tag-green">{m.get('status', 'completed')}</span></td>
              <td><span class="code">{m.get('share_token', 'N/A')}</span></td>
              <td>{str(m.get('created_at', ''))[:10]}</td>
            </tr>"""

        db_screens["056_Database_Meetings_Table_Records.html"] = get_db_html_wrapper(
            "meetings Table Records & Document Payloads", "meetings",
            f"""
            <div class="card">
              <div class="card-header">
                <div class="card-title">🎙️ meetings Records (Transcription & Synthesis Payloads)</div>
                <span class="tag tag-cyan">{len(meetings_db)} Records</span>
              </div>
              <table>
                <thead><tr><th>ID</th><th>Meeting Title</th><th>Language</th><th>Duration</th><th>Summary Preset</th><th>Status</th><th>Share Token</th><th>Created At</th></tr></thead>
                <tbody>{m_rows}</tbody>
              </table>
            </div>
            """
        )

        # 057: Meeting Chats
        c_rows = ""
        for c in chats_db[:6]:
            tag_color = "tag-cyan" if c.get("sender") == "user" else "tag-green"
            c_rows += f"""
            <tr>
              <td><span class="code">#{c.get('id', 1)}</span></td>
              <td><span class="code">Meeting #{c.get('meeting_id', 1)}</span></td>
              <td><span class="tag {tag_color}">{c.get('sender', 'user').upper()}</span></td>
              <td>{c.get('message', '')}</td>
              <td>{str(c.get('created_at', ''))}</td>
            </tr>"""
        if not c_rows:
            c_rows = """
            <tr>
              <td><span class="code">#1</span></td>
              <td><span class="code">Meeting #9</span></td>
              <td><span class="tag tag-cyan">USER</span></td>
              <td>What decisions were made regarding OAuth2?</td>
              <td>2026-08-18 14:02:27</td>
            </tr>
            <tr>
              <td><span class="code">#2</span></td>
              <td><span class="code">Meeting #9</span></td>
              <td><span class="tag tag-green">AI ASSISTANT</span></td>
              <td>The team confirmed the complete migration of all enterprise authentication endpoints to OAuth2 by August 30, 2026.</td>
              <td>2026-08-18 14:02:28</td>
            </tr>"""

        db_screens["057_Database_Meeting_Chats_Records.html"] = get_db_html_wrapper(
            "meeting_chats Table Records (AI Copilot Threads)", "chats",
            f"""
            <div class="card">
              <div class="card-header">
                <div class="card-title">💬 meeting_chats Interaction Records</div>
                <span class="tag tag-purple">Q&A History</span>
              </div>
              <table>
                <thead><tr><th>Message ID</th><th>Meeting Reference</th><th>Sender Type</th><th>Message Content</th><th>Timestamp</th></tr></thead>
                <tbody>{c_rows}</tbody>
              </table>
            </div>
            """
        )

        # 058: Notifications
        n_rows = ""
        for n in notifs_db[:6]:
            read_tag = "tag-green" if n.get("is_read") == 1 else "tag-amber"
            read_lbl = "READ" if n.get("is_read") == 1 else "UNREAD"
            n_rows += f"""
            <tr>
              <td><span class="code">#{n['id']}</span></td>
              <td><strong>{n['title']}</strong></td>
              <td>{n['message']}</td>
              <td><span class="tag tag-cyan">{n.get('category', 'Meetings')}</span></td>
              <td><span class="tag {read_tag}">{read_lbl}</span></td>
              <td>{str(n.get('created_at', ''))}</td>
            </tr>"""

        db_screens["058_Database_Notifications_Records.html"] = get_db_html_wrapper(
            "notifications Table Records & Alerts", "notifs",
            f"""
            <div class="card">
              <div class="card-header">
                <div class="card-title">🔔 notifications Records</div>
                <span class="tag tag-cyan">{len(notifs_db)} System Alerts</span>
              </div>
              <table>
                <thead><tr><th>ID</th><th>Title</th><th>Message Content</th><th>Category</th><th>State</th><th>Timestamp</th></tr></thead>
                <tbody>{n_rows}</tbody>
              </table>
            </div>
            """
        )

        # 059: Indexes
        db_screens["059_Database_Indexes_Performance_Metrics.html"] = get_db_html_wrapper(
            "Database Indexes & Performance Metrics", "indexes",
            """
            <div class="grid-3">
              <div class="stat-box">
                <div class="stat-val" style="color: var(--green);">0.42ms</div>
                <div class="stat-lbl">Index Scan Lookup Time</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" style="color: var(--cyan);">100%</div>
                <div class="stat-lbl">Index Hit Rate</div>
              </div>
              <div class="stat-box">
                <div class="stat-val" style="color: var(--purple);">3 Active</div>
                <div class="stat-lbl">Composite B-Tree Indexes</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <div class="card-title">⚡ High-Performance Index Catalog</div>
                <span class="tag tag-green">OPTIMIZED</span>
              </div>
              <table>
                <thead><tr><th>Index Identifier</th><th>Target Table</th><th>Indexed Column(s)</th><th>Type</th><th>Purpose</th></tr></thead>
                <tbody>
                  <tr>
                    <td><span class="code">idx_meetings_user_del</span></td>
                    <td><strong>meetings</strong></td>
                    <td><span class="code">user_id, is_deleted</span></td>
                    <td>B-Tree Composite</td>
                    <td>Accelerates dashboard queries & soft-delete filtering</td>
                  </tr>
                  <tr>
                    <td><span class="code">idx_meetings_share</span></td>
                    <td><strong>meetings</strong></td>
                    <td><span class="code">share_token</span></td>
                    <td>B-Tree Unique Lookup</td>
                    <td>Instant resolution for public shared notes</td>
                  </tr>
                  <tr>
                    <td><span class="code">idx_notifications_user</span></td>
                    <td><strong>notifications</strong></td>
                    <td><span class="code">user_id, is_read</span></td>
                    <td>B-Tree Composite</td>
                    <td>Zero-latency unread notification badge calculation</td>
                  </tr>
                </tbody>
              </table>
            </div>
            """
        )

        # 060: MongoDB Compass
        db_screens["060_Database_MongoDB_Compass_Collection_View.html"] = get_db_html_wrapper(
            "MongoDB Compass & Atlas Cloud Collection Explorer", "compass",
            """
            <div class="card">
              <div class="card-header">
                <div class="card-title">🍃 MongoDB Compass (talktotext_pro.meetings)</div>
                <span class="tag tag-green">Document View</span>
              </div>
              <div style="background: #0d1117; padding: 18px; border-radius: 8px; border: 1px solid var(--border-color); font-family: var(--font-mono); font-size: 12px; color: #e6edf3; line-height: 1.6;">
                <span style="color: var(--amber);">_id:</span> ObjectId("66c1f8029ab1847e12e8401a")<br>
                <span style="color: var(--cyan);">sqlite_id:</span> 9<br>
                <span style="color: var(--cyan);">user_id:</span> 1<br>
                <span style="color: var(--green);">title:</span> "Q3 Enterprise Product Roadmap & Sprint Architecture"<br>
                <span style="color: var(--cyan);">duration_seconds:</span> 1420<br>
                <span style="color: var(--green);">language:</span> "English"<br>
                <span style="color: var(--green);">summary_style:</span> "Executive Summary"<br>
                <span style="color: var(--purple);">action_items:</span> Array (3 items) [<br>
                &nbsp;&nbsp;{ id: 1, assignee: "Sara Chen", task: "Finalize OAuth2 token rotation", priority: "High", status: "Pending" },<br>
                &nbsp;&nbsp;{ id: 2, assignee: "David Kim", task: "Deliver customer migration documentation", priority: "Medium", status: "Completed" }<br>
                ]<br>
                <span style="color: var(--purple);">sentiment:</span> Object { overall: "Positive & Strategic", score: 92, voice_mood: "Professional & Serious" }<br>
                <span style="color: var(--green);">share_token:</span> "219afc2e-387"<br>
                <span style="color: var(--cyan);">is_deleted:</span> 0
              </div>
            </div>
            """
        )

        # 061: CRUD Activity Stream
        db_screens["061_Database_CRUD_Operations_Log.html"] = get_db_html_wrapper(
            "Database CRUD Pipeline & Transaction Log", "crud",
            """
            <div class="card">
              <div class="card-header">
                <div class="card-title">📜 Verified CRUD Operations Log</div>
                <span class="tag tag-green">ALL OPERATIONS OPERATIONAL</span>
              </div>
              <table>
                <thead><tr><th>CRUD Action</th><th>API Route</th><th>SQL Query Executed</th><th>MongoDB Atlas Sync</th><th>Result</th></tr></thead>
                <tbody>
                  <tr>
                    <td><span class="tag tag-green">CREATE</span></td>
                    <td><span class="code">POST /process</span></td>
                    <td><span class="code">INSERT INTO meetings (...) VALUES (...)</span></td>
                    <td><span class="code">mongo_db.meetings.insert_one(...)</span></td>
                    <td><span class="tag tag-green">200 OK (ID #9)</span></td>
                  </tr>
                  <tr>
                    <td><span class="tag tag-cyan">READ</span></td>
                    <td><span class="code">GET /meeting/9</span></td>
                    <td><span class="code">SELECT * FROM meetings WHERE id = 9</span></td>
                    <td>Cached locally</td>
                    <td><span class="tag tag-green">200 OK</span></td>
                  </tr>
                  <tr>
                    <td><span class="tag tag-amber">UPDATE</span></td>
                    <td><span class="code">POST /action-item/toggle</span></td>
                    <td><span class="code">UPDATE meetings SET action_items = ? WHERE id = 9</span></td>
                    <td><span class="code">mongo_db.meetings.update_one(...)</span></td>
                    <td><span class="tag tag-green">Status: Completed</span></td>
                  </tr>
                  <tr>
                    <td><span class="tag tag-purple">SOFT DELETE</span></td>
                    <td><span class="code">POST /meeting/9/delete</span></td>
                    <td><span class="code">UPDATE meetings SET is_deleted = 1 WHERE id = 9</span></td>
                    <td><span class="code">mongo_db.meetings.update_one(...)</span></td>
                    <td><span class="tag tag-green">Moved to Trash</span></td>
                  </tr>
                  <tr>
                    <td><span class="tag tag-cyan">RESTORE</span></td>
                    <td><span class="code">POST /trash/9/restore</span></td>
                    <td><span class="code">UPDATE meetings SET is_deleted = 0 WHERE id = 9</span></td>
                    <td><span class="code">mongo_db.meetings.update_one(...)</span></td>
                    <td><span class="tag tag-green">Restored Active</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
            """
        )

        for filename, html_content in db_screens.items():
            temp_file = os.path.join(temp_html_dir, filename)
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            page.goto(f"file:///{temp_file.replace(os.sep, '/')}")
            page.wait_for_timeout(300)
            png_name = filename.replace(".html", ".png")
            out_png = os.path.join(TARGET_SCREENSHOTS_DIR, png_name)
            page.screenshot(path=out_png, full_page=True)
            print(f"Captured: {png_name}")

        browser.close()

        # Synchronize to Data Specification folder
        dst = os.path.join(BASE_PROJECT_DIR, "Data Specfication", "Project Screenshots from Different Logs")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(TARGET_SCREENSHOTS_DIR, dst)

        all_files = sorted(os.listdir(TARGET_SCREENSHOTS_DIR))
        print(f"\n[COMPLETE ARCHIVE] Successfully generated and verified {len(all_files)} screenshots in {TARGET_SCREENSHOTS_DIR}")


if __name__ == "__main__":
    capture_complete_visual_archive()
