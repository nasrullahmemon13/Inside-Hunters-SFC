# 🎙️ TalkToText Pro — AI Meeting Intelligence Platform

> **Turn every conversation into an actionable, structured written record.**  
> Built with Python Flask, SQLite, MongoDB Atlas Sync, and Speech-to-Intelligence AI pipelines.

---

## ✨ Key Features

- **⚡ Multi-Preset Meeting Templates**:
  - `General Meeting`, `Daily Standup / Scrum`, `Client Discovery & Sales`, `1-on-1 Sync`, `Sprint Retrospective`, `Board & Executive Review`, and `Brainstorming & Ideation`.
  - Re-summarize any recorded meeting into different formats on demand.

- **🤖 Ask AI Meeting Assistant (Archive Intelligence)**:
  - Slide-over AI drawer searching across all past transcripts, decisions, and tasks.
  - Interactive quick question chips with instant answers grounded in your workspace history.

- **📦 Bulk Export & ZIP Archiving**:
  - Multi-select meetings in History to download bulk `.zip` archives containing formatted PDF reports, Microsoft Word `.docx` documents, Markdown `.md`, Plain Text `.txt`, and structured JSON.

- **📱 Progressive Web App (PWA)**:
  - Installable application with offline resilience and native mobile feel.

- **🔑 Bring Your Own API Keys & Quota Metering**:
  - Encrypted custom keys for OpenAI GPT-4o / Whisper, Groq, and Google Gemini.
  - Real-time token usage meter and monthly USD budget cap.

- **📬 Automated Weekly Email Digest**:
  - Clean HTML newsletter summarizing all team meetings, strategic agreements, and open action items.

- **🎙️ Voice Capture & Enhancer**:
  - HTML5 Live microphone recording and file upload (`.mp3`, `.wav`, `.m4a`, `.mp4`).
  - Background noise cleaner and speech optimizer.

---

## 📁 System Architecture

```
TalkToText Pro/
│
├── app.py                      # Main Flask application controllers & API routes
├── requirements.txt            # Python dependencies (Flask, ReportLab, docx, etc.)
├── .env.example                # Sample environment configuration template
├── .env                        # Local environment secrets
│
├── database/                   # SQLite database storage
│   └── app.db
│
├── models/
│   └── database.py             # SQLite schemas, auto-migrations & MongoDB sync
│
├── services/
│   ├── transcription.py        # Speech-to-Text (Whisper / Intelligent Fallback)
│   ├── translation.py          # Multilingual & Roman Urdu translator
│   ├── summarizer.py           # 7 Meeting templates & copilot engine
│   ├── export.py               # PDF, DOCX, TXT, ICS & Bulk ZIP generators
│   └── email_digest.py         # Weekly newsletter & digest compiler
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Master layout, PWA worker, & AI drawer
│   ├── index.html              # Landing page
│   ├── dashboard.html          # Analytics, KPIs, and meeting feed
│   ├── upload.html             # Studio upload & live recorder
│   ├── meeting_detail.html     # Meeting canvas, template switcher & player
│   ├── history.html            # Meeting library with bulk selection
│   ├── action_items.html       # Task tracking board
│   ├── decisions.html          # Strategic decisions intelligence
│   ├── calendar.html           # Meeting calendar sync
│   ├── analytics.html          # Productivity & sentiment trends
│   ├── settings.html           # API keys, tokens meter, & theme preferences
│   ├── share.html              # Public read-only meeting brief
│   └── auth/                   # Authentication views (login, register, reset)
│
├── static/
│   ├── manifest.json           # Web App PWA manifest
│   ├── sw.js                   # Service Worker for asset caching
│   ├── css/style.css           # Vanilla CSS tokens & design system
│   └── js/app.js               # Client interactive helpers
│
├── uploads/                    # Uploaded audio recordings
└── exports/                    # Generated exports & ZIP archives
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Environment Setup
```bash
# Clone or navigate to the repository directory
cd "TalkToText Pro"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

### 5. Launch the Application
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## 🔒 Security & Privacy
- Passwords hashed using modern `scrypt` cryptography.
- Custom API keys stored with encrypted isolation.
- Session-based CSRF protection and sanitized inputs.
