"""
Predictive analytics and reporting.
Computes clash probabilities, room utilisation, risk hotspots.
"""
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
import logging
from .models import Assessment, Building
from .memory import FirestoreMemory

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self, university_id: str, memory: FirestoreMemory, buildings: List[Building], assessments: List[Assessment]):
        self.university_id = university_id
        self.memory = memory
        self.buildings = buildings
        self.assessments = assessments

    def predict_clash_probability(self, unit_code: str, slot: str, room: str) -> float:
        """
        Estimate probability that this unit will experience a clash if placed at given slot/room.
        Uses historical data from memory.
        """
        slot_cong = self.memory.get_slot_congestion(slot)
        slot_factor = min(slot_cong / 100.0, 1.0)

        prefs = self.memory.get_unit_preferences(unit_code)
        total = sum(prefs.values())
        if total == 0:
            room_factor = 0.5
        else:
            room_popularity = prefs.get(room, 0) / total
            room_factor = room_popularity

        prob = 0.3 * slot_factor + 0.7 * room_factor
        return round(min(prob, 1.0), 2)

    def utilisation_report(self) -> Dict[str, float]:
        """Calculate room utilisation percentages."""
        room_slot_count = {}
        for a in self.assessments:
            if a.current_room and a.current_slot:
                key = (a.current_room, a.current_slot)
                room_slot_count[key] = room_slot_count.get(key, 0) + 1

        report = {}
        for b in self.buildings:
            total_slots = 20  # assume 20 exam slots per room (simplified)
            used_slots = sum(1 for (room, _) in room_slot_count if room == b.code)
            utilisation = (used_slots / total_slots) * 100 if total_slots > 0 else 0
            report[b.code] = round(utilisation, 1)
        return report

    def risk_hotspots(self) -> List[Dict]:
        """
        Identify rooms/times with high risk (overcrowding, frequent conflicts).
        Returns list of hotspots sorted by risk score.
        """
        hotspots = []
        for b in self.buildings:
            near_capacity = 0
            total = 0
            for a in self.assessments:
                if a.current_room == b.code:
                    total += 1
                    if a.student_count >= 0.9 * b.capacity:
                        near_capacity += 1
            if total > 0:
                risk = near_capacity / total
                hotspots.append({
                    "room": b.code,
                    "risk_score": round(risk, 2),
                    "near_capacity_count": near_capacity,
                    "total_assessments": total
                })
        hotspots.sort(key=lambda x: x["risk_score"], reverse=True)
        return hotspots

    def forecast_clash_hotspots(self, days_ahead: int = 7) -> List[Dict]:
        """
        Predict which rooms/times are likely to have clashes in the next `days_ahead`.
        Uses historical slot congestion from Firestore.
        """
        hotspots = []
        slots = set(a.current_slot for a in self.assessments if a.current_slot)
        for slot in slots:
            congestion = self.memory.get_slot_congestion(slot)
            forecast = congestion + 2 * days_ahead
            if forecast > 5:
                hotspots.append({
                    "slot": slot,
                    "predicted_congestion": forecast,
                    "risk_level": "high" if forecast > 10 else "medium"
                })
        return hotspots

    def utilization_trend(self) -> pd.DataFrame:
        """Return daily room utilization percentages for the last 7 days."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        data = []
        for date in dates:
            for b in self.buildings:
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "building": b.code,
                    "utilization": np.random.randint(30, 90)  # placeholder; in production, query historical data
                })
        return pd.DataFrame(data)