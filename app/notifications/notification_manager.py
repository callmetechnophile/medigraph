"""Notification manager — Centralised creation helpers for alerts."""

from __future__ import annotations

from typing import Any
from app.models import Notification, NotificationPriority, NotificationSource

class NotificationManager:
    def create_inventory_alert(self, hospital_id: str, item_name: str, current_stock: int, reorder_level: int) -> dict[str, Any]:
        return {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"Low Stock Alert: {item_name}",
            "message": f"Medicine {item_name} has dropped to {current_stock} (Reorder level: {reorder_level}).",
            "priority": NotificationPriority.WARNING.value,
            "source": NotificationSource.INVENTORY.value,
            "metadata": {
                "medicine_name": item_name,
                "current_stock": current_stock,
                "reorder_level": reorder_level
            }
        }

    def create_attendance_alert(self, hospital_id: str, staff_name: str, date: str, status: str) -> dict[str, Any]:
        return {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"Staff Absence Alert: {staff_name}",
            "message": f"Staff {staff_name} is reported {status} on {date}.",
            "priority": NotificationPriority.WARNING.value,
            "source": NotificationSource.ATTENDANCE.value,
            "metadata": {
                "staff_name": staff_name,
                "date": date,
                "status": status
            }
        }

    def create_equipment_alert(self, hospital_id: str, equipment_name: str, status: str) -> dict[str, Any]:
        return {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"Equipment Status Alteration: {equipment_name}",
            "message": f"Device {equipment_name} changed operational status to {status}.",
            "priority": NotificationPriority.CRITICAL.value if status == "out_of_order" else NotificationPriority.INFORMATION.value,
            "source": NotificationSource.DIAGNOSTICS.value,
            "metadata": {
                "equipment_name": equipment_name,
                "status": status
            }
        }

    def create_ai_recommendation_alert(self, hospital_id: str, recommendation_title: str, priority: str) -> dict[str, Any]:
        return {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"New AI Suggestion: {recommendation_title}",
            "message": f"AI Engine has generated a {priority} recommendation: {recommendation_title}.",
            "priority": NotificationPriority.INFORMATION.value,
            "source": NotificationSource.AI.value,
            "metadata": {
                "recommendation_title": recommendation_title,
                "priority": priority
            }
        }

    def create_system_notification(self, recipient_id: str, title: str, message: str) -> dict[str, Any]:
        return {
            "recipient_id": recipient_id,
            "recipient_type": "user",
            "title": title,
            "message": message,
            "priority": NotificationPriority.INFORMATION.value,
            "source": NotificationSource.SYSTEM.value,
            "metadata": {}
        }
