# MeetingOS 

An autonomous AI workflow system designed to instantly transform unstructured meeting notes and audio recordings into actionable, tracked tasks. 

MeetingOS utilizes local Machine Learning models to ensure absolute data privacy, bypassing the need for expensive API keys while delivering enterprise-grade natural language processing.

## 🚀 Features

* **AI-Powered Task Extraction:** Automatically parses raw text to identify action items, assignees, deadlines, and priority levels.
* **Audio Transcription:** Upload `.m4a`, `.mp3`, or `.wav` meeting recordings to automatically transcribe and extract tasks using OpenAI's Whisper model.
* **Autonomous Agents:** Features independent background agents (Escalation, Decision, and Audit) that autonomously monitor workloads and flag overdue tasks.
* **Production Dashboard:** A modern, reactive, dark-mode Single Page Application (SPA) with real-time analytics, timelines, and workload tracking.
* **100% Local & Private:** All NLP and audio processing happens directly on your machine.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI
* **Frontend:** Vanilla JavaScript, HTML5, CSS3
* **Database:** SQLite (Persistent storage)
* **Machine Learning / AI:** * `spaCy` (Natural Language Processing & Entity Recognition)
  * `OpenAI Whisper` (Audio Transcription)
  * `ffmpeg` (Audio processing)

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your machine:
* Python 3.9+
* Git
* FFmpeg (Required for audio processing)

## ⚙️ Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/MehulK711/MeetingAI.git](https://github.com/MehulK711/MeetingAI.git)
cd MeetingAI
