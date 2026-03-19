"""
Immutable audit ledger using Firestore.
Each entry is hashed with SHA‑256 to ensure integrity.
"""
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)

class AuditLedger:
    def __init__(self, university_id: str, db: firestore.Client):
        """
        Args:
            university_id: Unique identifier for the university.
            db: Firestore client instance (from firebase_admin.firestore.client()).
        """
        self.db = db
        self.university_id = university_id
        self.collection = self.db.collection("universities").document(university_id).collection("audit")

    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA‑256 hash of the data (sorted keys for consistency)."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def record(self, assessment_id: str, action: str, old_value: Dict, new_value: Dict,
               actor: Optional[str] = None, auto: bool = False) -> str:
        """
        Record an action in the ledger.
        Returns the document ID.
        """
        entry = {
            "timestamp": firestore.SERVER_TIMESTAMP,
            "assessment_id": assessment_id,
            "action": action,
            "old_value": old_value,
            "new_value": new_value,
            "actor": actor or "system",
            "auto": auto
        }
        # Compute hash of the entry (excluding timestamp which is server-side)
        hash_data = {k: v for k, v in entry.items() if k != "timestamp"}
        entry["hash"] = self._compute_hash(hash_data)

        # Add previous hash for chain (if any)
        last_entry = self.get_last_entry()
        if last_entry:
            entry["previous_hash"] = last_entry.get("hash")
        else:
            entry["previous_hash"] = None

        # Store
        doc_ref = self.collection.document()
        doc_ref.set(entry)
        logger.info(f"Ledger entry created: {doc_ref.id} for assessment {assessment_id}")
        return doc_ref.id

    def get_last_entry(self) -> Optional[Dict]:
        """Retrieve the most recent ledger entry."""
        docs = self.collection.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
        for doc in docs:
            return doc.to_dict()
        return None

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the entire ledger.
        Returns True if all hashes match.
        """
        entries = list(self.collection.order_by("timestamp").stream())
        if not entries:
            return True
        prev_hash = None
        for entry in entries:
            data = entry.to_dict()
            # Recompute hash (exclude timestamp and previous_hash)
            hash_data = {k: v for k, v in data.items() if k not in ("timestamp", "previous_hash")}
            computed = self._compute_hash(hash_data)
            if computed != data.get("hash"):
                logger.error(f"Hash mismatch in entry {entry.id}")
                return False
            if data.get("previous_hash") != prev_hash:
                logger.error(f"Chain broken at entry {entry.id}")
                return False
            prev_hash = data.get("hash")
        return True