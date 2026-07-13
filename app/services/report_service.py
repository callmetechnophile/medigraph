"""Report service — Generates PDF/CSV/Excel and uploads to Supabase Storage."""

from __future__ import annotations

import io
import csv
import os
import uuid
from typing import Any
from fastapi import HTTPException
import structlog
import pandas as pd
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from supabase import create_client, Client

from app.repositories import ReportRepository
from app.schemas import (
    ReportGenerateRequest,
    ReportResponse,
    PaginatedResponse,
)
from app.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        supabase_url: str,
        supabase_key: str,
        supabase_bucket: str,
        temp_dir: str = "./tmp/reports",
    ):
        self.report_repo = report_repo
        self.supabase_bucket = supabase_bucket
        self.temp_dir = temp_dir
        
        # Init Supabase Client
        if supabase_url and supabase_key:
            self.supabase: Client | None = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            logger.warning("supabase.not_configured", message="Supabase credentials missing. Reports will not be stored.")

        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    async def generate_report(self, user_id: str, data: ReportGenerateRequest) -> ReportResponse:
        # 1. Gather mock data or query Neo4j database (for simplicity, we create descriptive mock tables based on report type)
        columns, rows = self._get_mock_report_data(data.report_type)

        # 2. Build report file bytes
        filename = f"{data.report_type.value}_report_{uuid.uuid4().hex[:8]}"
        content_type = ""
        file_bytes = b""

        if data.report_format.value == "pdf":
            file_bytes = self._generate_pdf(data.title or f"{data.report_type.value.capitalize()} Report", columns, rows)
            filename += ".pdf"
            content_type = "application/pdf"
        elif data.report_format.value == "csv":
            file_bytes = self._generate_csv(columns, rows)
            filename += ".csv"
            content_type = "text/csv"
        elif data.report_format.value == "excel":
            file_bytes = self._generate_excel(data.title or "Report", columns, rows)
            filename += ".xlsx"
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # 3. Upload to Supabase Storage
        file_url = ""
        if self.supabase:
            try:
                # Upload binary data
                res = self.supabase.storage.from_(self.supabase_bucket).upload(
                    path=filename,
                    file=file_bytes,
                    file_options={"content-type": content_type}
                )
                # Get public URL
                file_url = self.supabase.storage.from_(self.supabase_bucket).get_public_url(filename)
            except Exception as e:
                logger.error("supabase.upload_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to upload report to storage: {str(e)}")
        else:
            # Fallback to saving locally
            local_path = os.path.join(self.temp_dir, filename)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            file_url = f"file://{os.path.abspath(local_path)}"

        # 4. Save metadata in Neo4j
        report_meta = {
            "id": generate_id(),
            "hospital_id": data.hospital_id,
            "district_id": data.district_id,
            "report_type": data.report_type.value,
            "report_format": data.report_format.value,
            "title": data.title or f"{data.report_type.value.capitalize()} Report",
            "description": f"Generated {data.report_type.value} report in {data.report_format.value} format.",
            "file_url": file_url,
            "file_size_bytes": len(file_bytes),
            "generated_by": user_id,
            "period_start": data.period_start,
            "period_end": data.period_end,
            "parameters": data.parameters,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }

        res = await self.report_repo.create_for_hospital(data.hospital_id or "district_report", report_meta)
        return ReportResponse(**res)

    def _generate_pdf(self, title: str, columns: list[str], rows: list[list[Any]]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Define styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=20,
        )
        
        story = []
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Generated at: {utc_now()}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Prep Table Data
        table_data = [columns] + rows
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#EDF2F7")]),
        ]))
        
        story.append(t)
        doc.build(story)
        return buffer.getvalue()

    def _generate_csv(self, columns: list[str], rows: list[list[Any]]) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        return output.getvalue().encode("utf-8")

    def _generate_excel(self, title: str, columns: list[str], rows: list[list[Any]]) -> bytes:
        buffer = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = title[:30]

        # Add columns
        ws.append(columns)
        for r in rows:
            ws.append(r)

        wb.save(buffer)
        return buffer.getvalue()

    async def list_reports(self, hospital_id: str, skip: int = 0, limit: int = 20, report_type: str = "") -> PaginatedResponse[ReportResponse]:
        items, total = await self.report_repo.get_by_hospital(hospital_id, skip=skip, limit=limit, report_type_filter=report_type)
        return PaginatedResponse(
            items=[ReportResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_report(self, report_id: str) -> ReportResponse:
        res = await self.report_repo.find_by_id(report_id)
        if not res:
            raise HTTPException(status_code=404, detail="Report not found.")
        return ReportResponse(**res)

    def _get_mock_report_data(self, report_type: Any) -> tuple[list[str], list[list[Any]]]:
        if report_type.value == "inventory":
            return (
                ["Medicine Name", "Category", "Current Stock", "Reorder Level", "Unit Cost ($)"],
                [
                    ["Paracetamol", "Analgesic", 150, 100, 0.50],
                    ["Amoxicillin", "Antibiotic", 45, 50, 1.20],
                    ["Metformin", "Antidiabetic", 200, 80, 0.75],
                    ["Atorvastatin", "Statins", 120, 60, 2.10],
                    ["Ibuprofen", "NSAID", 80, 100, 0.40],
                ]
            )
        elif report_type.value == "attendance":
            return (
                ["Staff ID", "Department", "Days Present", "Days Absent", "Late Check-ins", "Attendance Rate (%)"],
                [
                    ["doc-01", "Cardiology", 20, 1, 2, 95.2],
                    ["doc-02", "Pediatrics", 22, 0, 0, 100.0],
                    ["staff-01", "Nursing", 18, 4, 5, 81.8],
                    ["staff-02", "Emergency", 21, 1, 1, 95.4],
                ]
            )
        # Default fallback
        return (
            ["Metric", "Value", "Target", "Status"],
            [
                ["Bed Occupancy Rate (%)", 78.4, 80.0, "Optimal"],
                ["Average ER Wait Time (min)", 24, 15, "Attention Required"],
                ["Ambulance Readiness (%)", 100.0, 90.0, "Excellent"],
                ["Operational Compliance Score", 92.5, 90.0, "Excellent"],
            ]
        )
