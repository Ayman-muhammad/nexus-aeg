"""
Live anomaly detection monitor.
Runs in a background thread, checks for overcrowding, double‑booking,
and triggers auto‑resolution if live mode is enabled.
"""
import threading
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LiveMonitor:
    """
    Periodically scans assessments for anomalies.
    Call start() to begin monitoring in a daemon thread.
    """
    def __init__(self, engine, check_interval: int = 10):
        """
        Args:
            engine: Reference to the NexusEngine instance.
            check_interval: Seconds between scans.
        """
        self.engine = engine
        self.interval = check_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.alerts: List[Dict] = []  # recent alerts for UI

    def start(self):
        """Start the monitoring thread."""
        if self.running:
            logger.warning("Monitor already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("LiveMonitor started")

    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            logger.info("LiveMonitor stopped")

    def _monitor_loop(self):
        """Main loop – runs every `interval` seconds."""
        while self.running:
            try:
                self._check_anomalies()
            except Exception as e:
                logger.exception("Error in monitor loop")
            time.sleep(self.interval)

    def _check_anomalies(self):
        """Detect various anomalies and trigger resolution."""
        building_cap = {b.code: b.capacity for b in self.engine.buildings}
        slot_map: Dict[str, List] = {}
        for a in self.engine.assessments:
            if a.current_slot:
                slot_map.setdefault(a.current_slot, []).append(a)

        for slot, exams in slot_map.items():
            room_assignments = {}
            for exam in exams:
                # 1. Overcrowding
                capacity = building_cap.get(exam.current_room, 0)
                if exam.student_count > capacity:
                    alert = {
                        "type": "overcrowding",
                        "assessment_id": exam.id,
                        "unit": exam.unit_code,
                        "room": exam.current_room,
                        "students": exam.student_count,
                        "capacity": capacity,
                        "slot": slot,
                        "timestamp": time.time()
                    }
                    self.alerts.append(alert)
                    logger.info(f"Overcrowding detected: {exam.unit_code} in {exam.current_room}")
                    if self.engine.live_mode:
                        self._try_auto_resolve(alert)

                # 2. Double‑booking (same room at same slot)
                if exam.current_room in room_assignments:
                    # Only report once per pair
                    if exam.id > room_assignments[exam.current_room].id:
                        continue
                    alert = {
                        "type": "double_booking",
                        "assessment_ids": [room_assignments[exam.current_room].id, exam.id],
                        "room": exam.current_room,
                        "slot": slot,
                        "timestamp": time.time()
                    }
                    self.alerts.append(alert)
                    logger.info(f"Double‑booking detected in {exam.current_room} at {slot}")
                    if self.engine.live_mode:
                        # For double‑booking, we need to resolve both exams – simplified: just resolve one
                        self._try_auto_resolve(alert, exam.id)
                else:
                    room_assignments[exam.current_room] = exam

        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]

    def _try_auto_resolve(self, alert: Dict, specific_assessment_id: Optional[str] = None):
        """Ask engine to auto‑resolve an anomaly."""
        aid = specific_assessment_id or alert.get("assessment_id")
        if not aid:
            logger.error("No assessment_id in alert for auto‑resolve")
            return
        success = self.engine.auto_resolve({"assessment_id": aid})
        if success:
            self.alerts.append({
                "type": "auto_resolved",
                "assessment_id": aid,
                "timestamp": time.time()
            })

    def get_alerts(self) -> List[Dict]:
        """Return recent alerts for UI display."""
        return self.alerts