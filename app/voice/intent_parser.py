"""Intent parser — Regular expression engine for extracting speech commands."""

from __future__ import annotations

import re
from typing import Any

class IntentParser:
    def parse(self, transcript: str) -> dict[str, Any]:
        """Parse speech transcripts and return intent along with matched entities."""
        text = transcript.lower().strip()

        # 1. Update Stock: "update paracetamol stock to 120" / "set paracetamol to 120"
        m1 = re.search(r"(?:update|set|change)\s+([a-zA-Z0-9]+)\s+(?:stock\s+)?(?:to|=)\s*(\d+)", text)
        if m1:
            return {
                "intent": "update_stock",
                "entities": {"medicine": m1.group(1).capitalize(), "quantity": int(m1.group(2))},
                "confidence": 0.95
            }

        # 2. Check Stock: "check stock of paracetamol" / "how much paracetamol"
        m2 = re.search(r"(?:check\s+stock\s+of|how\s+much|get\s+stock\s+for)\s+([a-zA-Z0-9]+)", text)
        if m2:
            return {
                "intent": "check_stock",
                "entities": {"medicine": m2.group(1).capitalize()},
                "confidence": 0.90
            }

        # 3. Attendance: "mark john as present/absent"
        m3 = re.search(r"mark\s+([a-zA-Z0-9]+)\s+as\s+(present|absent|late|leave)", text)
        if m3:
            return {
                "intent": "mark_attendance",
                "entities": {"staff_name": m3.group(1), "status": m3.group(2)},
                "confidence": 0.90
            }

        # 4. Report: "generate operational report"
        m4 = re.search(r"(?:generate|show|get)\s+([a-zA-Z0-9]+)\s+report", text)
        if m4:
            return {
                "intent": "get_report",
                "entities": {"report_type": m4.group(1)},
                "confidence": 0.85
            }

        # 5. Ambulances: "how many ambulances available" / "ambulance status"
        if "ambulance" in text or "fleet" in text:
            return {
                "intent": "check_ambulance",
                "entities": {},
                "confidence": 0.80
            }

        # 6. HMI Score: "hospital score" / "performance score" / "hmi score"
        if "score" in text or "hmi" in text or "index" in text:
            return {
                "intent": "get_hmi",
                "entities": {},
                "confidence": 0.85
            }

        return {
            "intent": "unknown",
            "entities": {},
            "confidence": 0.0
        }
