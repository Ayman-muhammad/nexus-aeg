# 🎓 Nexus AEG – Autonomous Exam Governance Platform

[![Python](https://img.shields.io/badge/python-3.11-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Streamlit](https://img.shields.io/badge/streamlit-v1.30-orange?style=for-the-badge)](https://streamlit.io/)
[![Firebase](https://img.shields.io/badge/firebase-Firestore-yellow?style=for-the-badge)](https://firebase.google.com/)

**Repository:** [https://github.com/Ayman-muhammad/nexus-aeg](https://github.com/Ayman-muhammad/nexus-aeg)


## 🚀 Executive Summary

**Nexus AEG** is a **fully autonomous, AI-driven exam governance engine** that:

- Optimizes exam scheduling  
- Detects and resolves conflicts automatically  
- Provides **predictive analytics** and AI-driven insights  
- Delivers **real-time student and faculty notifications**  
- Maintains a **tamper-proof SHA-256 audit ledger**  

This platform **aligns with Mount Kenya University (MKU)**’s smart campus initiatives—complementing systems like **UnIRP**, **smart classrooms**, and **biometric access**—to form a **holistic adaptive exam management ecosystem**.



## 🏛️ Problem Statement

Current exam operations are **manual and error-prone**, leading to:

- Room overbooking or underutilization  
- Schedule conflicts for students and invigilators  
- Delayed alerts and notifications  
- Poor auditability  

**Nexus AEG solves this by:**

- Automated conflict detection & resolution  
- Predictive room and slot management  
- Immutable ledger for accountability  
- AI explanations for decisions  
- Real-time notifications via SMS/email



## 🛠️ Key Features

| Feature | Description |
|---------|-------------|
| **AI-Optimized Scheduling** | Google OR-Tools solver minimizes conflicts & maximizes room usage |
| **Conflict Detection & Auto-Resolution** | Automatic relocation of conflicting exams |
| **Predictive Analytics Dashboard** | Room utilization, congestion forecasting, and risk hotspots |
| **Immutable Audit Ledger** | Tamper-proof SHA-256 logging for every action |
| **Multi-format Data Ingestion** | CSV, Excel, PDF, DOCX uploads |
| **Real-time Notifications** | SMS via Africa’s Talking API, optional email |
| **AI Reasoning & Chat** | Gemini-powered decision explanations |



## 🏗️ System Architecture

```text
+----------------------+       +-----------------------+
|  Admin / Registrar   |<----->|  Streamlit Frontend   |
+----------------------+       +-----------------------+
        |                               |
        v                               v
+----------------------+       +-----------------------+
|  Nexus Engine Core   |<----->| OR-Tools Scheduler    |
| - Conflict Detector  |       | - Constraint Solver   |
| - Analytics Engine   |       +-----------------------+
| - Gemini Reasoner    |
| - Notifier           |
+----------------------+
        |
        v
+----------------------+
| Firestore / Firebase |
| - Buildings          |
| - Units              |
| - Assessments        |
| - Audit Ledger       |
+----------------------+
📂 Project Structure
nexus-aeg/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── app.py                 # Streamlit frontend
├── engine/                # Core logic & AI engine
│   ├── __init__.py
│   ├── py.typed
│   ├── core.py
│   ├── scheduler.py
│   ├── memory.py
│   ├── monitor.py
│   ├── analytics.py
│   ├── notifier.py
│   ├── ledger.py
│   ├── gemini.py
│   └── models.py
├── parsers/               # Multi-format file parsers
│   ├── __init__.py
│   └── file_parser.py
└── utils/                 # Auth & Firebase helpers
    ├── __init__.py
    ├── auth.py
    └── firebase_init.py
⚡ Installation & Setup
# Clone repository
git clone https://github.com/YOUR_USERNAME/nexus-aeg.git
cd nexus-aeg

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Update .env with Firebase credentials, Africa's Talking API keys, etc.

# Run Streamlit frontend
streamlit run app.py
🏫 MKU Context & Integration

Mount Kenya University has implemented:

University Integrated Resource Platform (UnIRP) – AI-enabled administration

Smart Classrooms & Interactive Displays

Automated Security & Biometric Access Control

Robotics, AI & Immersive Technology Labs

Nexus AEG complements these initiatives by providing:

Autonomous exam scheduling & monitoring

AI-powered decision support for faculty/registrar

Predictive analytics for room utilization and conflict resolution

💡 Demo Workflow

Upload exam, building, and unit data

Detect & resolve conflicts (AI + OR-Tools)

Approve or auto-resolve conflicts

Track changes in immutable ledger

Notify students/staff via SMS/email

Review predictive analytics dashboards

🔮 Future Enhancements

Direct UnIRP API integration

Voice-enabled AI assistant for registrar & faculty queries

Multi-language notification support

Advanced ML forecasting for congestion & exam load

📜 License

MIT License – see LICENSE

📞 Contact

Developer: Ekalale Lokaale Ayman
Email: ayman11muhammad@gmail.com
GitHub: https://github.com/Ayman-muhammad
