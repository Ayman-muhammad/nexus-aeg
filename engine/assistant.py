import re
from typing import Optional
from .analytics import AnalyticsEngine
from .core import NexusEngine
from .gemini import GeminiReasoner

class Assistant:
    def __init__(self, engine: NexusEngine, analytics: AnalyticsEngine):
        self.engine = engine
        self.analytics = analytics
        self.gemini = GeminiReasoner()
        self.context = {}

    def answer(self, query: str) -> str:
        q = query.lower().strip()

        # Scheduling intent
        schedule_match = re.search(r'schedule\s+(\w+)\s+with\s+(\d+)\s+students', q)
        if schedule_match:
            unit_code = schedule_match.group(1).upper()
            student_count = int(schedule_match.group(2))
            ass_type = "Final"
            if "lab" in q:
                ass_type = "Lab"
            elif "oral" in q:
                ass_type = "Oral"
            pref = None
            if "computer lab" in q or "lab" in q:
                pref = "Lab"
            elif "moot" in q:
                pref = "Moot"
            mode = "strict"
            if "adaptive" in q or "flexible" in q or "reshuffle" in q:
                mode = "adaptive"

            # Use memory to inform response
            pref_room = self.engine.memory.get_preferred_room(unit_code)
            if pref_room:
                pref_msg = f" Historically, this unit prefers {pref_room}."
            else:
                pref_msg = ""

            if student_count > 500:
                return (f"{unit_code} with {student_count} students is large. "
                        f"I recommend adaptive mode to reshuffle existing exams.{pref_msg} "
                        f"Would you like to proceed with adaptive? (reply 'yes adaptive')")

            proposal = self.engine.propose_new_assessment(unit_code, student_count, ass_type, pref, mode)
            if proposal:
                self.engine.pending_decisions.append(proposal)
                changes = proposal.get('changes', 0)
                # Safely access proposed_slot; if missing, use "unknown"
                proposed_slot = proposal.get('proposed_slot', 'unknown slot')
                congestion = self.engine.memory.get_congestion_level(proposed_slot) if proposed_slot != 'unknown slot' else 0
                proposed_room = proposal.get('proposed_room', 'unknown room')
                base_msg = (f"I've created a proposal for {unit_code} with {student_count} students: "
                            f"schedule in {proposed_room} at {proposed_slot}. ")
                if changes > 0:
                    base_msg += f"This will move {changes} existing exams. "
                if congestion > 0:
                    base_msg += f"Note: this slot historically has {congestion} exams. "
                if pref_room and pref_room == proposed_room:
                    base_msg += "This matches your historical preference. "
                base_msg += "You can review and approve in Pending Decisions."
                return base_msg
            else:
                return f"Sorry, I couldn't find a feasible placement for {unit_code} with {student_count} students."

        # Follow-up for adaptive confirmation
        if q in ["yes adaptive", "adaptive yes", "yes"]:
            return "Please repeat your scheduling request with the unit code and student count, including 'adaptive'."

        # Greetings
        if re.search(r'\b(hi|hello|hey)\b', q):
            return ("Hello, Registrar. I'm Nexus AI. I can schedule exams, predict clashes, give risk assessments, "
                    "and I learn from past schedules. How can I help?")

        # Pending count
        if 'pending' in q and ('decision' in q or 'approval' in q):
            count = len(self.engine.get_pending_decisions())
            return f"There are currently {count} pending decisions awaiting your approval."

        # Clash probability for a unit
        unit_match = re.search(r'(unit|course)\s*([a-zA-Z0-9]+)', q)
        if unit_match and ('clash' in q or 'probability' in q):
            unit_code = unit_match.group(2).upper()
            slots = ["Slot1", "Slot2", "Slot3"]
            best_prob = 0
            best_slot = None
            for s in slots:
                prob = self.analytics.predict_clash_probability(unit_code, s)
                if prob > best_prob:
                    best_prob = prob
                    best_slot = s
            if best_slot:
                congestion = self.engine.memory.get_congestion_level(best_slot)
                return (f"Unit {unit_code} has highest clash probability of {best_prob:.1%} in {best_slot}. "
                        f"Historically, that slot has {congestion} exams.")
            else:
                return f"Unit {unit_code} not found in historical data."

        # Student risk
        student_match = re.search(r'student\s*([a-zA-Z0-9]+)', q)
        if student_match and ('risk' in q):
            student_id = student_match.group(1)
            risk = self.analytics.predict_student_risk(student_id)
            return f"Student {student_id} has a risk index of {risk:.1%}."

        # Hotspots
        if 'hotspot' in q or 'stress' in q or 'problem' in q:
            hotspots = self.analytics.get_hotspots(3)
            if hotspots:
                msg = "Top potential clash hotspots (based on history):\n"
                for h in hotspots:
                    congestion = self.engine.memory.get_congestion_level(h['slot'])
                    msg += f"- {h['unit']} in {h['slot']}: {h['probability']:.1%} probability (historically {congestion} exams)\n"
                return msg
            else:
                return "No hotspots identified."

        # Help
        if 'help' in q or 'what can you do' in q:
            return ("I can answer questions about pending decisions, clash probabilities, student risk, and exam hotspots. "
                    "I can also schedule new assessments: try 'schedule BIT101 with 45 students' or "
                    "'schedule BIT101 with 300 students adaptive' to allow reshuffling. "
                    "I learn from past schedules, so I can suggest historically preferred rooms and avoid congested slots.")

        # Fallback to Gemini
        try:
            gemini_response = self.gemini.model.generate_content(
                f"You are an exam governance assistant. Answer briefly: {query}"
            )
            return gemini_response.text
        except:
            return "I'm sorry, I didn't understand that. Type 'help' to see what I can do."