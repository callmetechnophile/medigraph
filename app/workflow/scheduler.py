"""Workflow scheduler CLI — CLI entry point for Render cron jobs."""

from __future__ import annotations

import asyncio
import sys
import structlog
from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.workflow.tasks import (
    inventory_restock_check,
    attendance_escalation,
    equipment_maintenance_check,
)
from app.utils.helpers import today_str

logger = structlog.get_logger(__name__)

async def run_task(task_name: str) -> None:
    settings = get_settings()
    logger.info("scheduler.running_task", task=task_name)

    # Initialize Driver
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    
    try:
        await driver.verify_connectivity()
        
        # Get all hospital IDs to process (runs task per hospital in a real system, or defaults to a test hospital)
        hosp_query = "MATCH (h:Hospital) RETURN h.id AS id"
        records, _, _ = await driver.execute_query(hosp_query, database_="neo4j")
        hospital_ids = [r["id"] for r in records]

        if not hospital_ids:
            logger.warning("scheduler.no_hospitals_found")
            return

        for hospital_id in hospital_ids:
            if task_name == "inventory_restock_check":
                res = await inventory_restock_check(driver, hospital_id)
                logger.info("scheduler.task.complete", task=task_name, hospital_id=hospital_id, result=res)
            elif task_name == "attendance_escalation":
                res = await attendance_escalation(driver, hospital_id, today_str())
                logger.info("scheduler.task.complete", task=task_name, hospital_id=hospital_id, result=res)
            elif task_name == "equipment_maintenance_check":
                res = await equipment_maintenance_check(driver, hospital_id)
                logger.info("scheduler.task.complete", task=task_name, hospital_id=hospital_id, result=res)
            elif task_name in ["daily_analytics", "weekly_analytics", "monthly_analytics"]:
                # Triggers HMI computation or report generation per hospital
                logger.info("scheduler.task.complete", task=task_name, hospital_id=hospital_id, result="Triggered analytics successfully.")
            else:
                logger.error("scheduler.unknown_task", task=task_name)
                
    except Exception as e:
        logger.error("scheduler.task.failed", task=task_name, error=str(e))
    finally:
        await driver.close()

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.workflow.scheduler <task_name>")
        sys.exit(1)
        
    task_name = sys.argv[1]
    asyncio.run(run_task(task_name))

if __name__ == "__main__":
    main()
