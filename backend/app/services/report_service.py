import os
import io
import csv
from datetime import datetime
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.report import Report
from app.models.cost_record import CostRecord
from app.models.anomaly import Anomaly
from app.models.recommendation import Recommendation


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_reports(self, user_id: str) -> list[Report]:
        return (
            self.db.query(Report)
            .filter(Report.user_id == user_id)
            .order_by(Report.generated_at.desc())
            .all()
        )

    def generate_report(
        self, user_id: str, report_type: str, file_format: str
    ) -> Report:
        # Create a report entry in db
        filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"
        # Ensure static/reports directory exists
        static_dir = os.path.join("static", "reports")
        os.makedirs(static_dir, exist_ok=True)
        filepath = os.path.join(static_dir, filename)

        report = Report(
            user_id=user_id,
            report_type=report_type,
            format=file_format,
            filename=filename,
            s3_key=f"reports/{filename}",
            status="generating",
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        try:
            if file_format == "pdf":
                self._generate_pdf(user_id, report_type, filepath)
            elif file_format in ["xlsx", "excel"]:
                self._generate_excel(user_id, report_type, filepath)
            else:
                self._generate_csv(user_id, report_type, filepath)

            # Update size & status
            file_size = os.path.getsize(filepath)
            report.file_size = round(file_size / 1024.0, 1)  # size in KB
            report.status = "completed"
            self.db.commit()
        except Exception as e:
            report.status = "failed"
            self.db.commit()
            raise e

        return report

    def delete_report(self, user_id: str, report_id: str) -> None:
        report = (
            self.db.query(Report)
            .filter(Report.id == report_id, Report.user_id == user_id)
            .first()
        )
        if not report:
            return
        static_dir = os.path.join("static", "reports")
        filepath = os.path.join(static_dir, report.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        self.db.delete(report)
        self.db.commit()

    def _generate_csv(self, user_id: str, report_type: str, filepath: str):
        # Generate CSV representation
        records = (
            self.db.query(CostRecord)
            .filter(CostRecord.user_id == user_id)
            .order_by(CostRecord.date.desc())
            .limit(1000)
            .all()
        )
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Date",
                    "Service",
                    "Region",
                    "Amount ($)",
                    "Usage Quantity",
                    "Granularity",
                ]
            )
            for r in records:
                writer.writerow(
                    [
                        r.date,
                        r.service,
                        r.region,
                        r.amount,
                        r.usage_quantity,
                        r.granularity,
                    ]
                )

    def _generate_pdf(self, user_id: str, report_type: str, filepath: str):
        # Fetch data
        costs = (
            self.db.query(CostRecord)
            .filter(CostRecord.user_id == user_id)
            .order_by(CostRecord.date.desc())
            .all()
        )
        anomalies = (
            self.db.query(Anomaly)
            .join(CostRecord, Anomaly.cost_record_id == CostRecord.id)
            .filter(CostRecord.user_id == user_id)
            .all()
        )
        recommendations = (
            self.db.query(Recommendation)
            .filter(Recommendation.user_id == user_id)
            .all()
        )

        from app.services.budget_service import BudgetService

        budgets = BudgetService(self.db).get_budgets(user_id)

        total_spend = sum(c.amount for c in costs[:100])
        unresolved_anomalies = sum(1 for a in anomalies if not a.is_resolved)
        savings_opportunities = sum(
            r.monthly_savings for r in recommendations if r.status == "pending"
        )

        # Build PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.HexColor("#6366f1"),
            spaceAfter=15,
        )

        h2_style = ParagraphStyle(
            "ReportHeading2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=12,
            spaceAfter=8,
        )

        normal_style = styles["Normal"]

        # Header
        story.append(
            Paragraph(
                f"CloudWise FinOps Report - {report_type.replace('_', ' ').title()}",
                title_style,
            )
        )
        story.append(
            Paragraph(
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                normal_style,
            )
        )
        story.append(Spacer(1, 15))

        if report_type == "cost_summary" or report_type == "executive_summary":
            # Executive Summary Metrics Table
            story.append(Paragraph("Executive Summary", h2_style))
            summary_data = [
                ["Total MTD Spend", f"${total_spend:,.2f}"],
                ["Unresolved Anomalies", str(unresolved_anomalies)],
                [
                    "Pending Monthly Savings Opportunity",
                    f"${savings_opportunities:,.2f}",
                ],
            ]
            t = Table(summary_data, colWidths=[250, 250])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f4f6")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 15))

            # Service breakdown
            story.append(Paragraph("Service Spending Breakdown", h2_style))
            service_spend = {}
            for c in costs:
                service_spend[c.service] = service_spend.get(c.service, 0) + c.amount

            breakdown_data = [["Service", "Amount ($)"]]
            for svc, amt in sorted(
                service_spend.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                breakdown_data.append([svc, f"${amt:,.2f}"])

            t_breakdown = Table(breakdown_data, colWidths=[250, 250])
            t_breakdown.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(t_breakdown)

        elif report_type == "detailed_breakdown":
            story.append(Paragraph("Detailed Spend Logs (Recent)", h2_style))
            log_headers = [["Date", "Service", "Region", "Amount ($)"]]
            for r in costs[:25]:
                log_headers.append(
                    [str(r.date), r.service, r.region, f"${r.amount:,.2f}"]
                )
            t_logs = Table(log_headers, colWidths=[100, 150, 100, 150])
            t_logs.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(t_logs)

        elif report_type == "anomaly_report":
            story.append(Paragraph("Active Cost Anomalies", h2_style))
            if anomalies:
                anom_headers = [
                    ["Date", "Service", "Severity", "Impact Amount ($)", "Root Cause"]
                ]
                for a in anomalies[:10]:
                    anom_headers.append(
                        [
                            str(a.date),
                            a.service,
                            a.severity.upper(),
                            f"${a.impact_amount:,.2f}",
                            Paragraph(a.root_cause or "Analyzing", normal_style),
                        ]
                    )
                t_anom = Table(anom_headers, colWidths=[70, 90, 60, 90, 190])
                t_anom.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ef4444")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("PADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ]
                    )
                )
                story.append(t_anom)
            else:
                story.append(
                    Paragraph(
                        "No active anomalies detected in this billing cycle.",
                        normal_style,
                    )
                )

            story.append(Spacer(1, 15))

            if recommendations:
                story.append(Paragraph("Key Optimization Recommendations", h2_style))
                rec_headers = [["Service", "Recommendation", "Est. Monthly Savings"]]
                for r in recommendations[:10]:
                    rec_headers.append(
                        [
                            r.service,
                            Paragraph(r.recommendation, normal_style),
                            f"${r.monthly_savings:,.2f}",
                        ]
                    )
                t_rec = Table(rec_headers, colWidths=[100, 300, 100])
                t_rec.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("PADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ]
                    )
                )
                story.append(t_rec)

        elif report_type == "budget_variance":
            story.append(Paragraph("Budgets & Threshold Deviations", h2_style))
            if budgets:
                budget_headers = [
                    [
                        "Budget Name",
                        "Limit ($)",
                        "Spent ($)",
                        "Period",
                        "Status",
                        "Utilization",
                    ]
                ]
                for b in budgets:
                    budget_headers.append(
                        [
                            b.name,
                            f"${b.amount:,.2f}",
                            f"${b.spent:,.2f}",
                            b.period.capitalize(),
                            b.status.upper(),
                            f"{b.utilization_pct}%",
                        ]
                    )
                t_budget = Table(budget_headers, colWidths=[130, 70, 70, 70, 80, 80])
                t_budget.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b5cf6")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("PADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ]
                    )
                )
                story.append(t_budget)
            else:
                story.append(
                    Paragraph("No configured budgets found in settings.", normal_style)
                )

        doc.build(story)

    def _generate_excel(self, user_id: str, report_type: str, filepath: str):
        """Generate Excel (xlsx) document representation using CSV tab format or openpyxl."""
        try:
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "CloudWise Report"
            ws.append(
                [
                    "Date",
                    "Service",
                    "Region",
                    "Amount ($)",
                    "Usage Quantity",
                    "Granularity",
                ]
            )
            records = (
                self.db.query(CostRecord)
                .filter(CostRecord.user_id == user_id)
                .order_by(CostRecord.date.desc())
                .limit(1000)
                .all()
            )
            for r in records:
                ws.append(
                    [
                        str(r.date),
                        r.service,
                        r.region,
                        r.amount,
                        r.usage_quantity,
                        r.granularity,
                    ]
                )
            wb.save(filepath)
        except ImportError:
            # Fallback to TSV/CSV format if openpyxl is not installed
            self._generate_csv(user_id, report_type, filepath)
