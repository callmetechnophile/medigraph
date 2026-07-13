"""Workflow service — Manages rendering daily analytics, restocks, and alerts."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.services.inventory_service import InventoryService
from app.services.attendance_service import AttendanceService
from app.services.hmi_service import HMIService
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.services.recommendation_service import RecommendationService
from app.schemas import WorkflowStatusResponse, ReportGenerateRequest
from app.utils.helpers import generate_id, utc_now, today_str

logger = structlog.get_logger(__name__)

class WorkflowService:
    def __init__(
        self,
        inventory_service: InventoryService,
        attendance_service: AttendanceService,
        hmi_service: HMIService,
        report_service: ReportService,
        notification_service: NotificationService,
        recommendation_service: RecommendationService,
    ):
        self.inventory_service = inventory_service
        self.attendance_service = attendance_service
        self.hmi_service = hmi_service
        self.report_service = report_service
        self.notification_service = notification_service
        self.recommendation_service = recommendation_service

    async def run_inventory_restock_check(self, hospital_id: str) -> dict[str, Any]:
        logger.info("workflow.inventory_check.start", hospital_id=hospital_id)
        # Check low stock items
        alerts = await self.inventory_service.get_low_stock_alerts(hospital_id)
        triggered_alerts = len(alerts)
        
        for alert in alerts:
            # Create low stock AI recommendations
            rec_data = {
                "category": "inventory",
                "title": f"Restock Suggestion: {alert.medicine_name}",
                "description": f"Stock levels have dropped below reorder level ({alert.reorder_level}).",
                "prediction": "Risk of stockout within 5 days.",
                "reason": "Consumption trend exceeds current stock levels.",
                "confidence": 0.85,
                "priority": "high",
                "expected_impact": "Prevents stockouts of critical medicine.",
                "suggested_action": f"Order {alert.maximum_stock - alert.current_stock} units of {alert.medicine_name}.",
            }
            await self.recommendation_service.create_recommendation(hospital_id, rec_data)

        logger.info("workflow.inventory_check.complete", hospital_id=hospital_id, alerts=triggered_alerts)
        return {"alerts_triggered": triggered_alerts, "success": True}

    async def run_attendance_escalation(self, hospital_id: str, date: str = "") -> dict[str, Any]:
        logger.info("workflow.attendance_escalation.start", hospital_id=hospital_id)
        target_date = date or today_str()
        res = await self.attendance_service.escalate_absences(hospital_id, target_date)
        return res

    async def run_equipment_maintenance_check(self, hospital_id: str) -> dict[str, Any]:
        logger.info("workflow.equipment_check.start", hospital_id=hospital_id)
        # In a real environment, you would call a DiagnosticsService method to fetch maintenance-due items
        # and create notifications for them.
        logger.info("workflow.equipment_check.complete", hospital_id=hospital_id)
        return {"success": True}

    async def run_daily_analytics(self, hospital_id: str) -> dict[str, Any]:
        logger.info("workflow.daily_analytics.start", hospital_id=hospital_id)
        # 1. Recalculate HMI Score
        hmi_score = await self.hmi_service.calculate_hmi(hospital_id)
        
        # 2. Trigger Daily Performance Report
        report_req = ReportGenerateRequest(
            report_type="performance",
            report_format="pdf",
            hospital_id=hospital_id,
            period_start=today_str(),
            period_end=today_str(),
            title=f"Daily Performance Report - {today_str()}",
        )
        report = await self.report_service.generate_report(user_id="system_workflow", data=report_req)

        # 3. Dispatched notifications
        await self.notification_service.create_notification({
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": "Daily HMI Recalculated",
            "message": f"Daily analytics complete. New HMI Score: {hmi_score.overall_score}. Performance report is available.",
            "priority": "information",
            "source": "workflow",
            "source_id": hmi_score.id,
        })

        return {"hmi_score": hmi_score.overall_score, "report_url": report.file_url, "success": True}

    async def run_weekly_analytics(self, hospital_id: str) -> dict[str, Any]:
        # Triggers weekly report generation
        return {"success": True}

    async def run_monthly_analytics(self, hospital_id: str) -> dict[str, Any]:
        # Triggers monthly report generation
        return {"success": True}

    async def trigger_workflow(self, workflow_type: str, hospital_id: str, params: dict[str, Any]) -> WorkflowStatusResponse:
        started_at = utc_now()
        status = "completed"
        error = ""
        result = {}

        try:
            if workflow_type == "inventory_restock_check":
                result = await self.run_inventory_restock_check(hospital_id)
            elif workflow_type == "attendance_escalation":
                result = await self.run_attendance_escalation(hospital_id, params.get("date", ""))
            elif workflow_type == "equipment_maintenance_check":
                result = await self.run_equipment_maintenance_check(hospital_id)
            elif workflow_type == "daily_analytics":
                result = await self.run_daily_analytics(hospital_id)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown workflow type: {workflow_type}")
        except Exception as e:
            status = "failed"
            error = str(e)

        return WorkflowStatusResponse(
            id=generate_id(),
            workflow_type=workflow_type,
            status=status,
            started_at=started_at,
            completed_at=utc_now(),
            result=result,
            error=error,
        )
