"""Workflow tasks — Raw executions triggered by cron schedulers."""

from __future__ import annotations

import structlog
from neo4j import AsyncDriver

from app.utils.helpers import generate_id, utc_now, today_str

logger = structlog.get_logger(__name__)

async def inventory_restock_check(driver: AsyncDriver, hospital_id: str) -> dict[str, Any]:
    logger.info("workflow.task.inventory_check", hospital_id=hospital_id)
    # Fetch low stock inventory items directly
    query = (
        "MATCH (h:Hospital {id: $hospital_id})-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
        "WHERE i.current_stock <= i.reorder_level "
        "RETURN i.id AS id, m.name AS name, i.current_stock AS stock, i.reorder_level AS reorder"
    )
    records, _, _ = await driver.execute_query(query, hospital_id=hospital_id, database_="neo4j")
    
    count = 0
    for rec in records:
        # Create notification
        n_id = generate_id()
        notif_query = (
            "CREATE (n:Notification { "
            "  id: $id, recipient_id: $hospital_id, recipient_type: 'hospital', "
            "  title: $title, message: $message, priority: 'warning', "
            "  source: 'inventory', is_read: false, created_at: $now, updated_at: $now "
            "})"
        )
        await driver.execute_query(
            notif_query,
            id=n_id,
            hospital_id=hospital_id,
            title=f"Low Stock Alert: {rec['name']}",
            message=f"Medicine {rec['name']} is low: {rec['stock']} left (Reorder: {rec['reorder']})",
            now=utc_now(),
            database_="neo4j",
        )
        count += 1
        
    return {"alerts_sent": count}

async def attendance_escalation(driver: AsyncDriver, hospital_id: str, date: str) -> dict[str, Any]:
    logger.info("workflow.task.attendance_escalation", hospital_id=hospital_id, date=date)
    # Find absent doctors
    query = """
    MATCH (h:Hospital {id: $hospital_id})-[:HAS_DEPARTMENT]->(d:Department)-[:HAS_DOCTOR]->(doc:Doctor)
    WHERE NOT EXISTS {
        MATCH (doc)<-[:HAS_STAFF_ATTENDANCE]-(a:Attendance {date: $date, hospital_id: $hospital_id})
    }
    RETURN doc.id AS doc_id, doc.name AS name, d.name AS dept
    """
    records, _, _ = await driver.execute_query(query, hospital_id=hospital_id, date=date, database_="neo4j")
    
    count = 0
    for rec in records:
        n_id = generate_id()
        notif_query = (
            "CREATE (n:Notification { "
            "  id: $id, recipient_id: $hospital_id, recipient_type: 'hospital', "
            "  title: $title, message: $message, priority: 'warning', "
            "  source: 'attendance', is_read: false, created_at: $now, updated_at: $now "
            "})"
        )
        await driver.execute_query(
            notif_query,
            id=n_id,
            hospital_id=hospital_id,
            title=f"Absence Escalation: {rec['name']}",
            message=f"Doctor {rec['name']} ({rec['dept']}) has not checked in today.",
            now=utc_now(),
            database_="neo4j",
        )
        count += 1
        
    return {"escalations_sent": count}

async def equipment_maintenance_check(driver: AsyncDriver, hospital_id: str) -> dict[str, Any]:
    logger.info("workflow.task.equipment_check", hospital_id=hospital_id)
    # Check equipment next maintenance date
    query = (
        "MATCH (e:DiagnosticEquipment {hospital_id: $hospital_id}) "
        "WHERE e.next_maintenance_date IS NOT NULL AND date(e.next_maintenance_date) <= date() "
        "RETURN e.id AS id, e.name AS name, e.next_maintenance_date AS due"
    )
    records, _, _ = await driver.execute_query(query, hospital_id=hospital_id, database_="neo4j")
    
    count = 0
    for rec in records:
        n_id = generate_id()
        notif_query = (
            "CREATE (n:Notification { "
            "  id: $id, recipient_id: $hospital_id, recipient_type: 'hospital', "
            "  title: $title, message: $message, priority: 'warning', "
            "  source: 'diagnostics', is_read: false, created_at: $now, updated_at: $now "
            "})"
        )
        await driver.execute_query(
            notif_query,
            id=n_id,
            hospital_id=hospital_id,
            title=f"Maintenance Due: {rec['name']}",
            message=f"Equipment {rec['name']} is overdue for maintenance since {rec['due']}.",
            now=utc_now(),
            database_="neo4j",
        )
        count += 1
        
    return {"maintenance_alerts": count}

async def process_alerts(driver: AsyncDriver, hospital_id: str) -> dict[str, Any]:
    # Placeholder for arbitrary alert calculations
    return {"processed": True}
