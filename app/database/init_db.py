"""Neo4j schema initialisation — constraints, indexes, and seed data."""

from __future__ import annotations

import structlog
from neo4j import AsyncDriver

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Uniqueness constraints
# ---------------------------------------------------------------------------
_UNIQUENESS_CONSTRAINTS: list[tuple[str, str, str]] = [
    # (constraint_name, label, property)
    ("patient_id_unique", "Patient", "id"),
    ("hospital_id_unique", "Hospital", "id"),
    ("department_id_unique", "Department", "id"),
    ("doctor_id_unique", "Doctor", "id"),
    ("medicine_id_unique", "Medicine", "id"),
    ("inventory_id_unique", "Inventory", "id"),
    ("attendance_id_unique", "Attendance", "id"),
    ("medical_record_id_unique", "MedicalRecord", "id"),
    ("prescription_id_unique", "Prescription", "id"),
    ("diagnosis_id_unique", "Diagnosis", "id"),
    ("laboratory_report_id_unique", "LaboratoryReport", "id"),
    ("imaging_report_id_unique", "ImagingReport", "id"),
    ("diagnostic_equipment_id_unique", "DiagnosticEquipment", "id"),
    ("ambulance_id_unique", "Ambulance", "id"),
    ("notification_id_unique", "Notification", "id"),
    ("recommendation_id_unique", "Recommendation", "id"),
    ("hmi_score_id_unique", "HMIScore", "id"),
    ("district_id_unique", "District", "id"),
    ("state_id_unique", "State", "id"),
    ("country_id_unique", "Country", "id"),
    ("report_id_unique", "Report", "id"),
]

# ---------------------------------------------------------------------------
# Composite / lookup indexes for performance
# ---------------------------------------------------------------------------
_INDEXES: list[tuple[str, str, list[str]]] = [
    ("patient_name_idx", "Patient", ["name"]),
    ("patient_phone_idx", "Patient", ["phone"]),
    ("hospital_name_idx", "Hospital", ["name"]),
    ("doctor_name_idx", "Doctor", ["name"]),
    ("medicine_name_idx", "Medicine", ["name"]),
    ("notification_read_idx", "Notification", ["is_read"]),
    ("notification_priority_idx", "Notification", ["priority"]),
    ("attendance_date_idx", "Attendance", ["date"]),
    ("hmi_score_date_idx", "HMIScore", ["calculated_at"]),
    ("ambulance_status_idx", "Ambulance", ["status"]),
    ("report_type_idx", "Report", ["report_type"]),
    ("recommendation_status_idx", "Recommendation", ["status"]),
]


async def init_constraints(driver: AsyncDriver, database: str = "neo4j") -> None:
    """Create uniqueness constraints if they do not already exist."""
    for name, label, prop in _UNIQUENESS_CONSTRAINTS:
        query = (
            f"CREATE CONSTRAINT {name} IF NOT EXISTS "
            f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        )
        try:
            await driver.execute_query(query, database_=database)
            logger.debug("constraint.created", name=name)
        except Exception as exc:
            logger.warning("constraint.error", name=name, error=str(exc))


async def init_indexes(driver: AsyncDriver, database: str = "neo4j") -> None:
    """Create lookup indexes if they do not already exist."""
    for name, label, props in _INDEXES:
        prop_list = ", ".join(f"n.{p}" for p in props)
        query = (
            f"CREATE INDEX {name} IF NOT EXISTS "
            f"FOR (n:{label}) ON ({prop_list})"
        )
        try:
            await driver.execute_query(query, database_=database)
            logger.debug("index.created", name=name)
        except Exception as exc:
            logger.warning("index.error", name=name, error=str(exc))


async def init_database(driver: AsyncDriver, database: str = "neo4j") -> None:
    """Run all schema initialisation steps."""
    logger.info("database.init.start")
    await init_constraints(driver, database)
    await init_indexes(driver, database)
    logger.info("database.init.complete")
