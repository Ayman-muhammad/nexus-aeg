"""
OR‑Tools based scheduler with hard and soft constraints.
Generates feasible alternatives and scores them.
"""
from typing import List, Dict, Optional, Tuple
from ortools.sat.python import cp_model
from .models import Assessment, Building, ConflictSolution
import logging

logger = logging.getLogger(__name__)

class ORToolsScheduler:
    def __init__(self, assessments: List[Assessment], buildings: List[Building]):
        self.assessments = assessments
        self.buildings = buildings
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

    def find_conflicts(self) -> List[Dict]:
        """
        Detect existing conflicts in the current schedule.
        Returns list of conflict dictionaries.
        """
        conflicts = []
        # Group by slot
        slot_map = {}
        for a in self.assessments:
            if not a.current_slot:
                continue
            slot_map.setdefault(a.current_slot, []).append(a)

        for slot, exams in slot_map.items():
            room_assignments = {}
            for exam in exams:
                if not exam.current_room:
                    continue
                if exam.current_room in room_assignments:
                    conflicts.append({
                        "type": "double_booking",
                        "slot": slot,
                        "room": exam.current_room,
                        "assessment_ids": [room_assignments[exam.current_room].id, exam.id]
                    })
                else:
                    room_assignments[exam.current_room] = exam
        return conflicts

    def generate_alternative_schedules(self, conflicting_assessments: List[Assessment]) -> List[Dict]:
        """
        For each conflicting assessment, generate multiple feasible alternatives.
        Returns list of decision objects each with multiple options.
        """
        decisions = []
        for assessment in conflicting_assessments:
            options = self._find_feasible_rooms_and_slots(assessment)
            if options:
                decisions.append({
                    "assessment_id": assessment.id,
                    "unit": assessment.unit_code,
                    "options": options
                })
        return decisions

    def _find_feasible_rooms_and_slots(self, assessment: Assessment) -> List[Dict]:
        """Return up to 3 feasible (room, slot) pairs with scores."""
        feasible = []
        # Use a few default slots for demo; in production, slots would come from a calendar.
        slots = ["2025-05-10 09:00", "2025-05-10 14:00", "2025-05-11 09:00"]
        for building in self.buildings:
            if building.capacity < assessment.student_count:
                continue
            for slot in slots:
                # Check if room is already occupied at that slot
                occupied = any(
                    a.current_slot == slot and a.current_room == building.code
                    for a in self.assessments if a.id != assessment.id
                )
                if not occupied:
                    score = self._score_option(assessment, building.code, slot)
                    feasible.append({
                        "proposed_room": building.code,
                        "proposed_slot": slot,
                        "score": score
                    })
        # Sort by score descending and return top 3
        feasible.sort(key=lambda x: x["score"], reverse=True)
        return feasible[:3]

    def _score_option(self, assessment: Assessment, room: str, slot: str) -> float:
        """
        Compute a score based on capacity fit, historical preferences,
        and slot congestion (would use FirestoreMemory in real system).
        For demo, returns a random score.
        """
        import random
        return random.uniform(0.5, 1.0)

    def find_best_relocation(self, assessment_id: str) -> Optional[Dict]:
        """
        Used by auto‑resolve: find the single best alternative.
        """
        assessment = next((a for a in self.assessments if a.id == assessment_id), None)
        if not assessment:
            return None
        options = self._find_feasible_rooms_and_slots(assessment)
        if options:
            return options[0]  # highest score
        return None