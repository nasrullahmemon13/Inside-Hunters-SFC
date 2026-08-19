import os
import sys
import time
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
    flask_app_module.app.run(host="127.0.0.1", port=5009, debug=False, use_reloader=False)


def capture_all_screenshots():
    seed_database()

    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    time.sleep(2.0)

    print("[Playwright] Starting headless Chrome browser...")
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

        base_url = "http://127.0.0.1:5009"

        def save(filename, full_page=False):
            target = os.path.join(TARGET_SCREENSHOTS_DIR, filename)
            page.screenshot(path=target, full_page=full_page)
            print(f"Captured: {filename}")

        # 1. Public Pages (Logged Out)
        page.goto(f"{base_url}/")
        page.wait_for_timeout(600)
        save("001_Landing_Hero_Section.png")
        save("002_Landing_Full_Page.png", full_page=True)

        # Login Screen
        page.goto(f"{base_url}/login")
        page.wait_for_timeout(400)
        save("003_Auth_Login_Screen.png")

        # Login Error State
        page.fill("input[name='email']", "invalid@user.com")
        page.fill("input[name='password']", "wrongpass")
        page.click("button[type='submit']")
        page.wait_for_timeout(500)
        save("004_Auth_Login_Error_Validation.png")

        # Register Screen
        page.goto(f"{base_url}/register")
        page.wait_for_timeout(400)
        save("005_Auth_Register_Screen.png")

        # Forgot Password Screen
        page.goto(f"{base_url}/forgot-password")
        page.wait_for_timeout(400)
        save("006_Auth_Forgot_Password_Screen.png")

        # Forgot Password Link Generated State
        page.fill("input[name='email']", "demo@talktotext.pro")
        page.click("button[type='submit']")
        page.wait_for_timeout(500)
        save("007_Auth_Forgot_Password_Success_State.png")

        # Reset Password Screen
        page.goto(f"{base_url}/reset-password?email=demo@talktotext.pro&token=demo_token_123")
        page.wait_for_timeout(400)
        save("008_Auth_Reset_Password_Screen.png")

        # Verify Email Screen
        page.goto(f"{base_url}/verify-email")
        page.wait_for_timeout(400)
        save("009_Auth_Verify_Email_Screen.png")

        # Help & Support Documentation
        page.goto(f"{base_url}/help")
        page.wait_for_timeout(400)
        save("010_Help_Support_Documentation.png", full_page=True)

        # 2. Authenticated Session: Log in as Demo User
        page.goto(f"{base_url}/login")
        page.fill("input[name='email']", "demo@talktotext.pro")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_timeout(600)

        # 3. Dashboard Screens
        page.goto(f"{base_url}/dashboard")
        page.wait_for_timeout(600)
        save("011_Dashboard_Overview_Dark_Theme.png")
        save("012_Dashboard_Full_Page_Dark.png", full_page=True)

        # Dashboard in Adaptive Light Mode
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(500)
        save("013_Dashboard_Overview_Light_Theme.png")
        save("014_Dashboard_Full_Page_Light.png", full_page=True)
        # Switch back to dark theme
        page.evaluate("toggleTheme()")
        page.wait_for_timeout(300)

        # Command Palette Modal (Ctrl+K)
        page.keyboard.press("Control+KeyK")
        page.wait_for_timeout(400)
        save("015_Global_Command_Palette_Modal.png")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # 4. Upload & Meeting Ingestion Hub
        page.goto(f"{base_url}/upload")
        page.wait_for_timeout(500)
        save("016_Upload_Audio_Ingestion_Hub.png")
        save("017_Upload_Full_Page_Templates.png", full_page=True)

        # Microphone Recording Simulated Active State
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
        except Exception as e:
            print("Mic state note:", e)

        # 5. Meeting Detail & Intelligence Views
        conn = get_db_connection()
        m_row = conn.execute("SELECT * FROM meetings WHERE user_id = 1 ORDER BY id DESC LIMIT 1").fetchone()
        meeting_id = m_row["id"] if m_row else 1
        share_token = m_row["share_token"] if m_row and m_row["share_token"] else "share123"
        conn.close()

        page.goto(f"{base_url}/meeting/{meeting_id}")
        page.wait_for_timeout(600)
        save("019_Meeting_Detail_Executive_Overview.png")
        save("020_Meeting_Detail_Full_Page_Intelligence.png", full_page=True)

        # Voice Mood & Acoustic Sentiment Section
        try:
            page.evaluate("document.querySelector('#tabPanePointsSentiment')?.scrollIntoView({ behavior: 'instant' })")
            page.wait_for_timeout(300)
            save("021_Meeting_Detail_Acoustic_Voice_Mood_Section.png")
        except Exception as e:
            print("Sentiment scroll note:", e)

        # AI Copilot Q&A Interaction
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
        except Exception as e:
            print("Chat interaction note:", e)

        # 6. Meeting History & Archive
        page.goto(f"{base_url}/history")
        page.wait_for_timeout(500)
        save("023_Meeting_History_Archive.png", full_page=True)

        # History with Filter (Favorites)
        page.goto(f"{base_url}/history?filter=favorites")
        page.wait_for_timeout(400)
        save("024_Meeting_History_Favorites_Filter.png")

        # History with Search Query
        page.goto(f"{base_url}/history?q=Roadmap")
        page.wait_for_timeout(400)
        save("025_Meeting_History_Search_Results.png")

        # 7. Action Items Tracker Hub
        page.goto(f"{base_url}/action-items")
        page.wait_for_timeout(500)
        save("026_Action_Items_Central_Hub.png", full_page=True)

        # Add Action Item Modal Open State
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
        except Exception as e:
            print("Action item modal note:", e)

        # 8. Decisions Intelligence Board
        page.goto(f"{base_url}/decisions")
        page.wait_for_timeout(500)
        save("028_Decisions_Intelligence_Log.png", full_page=True)

        # 9. Calendar Deliverables View
        page.goto(f"{base_url}/calendar")
        page.wait_for_timeout(500)
        save("029_Calendar_Deliverables_Schedule.png", full_page=True)

        # 10. Analytics & Performance Dashboard
        page.goto(f"{base_url}/analytics")
        page.wait_for_timeout(500)
        save("030_Analytics_Performance_Dashboard.png", full_page=True)

        # 11. Trash & Recovery Archive
        page.goto(f"{base_url}/trash")
        page.wait_for_timeout(500)
        save("031_Trash_Recovery_Archive.png", full_page=True)

        # 12. Notifications Center
        page.goto(f"{base_url}/notifications")
        page.wait_for_timeout(500)
        save("032_Notifications_Center_All.png", full_page=True)

        # Notifications Filter Tab (System Category)
        page.goto(f"{base_url}/notifications?cat=System")
        page.wait_for_timeout(400)
        save("033_Notifications_System_Filter.png")

        # 13. Settings & Preferences
        page.goto(f"{base_url}/settings")
        page.wait_for_timeout(500)
        save("034_Settings_General_Profile.png", full_page=True)

        # Settings Security Tab
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
        except Exception as e:
            print("Security tab note:", e)

        # Settings API Keys & Quota Tab
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
        except Exception as e:
            print("API Keys tab note:", e)

        # 14. Public Shared Note View
        page.goto(f"{base_url}/share/{share_token}")
        page.wait_for_timeout(500)
        save("037_Public_Shared_Meeting_Note.png", full_page=True)

        # 15. Weekly Executive Intelligence Digest HTML Preview
        page.goto(f"{base_url}/api/digest/preview")
        page.wait_for_timeout(500)
        save("038_Weekly_Intelligence_Digest_Email_Preview.png", full_page=True)

        # 16. Mobile Viewport Responsive Screens (390x844)
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            device_scale_factor=2.0
        )
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

        browser.close()
        print(f"\n[COMPLETE] Successfully generated 51 screenshots directly inside: {TARGET_SCREENSHOTS_DIR}")


if __name__ == "__main__":
    capture_all_screenshots()
