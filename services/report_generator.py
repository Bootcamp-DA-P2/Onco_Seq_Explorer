"""Clinical report generation helpers."""

from __future__ import annotations

from io import BytesIO
from typing import Dict, Any


class ReportGeneratorService:
    """Generates lightweight clinical PDF reports."""

    def is_available(self) -> bool:
        try:
            from reportlab.pdfgen import canvas  # noqa: F401
            return True
        except Exception:
            return False

    def build_patient_intake_pdf_bytes(self, patient_data: Dict[str, Any]) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        pdf.setTitle("Informe clínico - OncoSeq Explorer")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, height - 50, "OncoSeq Explorer - Informe clínico de paciente")

        pdf.setFont("Helvetica", 10)
        y = height - 85
        line_gap = 16

        rows = [
            ("Patient ID", patient_data.get("patient_id", "")),
            ("Edad", patient_data.get("age", "")),
            ("Sexo", patient_data.get("sex", "")),
            ("Nacionalidad", patient_data.get("nationality", "")),
            ("Peso (kg)", patient_data.get("weight_kg", "")),
            ("Altura (cm)", patient_data.get("height_cm", "")),
            ("IMC", patient_data.get("bmi", "")),
            ("Clasificación IMC", patient_data.get("bmi_classification", "")),
            ("Estado de fumador", patient_data.get("smoker_status", "")),
        ]

        for label, value in rows:
            pdf.drawString(40, y, f"{label}: {value}")
            y -= line_gap

        notes = str(patient_data.get("clinical_notes", "") or "")
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y - 6, "Notas clínicas")
        y -= 24
        pdf.setFont("Helvetica", 10)

        if notes:
            max_chars = 110
            while notes:
                line = notes[:max_chars]
                notes = notes[max_chars:]
                pdf.drawString(40, y, line)
                y -= 14
                if y < 60:
                    pdf.showPage()
                    y = height - 50
                    pdf.setFont("Helvetica", 10)
        else:
            pdf.drawString(40, y, "Sin observaciones.")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()