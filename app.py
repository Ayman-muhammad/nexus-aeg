"""
Nexus AEG – Streamlit Frontend
Integrates authentication, data ingestion, live monitoring, and engine control.
"""
import streamlit as st
import pandas as pd
import os
import time
from streamlit_autorefresh import st_autorefresh

# Local modules
from engine.core import NexusEngine
from engine.monitor import LiveMonitor
from engine.models import Building, Unit, Assessment
from parsers.file_parser import parse_file
from utils.auth import login, logout, is_authenticated, get_user_university_id
from dotenv import load_dotenv
from utils.firebase_init import init_firebase


load_dotenv()

# -------------------------------------------------------------------
# Page configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Nexus AEG – Autonomous Exam Governance",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialise Firebase once
init_firebase()

# Custom CSS (professional dark theme)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    h1, h2, h3 { color: #e0e0e0; font-weight: 500; }
    div[data-testid="metric-container"] { background-color: #1e2128; border: 1px solid #2e333d; border-radius: 8px; padding: 15px; }
    .stButton button { background-color: #2e7d32; color: white; border: none; border-radius: 6px; font-weight: 500; }
    .stButton button:hover { background-color: #1b5e20; }
    section[data-testid="stSidebar"] { background-color: #1a1d24; border-right: 1px solid #2e333d; }
    .stAlert { background-color: #2b2f38; border-left-color: #ffaa00; color: #e0e0e0; }
    .stChatInput { background-color: #1e2128; }
    @media (max-width: 768px) {
        .stButton button { width: 100%; }
        div[data-testid="column"] { min-width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Authentication
# -------------------------------------------------------------------
if not is_authenticated():
    st.title("🔐 Nexus AEG – Login")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="registrar@mku.ac.ke")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width='stretch')
        if submitted:
            if login(email, password):
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid email or password")
    st.stop()

# -------------------------------------------------------------------
# Initialise session state
# -------------------------------------------------------------------
if "engine" not in st.session_state:
    university_id = get_user_university_id()
    st.session_state.engine = NexusEngine(university_id)
    st.session_state.monitor = None
    st.session_state.data_loaded = False
    st.session_state.messages = []  # for assistant chat

engine = st.session_state.engine

# -------------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=NEXUS+AEG", use_container_width='stretch')
    st.markdown(f"**Logged in as:** {st.session_state.user['email']}")
    if st.button("🚪 Logout", use_container_width='stretch'):
        logout()
        st.rerun()

    st.markdown("---")
    st.header("📂 Data Ingestion")

    with st.expander("Upload Files", expanded=not st.session_state.data_loaded):
        buildings_file = st.file_uploader("Buildings (CSV/XLSX/PDF/DOCX)", type=["csv", "xlsx", "pdf", "docx"], key="buildings")
        units_file = st.file_uploader("Units", type=["csv", "xlsx", "pdf", "docx"], key="units")
        assessments_file = st.file_uploader("Assessments", type=["csv", "xlsx", "pdf", "docx"], key="assessments")

        if st.button("🚀 Load Data", use_container_width='stretch'):
            with st.spinner("Loading and validating..."):
                try:
                    buildings = parse_file(buildings_file, "buildings", engine.reasoner) if buildings_file else []
                    units = parse_file(units_file, "units", engine.reasoner) if units_file else []
                    assessments = parse_file(assessments_file, "assessments", engine.reasoner) if assessments_file else []

                    # If no files uploaded, try loading from Firestore
                    if not buildings:
                        buildings = engine.memory.get_buildings()
                    if not units:
                        units = engine.memory.get_units()
                    if not assessments:
                        assessments = engine.memory.get_assessments()

                    # If still empty, use sample data as fallback
                    if not buildings:
                        buildings = [Building(code="HALL_A", name="Main Hall", capacity=150)]
                    if not units:
                        units = [Unit(code="CS101", name="Intro to CS", year=1, semester=1, exam_duration_minutes=120)]
                    if not assessments:
                        assessments = [Assessment(unit_code="CS101", student_count=120, current_room="HALL_A", current_slot="2025-05-10 09:00")]

                    engine.load_data(buildings, units, assessments)

                    # Save to Firestore for future sessions
                    engine.memory.save_buildings(buildings)
                    engine.memory.save_units(units)
                    engine.memory.save_assessments(assessments)

                    st.session_state.data_loaded = True
                    st.success("Data loaded and saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load data: {str(e)}")

    st.markdown("---")

    # Live mode toggle
    st.header("⚙️ Control")
    live_mode = st.toggle("⚡ Live Autonomous Mode", value=engine.live_mode)
    if live_mode != engine.live_mode:
        engine.live_mode = live_mode
        if live_mode:
            if st.session_state.monitor is None:
                st.session_state.monitor = LiveMonitor(engine)
                st.session_state.monitor.start()
            st.success("Live mode ACTIVE – system will auto‑resolve anomalies")
        else:
            if st.session_state.monitor:
                st.session_state.monitor.stop()
                st.session_state.monitor = None
            st.info("Live mode OFF – anomalies require approval")

    # Admin phone numbers (optional)
    st.markdown("---")
    st.header("📞 Admin Alerts")
    admin_numbers = st.text_input("Phone numbers (comma-separated)", value=os.environ.get("ADMIN_PHONE_NUMBERS", ""))
    if st.button("Save Numbers", use_container_width='stretch'):
        os.environ["ADMIN_PHONE_NUMBERS"] = admin_numbers  # only for session; in production, store in Firestore
        st.success("Saved for this session")

    st.markdown("---")
    st.caption("© 2025 Nexus AEG – AI Governance for Education")

# -------------------------------------------------------------------
# Main navigation
# -------------------------------------------------------------------
tabs = st.tabs(["🏠 Dashboard", "🚨 Simulation", "📈 Predictive", "➕ New Exam", "🤖 Assistant", "📜 Audit"])

# -------------------------------------------------------------------
# Tab 1: Dashboard
# -------------------------------------------------------------------
with tabs[0]:
    if not st.session_state.data_loaded:
        st.info("👈 Please upload data files in the sidebar and click 'Load Data'.")
        st.stop()

    st.title("🏛️ Nexus AEG – Autonomous Exam Governance")
    st.caption("Real‑time academic oversight with adaptive intelligence")

    # Metrics row
    metrics = engine.get_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Total Exams", metrics["total_assessments"])
    col2.metric("⚠️ Pending Conflicts", metrics["pending_decisions"])
    col3.metric("✅ Resolved", metrics["resolved_conflicts"])
    col4.metric("📊 Room Utilisation", f"{metrics['room_utilization']}%")

    # Live alerts feed (auto‑refresh every 10 seconds)
    st.subheader("📡 Live Event Feed")
    monitor = st.session_state.monitor
    if monitor:
        st_autorefresh(interval=10000, limit=100, key="alert_refresh")
        alerts = monitor.get_alerts()
        if alerts:
            for alert in reversed(alerts[-10:]):
                if alert["type"] == "overcrowding":
                    st.warning(f"⚠️ **Overcrowding** – {alert['unit']} in {alert['room']} ({alert['students']} > {alert['capacity']})")
                elif alert["type"] == "double_booking":
                    st.error(f"🚨 **Double‑booking** – Room {alert['room']} at {alert['slot']}")
                elif alert["type"] == "auto_resolved":
                    st.success(f"⚡ **Auto‑resolved** – Assessment {alert['assessment_id'][:8]} moved")
                else:
                    st.info(f"{alert}")
        else:
            st.info("No recent events – system nominal.")
    else:
        st.info("Live mode is off. Enable in sidebar to monitor events.")

    # Pending decisions
    st.subheader("⏳ Pending Decisions")
    pending = engine.get_pending_decisions()
    if not pending:
        st.success("No pending conflicts. All schedules are optimal.")
    else:
        for idx, dec in enumerate(pending):
            with st.container(border=True):
                cols = st.columns([3, 1])
                cols[0].markdown(f"**{dec['unit']}** – Conflict detected")
                with cols[1]:
                    st.markdown(f"🆔 `{dec['assessment_id'][:8]}`")

                options = dec['options']
                option_labels = [
                    f"{opt['proposed_room']} at {opt['proposed_slot']} (score: {opt['score']:.2f})"
                    for opt in options
                ]
                selected = st.radio(
                    "Choose resolution:",
                    options=range(len(options)),
                    format_func=lambda i: option_labels[i],
                    key=f"pending_{idx}",
                    label_visibility="collapsed"
                )
                if st.button("✅ Approve", key=f"approve_{idx}"):
                    try:
                        msg = engine.registrar_authorize(idx, selected)
                        st.success(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Approval failed: {e}")

                if options[selected].get("reasoning"):
                    with st.expander("🤖 AI Reasoning"):
                        st.write(options[selected]["reasoning"])

# -------------------------------------------------------------------
# Tab 2: Simulation
# -------------------------------------------------------------------
with tabs[1]:
    st.title("🚨 Simulation Mode")
    st.markdown("Adjust parameters to see how the system reacts.")

    if not st.session_state.data_loaded:
        st.info("Please load data first.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        new_student_count = st.slider("Increase student numbers by (%)", 0, 100, 20)
    with col2:
        conflict_prob = st.slider("Conflict probability (random)", 0.0, 1.0, 0.3)

    if st.button("▶️ Run Simulation"):
        with st.spinner("Simulating..."):
            import random
            sim_assessments = []
            for a in engine.assessments:
                new_count = int(a.student_count * (1 + new_student_count/100))
                if random.random() < conflict_prob:
                    small_rooms = [b for b in engine.buildings if b.capacity < new_count]
                    if small_rooms:
                        a_clone = a.copy()
                        a_clone.student_count = new_count
                        a_clone.current_room = small_rooms[0].code
                        sim_assessments.append(a_clone)
                    else:
                        sim_assessments.append(a)
                else:
                    sim_assessments.append(a)

            sim_engine = NexusEngine(engine.university_id)
            sim_engine.load_data(engine.buildings, engine.units, sim_assessments)
            conflicts = sim_engine.detect_conflicts()

            st.subheader("Simulation Results")
            st.write(f"Detected **{len(conflicts)}** conflicts in simulated schedule.")
            if conflicts:
                st.dataframe(pd.DataFrame(conflicts))
            else:
                st.success("No conflicts detected in simulated data.")

# -------------------------------------------------------------------
# Tab 3: Predictive Analytics
# -------------------------------------------------------------------
with tabs[2]:
    st.title("📈 Predictive Analytics")
    st.markdown("Forecast future conflicts and utilization trends.")

    if not st.session_state.data_loaded or engine.analytics is None:
        st.info("Please load data first.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔮 Predicted Hotspots")
        hotspots = engine.analytics.forecast_clash_hotspots()
        if hotspots:
            for h in hotspots:
                st.warning(f"**{h['slot']}** – {h['risk_level']} risk (predicted congestion: {h['predicted_congestion']})")
        else:
            st.success("No high-risk hotspots predicted.")

    with col2:
        st.subheader("📊 Utilization Trend")
        trend_df = engine.analytics.utilization_trend()
        st.line_chart(trend_df.pivot(index="date", columns="building", values="utilization"))

    st.subheader("🔥 Current Risk Hotspots")
    hotspots_now = engine.analytics.risk_hotspots()
    if hotspots_now:
        st.dataframe(pd.DataFrame(hotspots_now))
    else:
        st.info("No high-risk rooms identified.")

# -------------------------------------------------------------------
# Tab 4: New Exam
# -------------------------------------------------------------------
with tabs[3]:
    st.title("➕ Add New Assessment")

    with st.form("new_exam_form"):
        unit_code = st.text_input("Unit Code", placeholder="CS101")
        student_count = st.number_input("Number of Students", min_value=1, value=50)
        preferred_room = st.selectbox("Preferred Room", [b.code for b in engine.buildings] if engine.buildings else ["HALL_A"])
        preferred_slot = st.text_input("Preferred Slot (YYYY-MM-DD HH:MM)", placeholder="2025-05-10 09:00")
        submitted = st.form_submit_button("Add Assessment")

        if submitted:
            try:
                new_assessment = Assessment(
                    unit_code=unit_code,
                    student_count=student_count,
                    current_room=preferred_room,
                    current_slot=preferred_slot
                )
                engine.assessments.append(new_assessment)
                st.success(f"Assessment {new_assessment.id} added successfully!")
                engine.detect_conflicts()
            except Exception as e:
                st.error(f"Invalid data: {e}")

# -------------------------------------------------------------------
# Tab 5: Assistant
# -------------------------------------------------------------------
with tabs[4]:
    st.title("🤖 Nexus Assistant")
    st.caption("Ask questions about the schedule, policies, or get recommendations.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = engine.reasoner.chat_response(prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------------------------------------------
# Tab 6: Audit Ledger
# -------------------------------------------------------------------
with tabs[5]:
    st.title("📜 Audit Ledger")
    st.markdown("Immutable record of all actions (SHA‑256 hashed chain).")

    if st.button("🔍 Verify Ledger Integrity"):
        with st.spinner("Verifying..."):
            valid = engine.ledger.verify_chain()
            if valid:
                st.success("✅ Ledger is intact – all hashes match.")
            else:
                st.error("❌ Ledger corruption detected!")

    # Fetch last 20 entries
    entries = list(engine.ledger.collection.order_by("timestamp", direction="DESCENDING").limit(20).stream())
    if entries:
        data = []
        for e in entries:
            d = e.to_dict()
            data.append({
                "Time": d.get("timestamp").strftime("%Y-%m-%d %H:%M") if d.get("timestamp") else "",
                "Assessment": d.get("assessment_id")[:8],
                "Action": d.get("action"),
                "Auto": "✅" if d.get("auto") else "❌",
                "Hash": d.get("hash")[:10] + "..."
            })
        st.dataframe(pd.DataFrame(data), use_container_width='stretch')
    else:
        st.info("No audit entries yet.")