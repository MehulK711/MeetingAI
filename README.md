# MeetingOS — Autonomous Meeting-to-Execution AI Workflow System

> **Transform unstructured meeting notes into tracked, escalated, and audited tasks — powered by local NLP. No API key required.**

---

## Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [ML Pipeline](#ml-pipeline)
- [Folder Structure](#folder-structure)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Frontend Sections](#frontend-sections)
- [Multi-Agent Design](#multi-agent-design)
- [Database Schema](#database-schema)
- [Sample Input & Output](#sample-input--output)
- [Troubleshooting](#troubleshooting)
- [Future Roadmap](#future-roadmap)

---

## Project Overview

MeetingOS is a **production-grade autonomous workflow system** that solves one of the most common productivity failures in organizations — untracked meeting action items.

### The Problem

- 70% of meeting action items are forgotten within 48 hours
- Manual task creation from meeting notes is slow and inconsistent
- No automatic escalation when deadlines are missed
- No audit trail of who committed to what and when

### The Solution

MeetingOS automatically:

1. Parses raw meeting transcripts using a local NLP pipeline
2. Extracts structured tasks with owner, deadline, and priority
3. Stores tasks in a database with full audit logging
4. Monitors SLA deadlines and escalates overdue tasks
5. Provides a real-time dashboard with analytics and performance metrics

### Type of ML Problem

This is a **multi-task NLP pipeline** combining:

| Task | Type | Algorithm |
|---|---|---|
| Task sentence detection | Binary classification | Rule-based (action verbs) |
| Owner extraction | Named Entity Recognition | spaCy statistical NER |
| Deadline extraction | Temporal NLP | Regex + dateparser |
| Priority classification | Multi-class classification | Keyword scoring |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEETINGOS v3                             │
│                                                                 │
│   Browser (Frontend)                                            │
│   ├── Dashboard    ├── Analytics   ├── Workload                 │
│   ├── Timeline     ├── Audit Log   └── Performance              │
│            │                                                    │
│            │ HTTP REST API                                       │
│            ▼                                                    │
│   FastAPI Backend (port 8000)                                   │
│   ├── meeting_routes.py   (POST /process-meeting)               │
│   └── task_routes.py      (GET /tasks, PUT /update-task-status) │
│            │                                                    │
│            ▼                                                    │
│   ML Pipeline (Local, Offline)                                  │
│   ├── extractor.py        (spaCy NLP)                           │
│   ├── priority_model.py   (Keyword classifier)                  │
│   └── date_parser.py      (Temporal extraction)                 │
│            │                                                    │
│            ▼                                                    │
│   Multi-Agent System                                            │
│   ├── audit_agent.py      (Immutable event logging)             │
│   ├── escalation_agent.py (Deadline monitoring)                 │
│   └── decision_agent.py   (Urgency scoring, workload)           │
│            │                                                    │
│            ▼                                                    │
│   SQLite Database (meeting_workflow.db)                         │
│   ├── tasks table                                               │
│   ├── meetings table                                            │
│   └── audit_logs table                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## ML Pipeline

### How Task Extraction Works

```
Raw Meeting Text
      │
      ▼
Step 1: Text Cleaning & Sentence Segmentation
        → spaCy splits text into sentences
        → Newline-aware splitting handles meeting note format
      │
      ▼
Step 2: Task Sentence Detection
        → Filter sentences containing action verbs
          (will, must, needs, should, complete, fix, design...)
        → Skip discussion sentences
          (we discussed, the team agreed, today's agenda...)
      │
      ▼
Step 3: Owner Extraction (NER)
        → spaCy en_core_web_sm identifies PERSON entities
        → Fallback: regex pattern "Name will/should/must..."
        → Fallback: "Name:" prefix pattern
        → Final fallback: "Unassigned"
      │
      ▼
Step 4: Deadline Extraction
        → Pattern 1: Relative ("end of week" → Friday)
        → Pattern 2: Absolute ("April 20" → 2026-04-20)
        → Pattern 3: dateparser NLP
        → Final fallback: today + 7 days
      │
      ▼
Step 5: Priority Classification
        → HIGH:   asap, urgent, critical, immediately, blocker
        → MEDIUM: soon, important, this week, follow up
        → LOW:    eventually, nice to have, backlog
        → Default: medium
      │
      ▼
Structured Task Objects
[{task, owner, deadline, priority}, ...]
```

---

## Folder Structure

```
ai_workflow/
│
├── backend/
│   ├── main.py                    # FastAPI app, startup, CORS
│   ├── database.py                # SQLite init, connection manager
│   ├── models.py                  # Pydantic request/response models
│   ├── ai_service.py              # ML service interface layer
│   ├── requirements.txt           # Python dependencies
│   ├── meeting_workflow.db        # SQLite database (auto-created)
│   │
│   ├── ml_model/                  # Local ML pipeline
│   │   ├── __init__.py
│   │   ├── extractor.py           # Core NLP extraction (spaCy)
│   │   ├── priority_model.py      # Priority keyword classifier
│   │   └── date_parser.py         # Deadline extraction
│   │
│   ├── agents/                    # Multi-agent system
│   │   ├── __init__.py
│   │   ├── audit_agent.py         # Immutable audit logger
│   │   ├── escalation_agent.py    # Overdue detection & escalation
│   │   └── decision_agent.py      # Urgency scoring & workload
│   │
│   ├── routes/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── meeting_routes.py      # Meeting processing endpoints
│   │   └── task_routes.py         # Task CRUD + analytics endpoints
│   │
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       └── helpers.py             # task_row_to_response() converter
│
├── frontend/
│   ├── index.html                 # Full single-page application
│   ├── style.css                  # 874-line professional dark theme
│   └── script.js                  # 781-line full JS application
│
└── README.md                      # This file
```

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| FastAPI | 0.111.0 | REST API framework |
| Uvicorn | 0.29.0 | ASGI server |
| Pydantic | 2.7.1 | Data validation |
| spaCy | 3.7.4 | NLP engine (NER, tokenization) |
| dateparser | 1.2.0 | Natural language date extraction |
| scikit-learn | 1.4.2 | ML utilities (extensible) |
| NumPy | 1.26.4 | Numerical operations |
| SQLite | Built-in | Persistent storage |

### Frontend

| Technology | Purpose |
|---|---|
| HTML5 | Structure |
| CSS3 | Styling (CSS variables, grid, animations) |
| Vanilla JavaScript | Full SPA logic, API calls, rendering |
| Google Fonts (Syne + Inter + JetBrains Mono) | Typography |

### ML Models

| Model | Source | Size | Purpose |
|---|---|---|---|
| en_core_web_sm | spaCy | 12MB | NER, tokenization, sentence detection |
| dateparser | pip | 5MB | Temporal expression extraction |
| Priority classifier | Custom (rule-based) | 0MB | Keyword-based priority scoring |

---

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- 500MB free disk space (for spaCy model)
- Internet connection (for initial setup only)

### Step 1 — Clone / Download the Project

```
ai_workflow/
├── backend/
└── frontend/
```

### Step 2 — Create Virtual Environment

```powershell
# Windows
cd C:\Users\YourName\ai_workflow
python -m venv venv
venv\Scripts\activate
```

```bash
# Mac/Linux
cd ~/ai_workflow
python -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

### Step 4 — Download spaCy NLP Model

```powershell
python -m spacy download en_core_web_sm
```

This downloads the `en_core_web_sm` model (12MB) which powers:
- Named Entity Recognition (person name detection)
- Sentence boundary detection
- Part-of-speech tagging

### Step 5 — Verify Installation

```powershell
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy OK')"
python -c "import dateparser; print('dateparser OK')"
python -c "import fastapi; print('FastAPI OK')"
```

All three should print OK.

---

## Running the Project

### Terminal 1 — Start Backend

```powershell
cd C:\Users\YourName\ai_workflow\backend
venv\Scripts\activate
python main.py
```

**Expected output:**
```
INFO: Initializing database...
INFO: Database ready.
INFO: spaCy model loaded successfully.
INFO: Local ML model (spaCy) loaded successfully.
INFO: Startup escalation: 0 overdue, 0 escalated
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Start Frontend

```powershell
cd C:\Users\YourName\ai_workflow\frontend
python -m http.server 3000
```

**Expected output:**
```
Serving HTTP on :: port 3000 (http://[::]:3000/) ...
```

### Step 3 — Open Browser

```
http://localhost:3000
```

> ⚠️ Always use `localhost` not `0.0.0.0` in the browser

### Verify Backend is Running

Open in browser:
```
http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "local_ml",
  "ml_model": "spaCy en_core_web_sm",
  "version": "2.0.0"
}
```

---

## API Reference

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### POST /process-meeting
Extract tasks from meeting text using the ML pipeline.

**Request:**
```json
{
  "text": "Sarah will redesign the onboarding flow by April 20. High priority.\nJohn must fix the login bug ASAP."
}
```

**Response:**
```json
{
  "meeting_id": "mtg_a3f7b2c1d4e5",
  "task_count": 2,
  "tasks": [
    {
      "id": 1,
      "task": "Redesign the onboarding flow by April 20.",
      "owner": "Sarah",
      "deadline": "2026-04-20",
      "priority": "high",
      "status": "pending",
      "sla_hours": 48,
      "escalated": false,
      "days_until_deadline": 7,
      "is_overdue": false,
      "created_at": "2026-04-13 10:00:00",
      "updated_at": "2026-04-13 10:00:00"
    }
  ],
  "message": "Successfully extracted 2 task(s) from meeting."
}
```

---

#### GET /tasks
Get all tasks with optional filters.

**Query Parameters:**

| Parameter | Type | Example | Description |
|---|---|---|---|
| status | string | `overdue` | Filter by status |
| priority | string | `high` | Filter by priority |
| owner | string | `John` | Filter by owner name |

**Response:** Array of task objects (same structure as above)

---

#### PUT /update-task-status
Update the status of a specific task.

**Request:**
```json
{
  "task_id": 1,
  "status": "completed",
  "actor": "user",
  "note": "Deployed to production"
}
```

**Valid status values:** `pending` | `in-progress` | `completed` | `overdue`

---

#### GET /logs
Get audit log entries.

**Query Parameters:**

| Parameter | Default | Description |
|---|---|---|
| limit | 100 | Max entries to return (max 500) |
| event_type | — | Filter by event type |

**Event Types:**
- `MEETING_PROCESSED`
- `TASK_CREATED`
- `TASK_STATUS_UPDATED`
- `TASK_ESCALATED`
- `SLA_BREACH_DETECTED`
- `AI_EXTRACTION_FAILED`

---

#### GET /analytics
Get KPI metrics and breakdowns.

**Response:**
```json
{
  "total_tasks": 15,
  "pending": 5,
  "in_progress": 4,
  "completed": 3,
  "overdue": 3,
  "escalated": 2,
  "completion_rate": 20.0,
  "overdue_rate": 20.0,
  "priority_breakdown": {"high": 6, "medium": 7, "low": 2},
  "owner_breakdown": {
    "Sarah": {"total": 5, "completed": 2, "overdue": 1}
  }
}
```

---

#### POST /escalate
Manually trigger the escalation agent sweep.

**Response:**
```json
{
  "status": "ok",
  "newly_overdue": 2,
  "escalated": 2,
  "errors": []
}
```

---

#### GET /workload
Get per-owner workload analysis.

---

#### GET /api/health
Health check endpoint.

---

## Frontend Sections

### 🏠 Dashboard (Default View)
- **Meeting Input Panel** — Paste meeting notes and extract tasks
- **Task Board** — All tasks with sort (Urgency / Deadline / Owner) and filters
- **Audit Feed** — Real-time event stream
- **SLA Meter** — Completion and overdue rate rings
- **Stats Row** — Total, Completed, Active, Overdue counts
- **Search** — Live search across task name, owner, priority, status

### 📊 Analytics
- 5 KPI metric cards with trend indicators
- Animated SVG donut chart (status breakdown)
- Priority distribution horizontal bar chart
- Owner task distribution bars
- Completion rate ring chart

### 👥 Workload
- Per-owner card with avatar initials
- Task count breakdown (Total / Done / Overdue)
- Completion rate progress bar
- Overload warning badge (>5 tasks or >2 high priority)

### 📅 Timeline
- All active tasks sorted by deadline (ascending)
- Color-coded timeline nodes (red = overdue, yellow = medium, green = low)
- Clickable cards open task detail modal

### 📋 Audit Log
- Full audit event table (200 most recent events)
- Filterable by event type
- Color-coded event tags
- Shows: timestamp, event, entity, actor, description
- Manual refresh button

### 🏆 Performance
- Team leaderboard ranked by completion rate
- 🥇🥈🥉 medal system for top 3
- Per-member metrics: Assigned / Done / Overdue
- Completion rate progress bar
- Summary strip showing top performers

---

## Multi-Agent Design

### Agent 1: ML Extraction Agent (`extractor.py`)
- **Role:** Core intelligence layer
- **Trigger:** Every POST /process-meeting request
- **Actions:** Sentence segmentation → NER → date extraction → priority classification
- **Logs:** `TASK_CREATED` for every extracted task

### Agent 2: Escalation Agent (`escalation_agent.py`)
- **Role:** Deadline enforcer
- **Trigger:** Startup + every POST /process-meeting + POST /escalate
- **Actions:** Marks pending/in-progress tasks as overdue when deadline < today
- **Actions:** Flags newly overdue tasks as escalated
- **Actions:** Suggests task reassignment based on other owners
- **Logs:** `TASK_STATUS_UPDATED`, `SLA_BREACH_DETECTED`, `TASK_ESCALATED`

### Agent 3: Audit Agent (`audit_agent.py`)
- **Role:** Immutable event ledger
- **Trigger:** Called by all other agents and routes
- **Actions:** Writes structured event records to audit_logs table
- **Never raises:** All failures logged to stderr only
- **Guarantees:** Every action in the system has a corresponding log entry

### Agent 4: Decision Agent (`decision_agent.py`)
- **Role:** Strategic analysis layer
- **Trigger:** On-demand via API calls
- **Actions:** Computes urgency scores for tasks
- **Actions:** Analyzes owner workload distribution
- **Actions:** Detects overload risk (>5 tasks or >2 high priority per person)

---

## Database Schema

### tasks table
```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id  TEXT    NOT NULL,
    task        TEXT    NOT NULL,
    owner       TEXT    NOT NULL,
    deadline    TEXT    NOT NULL,         -- YYYY-MM-DD format
    priority    TEXT    NOT NULL CHECK(priority IN ('high','medium','low')),
    status      TEXT    NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','in-progress','completed','overdue')),
    sla_hours   INTEGER DEFAULT 48,       -- SLA window in hours
    escalated   INTEGER DEFAULT 0,        -- 0=false, 1=true
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### meetings table
```sql
CREATE TABLE meetings (
    id           TEXT PRIMARY KEY,        -- mtg_<hex>
    raw_text     TEXT NOT NULL,
    processed_at TEXT NOT NULL DEFAULT (datetime('now')),
    task_count   INTEGER DEFAULT 0
);
```

### audit_logs table
```sql
CREATE TABLE audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,
    entity_type TEXT NOT NULL,            -- 'task' or 'meeting'
    entity_id   TEXT NOT NULL,
    actor       TEXT NOT NULL DEFAULT 'system',
    description TEXT NOT NULL,
    metadata    TEXT,                     -- JSON string
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Sample Input & Output

### Sample Meeting Input

```
Q3 Planning Meeting — April 2026

Sarah will redesign the onboarding flow by April 20. High priority.
John needs to complete the API integration ASAP — it is critical for the launch.
The marketing team should prepare the campaign assets by April 25.
Dev team must fix the login bug before end of this week.
Alice will review the Q3 budget proposal by April 18.
```

### Expected Output (5 Tasks)

| # | Task | Owner | Deadline | Priority |
|---|---|---|---|---|
| 1 | Redesign the onboarding flow | Sarah | Apr 20, 2026 | 🔴 High |
| 2 | Complete the API integration | John | Apr 20, 2026 | 🔴 High |
| 3 | Prepare the campaign assets | Marketing Team | Apr 25, 2026 | 🟡 Medium |
| 4 | Fix the login bug | Dev Team | Apr 17, 2026 | 🟡 Medium |
| 5 | Review the Q3 budget proposal | Alice | Apr 18, 2026 | 🟡 Medium |

---

## Troubleshooting

### Backend won't start

```
Error: No module named 'spacy'
Solution: pip install spacy

Error: No module named 'spacy.lang.en'
Solution: python -m spacy download en_core_web_sm

Error: cannot import name 'format_duration' from 'utils.helpers'
Solution: Open backend/utils/__init__.py and make it completely empty
```

### Frontend shows "Backend Offline"

```
Check 1: Is backend running? → python main.py should show "Uvicorn running"
Check 2: Use localhost:3000, not 0.0.0.0:3000
Check 3: Check http://localhost:8000/api/health in browser
Check 4: Both terminals must stay open simultaneously
```

### No tasks extracted from meeting

```
Cause 1: Sentences don't contain action verbs
Fix: Use sentences like "John WILL complete..." or "Sarah MUST review..."

Cause 2: Text too short (< 20 characters)
Fix: Add more meeting context

Cause 3: All sentences are discussion (past tense)
Fix: Include future-tense action items
```

### spaCy model not found

```powershell
# Run this command
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm'); print('OK')"
```

---

## Future Roadmap

### Phase 1 — Enhanced ML (Next Steps)
- [ ] Train scikit-learn LogisticRegression priority classifier on labeled data
- [ ] Add coreference resolution (resolve pronouns to person names)
- [ ] Multi-language support (spaCy multilingual models)
- [ ] Confidence scores for each extraction

### Phase 2 — Integrations
- [ ] Jira API integration (auto-create Jira tickets)
- [ ] Slack bot (post overdue task alerts to channels)
- [ ] Google Calendar integration (add deadlines to calendar)
- [ ] Email escalation notifications

### Phase 3 — Advanced ML
- [ ] Fine-tune BERT/RoBERTa on meeting-specific task extraction
- [ ] Active learning pipeline (human feedback improves model)
- [ ] Audio input support (OpenAI Whisper for meeting recordings)
- [ ] Sentiment analysis on meeting tone

### Phase 4 — Production Scale
- [ ] PostgreSQL migration for concurrent write workloads
- [ ] Redis caching for analytics queries
- [ ] Docker containerization
- [ ] Kubernetes deployment with horizontal scaling
- [ ] Prometheus + Grafana monitoring

---

## License

MIT License — Free for educational and commercial use.

---

## Acknowledgements

- **spaCy** by Explosion AI — The NLP backbone of this system
- **dateparser** — Natural language date extraction
- **FastAPI** by Sebastián Ramírez — The most productive Python API framework
- **SQLite** — Zero-configuration embedded database

---

*Built as a hackathon project demonstrating multi-agent AI workflow automation with local ML inference.*
"# MeetFlow-AI" 
"# MeetFlow-AI" 
