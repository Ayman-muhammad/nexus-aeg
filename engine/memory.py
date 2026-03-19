"""
Firestore-based persistent memory for learning.
All data is partitioned by university_id.
Uses the Firebase‑managed Firestore client.
"""
from google.cloud import firestore
from typing import List, Dict, Optional, Any
import logging
from .models import Building, Unit, Assessment

logger = logging.getLogger(__name__)

class FirestoreMemory:
    def __init__(self, university_id: str, db):
        """
        Args:
            university_id: Unique identifier for the university (from Firebase UID).
            db: Firestore client instance (from firebase_admin.firestore.client()).
        """
        self.db = db
        self.university_id = university_id
        self._root_ref = self.db.collection("universities").document(university_id)

    def _col(self, collection_name: str):
        """Helper to get a subcollection reference."""
        return self._root_ref.collection(collection_name)

    # ----- Unit preferences (room popularity) -----
    def get_unit_preferences(self, unit_code: str) -> Dict[str, int]:
        """Return dict {room_code: count} for this unit."""
        doc = self._col("unit_preferences").document(unit_code).get()
        return doc.to_dict() if doc.exists else {}

    def update_unit_preference(self, unit_code: str, room_code: str):
        """Increment count for this unit+room."""
        ref = self._col("unit_preferences").document(unit_code)
        ref.set({room_code: firestore.Increment(1)}, merge=True)
        logger.debug(f"Updated preference for {unit_code} -> {room_code}")

    # ----- Slot congestion -----
    def get_slot_congestion(self, slot: str) -> int:
        doc = self._col("slot_congestion").document(slot).get()
        return doc.to_dict().get("count", 0) if doc.exists else 0

    def increment_slot_congestion(self, slot: str):
        ref = self._col("slot_congestion").document(slot)
        ref.set({"count": firestore.Increment(1)}, merge=True)

    # ----- Room capacities (override if needed) -----
    def set_room_capacity(self, room_code: str, capacity: int):
        self._col("room_capacities").document(room_code).set({"capacity": capacity})

    def get_room_capacity(self, room_code: str) -> Optional[int]:
        doc = self._col("room_capacities").document(room_code).get()
        return doc.to_dict().get("capacity") if doc.exists else None

    # ----- Invigilator assignments (for workload balancing) -----
    def record_invigilator_assignment(self, staff_id: str, slot: str):
        ref = self._col("invigilator_assignments").document(staff_id)
        ref.set({slot: firestore.Increment(1)}, merge=True)

    def get_invigilator_load(self, staff_id: str, slot: str) -> int:
        doc = self._col("invigilator_assignments").document(staff_id).get()
        return doc.to_dict().get(slot, 0) if doc.exists else 0

    # ----- General key‑value store for any other stats -----
    def set_stat(self, key: str, value: Any):
        self._col("stats").document(key).set({"value": value})

    def get_stat(self, key: str) -> Any:
        doc = self._col("stats").document(key).get()
        return doc.to_dict().get("value") if doc.exists else None

    # ----- Persistent storage for core data -----
    def save_buildings(self, buildings: List[Building]):
        """Store buildings in Firestore (overwrites existing)."""
        batch = self.db.batch()
        for b in buildings:
            doc_ref = self._col("buildings").document(b.code)
            batch.set(doc_ref, b.dict())
        batch.commit()
        logger.info(f"Saved {len(buildings)} buildings.")

    def get_buildings(self) -> List[Building]:
        """Retrieve all buildings for this university."""
        docs = self._col("buildings").stream()
        return [Building(**doc.to_dict()) for doc in docs]

    def save_units(self, units: List[Unit]):
        batch = self.db.batch()
        for u in units:
            doc_ref = self._col("units").document(u.code)
            batch.set(doc_ref, u.dict())
        batch.commit()
        logger.info(f"Saved {len(units)} units.")

    def get_units(self) -> List[Unit]:
        docs = self._col("units").stream()
        return [Unit(**doc.to_dict()) for doc in docs]

    def save_assessments(self, assessments: List[Assessment]):
        batch = self.db.batch()
        for a in assessments:
            doc_ref = self._col("assessments").document(a.id)
            batch.set(doc_ref, a.dict())
        batch.commit()
        logger.info(f"Saved {len(assessments)} assessments.")

    def get_assessments(self) -> List[Assessment]:
        docs = self._col("assessments").stream()
        return [Assessment(**doc.to_dict()) for doc in docs]