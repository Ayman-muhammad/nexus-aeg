"""
Main orchestrator – Nexus Engine.
Integrates memory, scheduler, ledger, notifier, gemini, and analytics.
"""
from typing import List, Optional, Dict
import logging

from .models import Assessment, Building, Unit
from .scheduler import ORToolsScheduler
from .memory import FirestoreMemory
from .ledger import AuditLedger
from .notifier import Notifier
from .gemini import GeminiReasoner
from .analytics import AnalyticsEngine
from utils.firebase_init import init_firebase

logger = logging.getLogger(__name__)

class NexusEngine:
    def __init__(self, university_id: str):
        self.university_id = university_id

        # ✅ Proper tuple unpacking
        self.db, _ = init_firebase()  # self.db is Firestore client
        self.memory = FirestoreMemory(university_id, self.db)
        self.ledger = AuditLedger(university_id, self.db)
        self.notifier = Notifier()
        self.reasoner = GeminiReasoner()

        self.assessments: List[Assessment] = []
        self.buildings: List[Building] = []
        self.units: List[Unit] = []
        self.pending_decisions: List[Dict] = []
        self.live_mode = False

        # Analytics engine will be initialised after data is loaded
        self.analytics: Optional[AnalyticsEngine] = None

    def load_data(self, buildings: List[Building], units: List[Unit],
                  assessments: List[Assessment]):
        """Load domain entities into engine."""
        self.buildings = buildings
        self.units = units
        self.assessments = assessments
        # Load room capacities from memory (if any override)
        for b in buildings:
            cap = self.memory.get_room_capacity(b.code)
            if cap is not None:
                b.capacity = cap
        # Initialise analytics with current data
        self.analytics = AnalyticsEngine(self.university_id, self.memory, self.buildings, self.assessments)
        logger.info(f"Loaded {len(assessments)} assessments, {len(buildings)} buildings.")

    def detect_conflicts(self) -> List[Dict]:
        """Use scheduler to find conflicts and generate alternatives."""
        scheduler = ORToolsScheduler(self.assessments, self.buildings)
        conflicts = scheduler.find_conflicts()
        # Extract unique assessment objects
        conflict_assessments = []
        for c in conflicts:
            for aid in c.get("assessment_ids", []):
                a = next((a for a in self.assessments if a.id == aid), None)
                if a and a not in conflict_assessments:
                    conflict_assessments.append(a)
        # Generate alternatives
        decisions = scheduler.generate_alternative_schedules(conflict_assessments)
        # Add Gemini reasoning
        for dec in decisions:
            for opt in dec["options"]:
                opt["reasoning"] = self.reasoner.explain_choice(dec["unit"], opt)
        self.pending_decisions = decisions
        return conflicts

    def registrar_authorize(self, decision_index: int, option_index: int) -> str:
        """Apply a selected option and record in ledger/memory."""
        if decision_index >= len(self.pending_decisions):
            raise IndexError("Decision index out of range")
        decision = self.pending_decisions[decision_index]
        if option_index >= len(decision["options"]):
            raise IndexError("Option index out of range")
        chosen = decision["options"][option_index]

        assessment = next(
            (a for a in self.assessments if a.id == decision["assessment_id"]),
            None
        )
        if not assessment:
            raise ValueError("Assessment not found")

        old_room = assessment.current_room
        old_slot = assessment.current_slot
        assessment.current_room = chosen["proposed_room"]
        assessment.current_slot = chosen["proposed_slot"]

        # Record in ledger
        self.ledger.record(
            assessment_id=assessment.id,
            action="registrar_approval",
            old_value={"room": old_room, "slot": old_slot},
            new_value={"room": chosen["proposed_room"], "slot": chosen["proposed_slot"]},
            actor="registrar"
        )

        # Learn
        self.memory.update_unit_preference(assessment.unit_code, chosen["proposed_room"])
        self.memory.increment_slot_congestion(chosen["proposed_slot"])

        # Remove from pending
        self.pending_decisions.pop(decision_index)
        return f"Approved: {assessment.unit_code} moved to {chosen['proposed_room']} at {chosen['proposed_slot']}"

    def auto_resolve(self, alert: dict) -> bool:
        """Called by monitor to automatically resolve an anomaly."""
        scheduler = ORToolsScheduler(self.assessments, self.buildings)
        best = scheduler.find_best_relocation(alert["assessment_id"])
        if not best:
            logger.warning(f"No feasible relocation for alert {alert}")
            return False

        assessment = next(
            (a for a in self.assessments if a.id == alert["assessment_id"]),
            None
        )
        if not assessment:
            return False

        old_room = assessment.current_room
        old_slot = assessment.current_slot
        assessment.current_room = best["proposed_room"]
        assessment.current_slot = best["proposed_slot"]

        # Record in ledger
        self.ledger.record(
            assessment_id=assessment.id,
            action="auto_resolve",
            old_value={"room": old_room, "slot": old_slot},
            new_value={"room": best["proposed_room"], "slot": best["proposed_slot"]},
            auto=True
        )

        # Learn
        self.memory.update_unit_preference(assessment.unit_code, best["proposed_room"])
        self.memory.increment_slot_congestion(best["proposed_slot"])

        # Notify
        self.notifier.notify_students(assessment.id, "Exam room changed", best)

        logger.info(f"Auto‑resolved {assessment.id} to {best['proposed_room']}")
        return True

    def get_metrics(self) -> dict:
        """Return dashboard metrics."""
        total = len(self.assessments)
        pending = len(self.pending_decisions)
        if self.analytics:
            utilisation_report = self.analytics.utilisation_report()
            avg_utilisation = sum(utilisation_report.values()) / len(utilisation_report) if utilisation_report else 0
        else:
            avg_utilisation = 0
        return {
            "total_assessments": total,
            "pending_decisions": pending,
            "resolved_conflicts": total - pending,  # simplified
            "room_utilization": round(avg_utilisation, 1)
        }

    def get_pending_decisions(self) -> List[Dict]:
        """Return pending decisions for UI."""
        return self.pending_decisions