# Nexus AEG – Autonomous Exam Governance

Production‑ready AI system for smart campus scheduling.

## Features
- Multi‑tenant Firebase Authentication
- Live Adaptive Autonomy with background monitor
- Firestore persistent memory
- OR‑Tools optimisation engine
- Gemini‑powered explanations and chat
- SHA‑256 audit ledger
- SMS notifications (Africa’s Talking)
- PDF/DOCX import with AI extraction
- Predictive analytics dashboard

## Quick Start

1. Set environment variables (see `.env.example`)
2. Install dependencies: `pip install -r requirements.txt`
3. Run locally: `streamlit run app.py`
4. Deploy to Cloud Run: `gcloud run deploy nexus-aeg --source .`

## Project Structure
- `engine/` – core logic (scheduler, memory, monitor, analytics, etc.)
- `parsers/` – file parsing (CSV, Excel, PDF, DOCX)
- `utils/` – Firebase auth and initialisation
- `app.py` – main Streamlit UI