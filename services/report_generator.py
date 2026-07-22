"""Clinical report generation based on a single ClinicalReport object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple


DISCLAIMER_TEXT = (
    "Este informe corresponde a la prediccion realizada por un modelo de inteligencia "
    "artificial desarrollado con fines de investigacion y apoyo a la decision clinica. "
    "No constituye un diagnostico medico ni sustituye el criterio del profesional sanitario."
)


@dataclass
class ClinicalReport:
    generated_at: str
    patient: Dict[str, Any]
    clinical_info: Dict[str, Any]
    sample_validation: Dict[str, Any]
    model1_result: Dict[str, Any]
    model2_result: Dict[str, Any]
    probabilities: Dict[str, float]
    observations: str


class ReportGeneratorService:
    def is_available(self) -> bool:
        return True

    def create_clinical_report(
        self,
        patient: Dict[str, Any],
        clinical_info: Dict[str, Any],
        sample_validation: Dict[str, Any],
        model1_result: Dict[str, Any],
        model2_result: Dict[str, Any],
        probabilities: Dict[str, float],
        observations: str,
    ) -> ClinicalReport:
        return ClinicalReport(
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            patient=patient,
            clinical_info=clinical_info,
            sample_validation=sample_validation,
            model1_result=model1_result,
            model2_result=model2_result,
            probabilities=probabilities,
            observations=observations,
        )

    def _section_rows(self, report: ClinicalReport) -> List[Tuple[str, List[Tuple[str, str]]]]:
        validation = report.sample_validation or {}
        probs = report.probabilities or {}

        probs_rows = [(label, f"{value:.4f}") for label, value in sorted(probs.items(), key=lambda item: item[1], reverse=True)]
        if not probs_rows:
            probs_rows = [("No aplica", "-")]

        return [
            (
                "Informacion del paciente",
                [
                    ("ID paciente", str(report.patient.get("patient_id", ""))),
                    ("Nombre", str(report.patient.get("first_name", ""))),
                    ("Apellidos", str(report.patient.get("last_name", ""))),
                    ("Edad", str(report.patient.get("age", ""))),
                    ("Sexo", str(report.patient.get("sex", ""))),
                    ("Nacionalidad", str(report.patient.get("nationality", ""))),
                ],
            ),
            (
                "Informacion clinica",
                [
                    ("Peso (kg)", str(report.clinical_info.get("weight_kg", ""))),
                    ("Altura (cm)", str(report.clinical_info.get("height_cm", ""))),
                    ("IMC", str(report.clinical_info.get("bmi", ""))),
                    ("Clasificacion IMC", str(report.clinical_info.get("bmi_classification", ""))),
                    ("Estado de fumador", str(report.clinical_info.get("smoker_status", ""))),
                ],
            ),
            (
                "Validacion de la muestra",
                [
                    ("Genes encontrados", str(validation.get("genes_found", "N/D"))),
                    ("Genes faltantes", str(validation.get("missing_count", "N/D"))),
                    ("Genes adicionales", str(validation.get("extra_count", "N/D"))),
                    ("Valores no numericos", str(validation.get("non_numeric_count", "N/D"))),
                    ("Valores nulos", str(validation.get("null_count", "N/D"))),
                    ("Estado general", str(validation.get("status", "N/D"))),
                ],
            ),
            (
                "Resultado Modelo 1",
                [
                    ("Clase predicha", str(report.model1_result.get("predicted_label", ""))),
                    ("Normal / Tumoral", str(report.model1_result.get("normal_tumoral", ""))),
                    ("Probabilidad", str(report.model1_result.get("probability", ""))),
                ],
            ),
            (
                "Resultado Modelo 2",
                [
                    ("Tipo de cancer estimado", str(report.model2_result.get("predicted_cancer", "No aplica"))),
                    ("Probabilidad", str(report.model2_result.get("probability", "No aplica"))),
                ],
            ),
            (
                "Tabla de probabilidades",
                probs_rows,
            ),
            (
                "Observaciones",
                [
                    ("Notas", str(report.observations or "Sin observaciones.")),
                    ("Fecha y hora", report.generated_at),
                ],
            ),
        ]

    def render_html_report(self, report: ClinicalReport) -> str:
        sections = self._section_rows(report)

        section_html_parts = []
        for title, rows in sections:
            rows_html = "".join(
                f"<tr><th>{label}</th><td>{value}</td></tr>"
                for label, value in rows
            )
            section_html_parts.append(
                f"""
                <section class='block'>
                    <h3>{title}</h3>
                    <table>{rows_html}</table>
                </section>
                """
            )

        sections_html = "\n".join(section_html_parts)

        return f"""
        <div class='report'>
            <header>
                <div class='logo'>OncoSeq Explorer</div>
                <div class='meta'>Informe de resultados IA<br/>{report.generated_at}</div>
            </header>
            {sections_html}
            <footer>
                <small>{DISCLAIMER_TEXT}</small>
            </footer>
        </div>
        <style>
            .report {{ background:#fff; border:1px solid #dbe4ef; border-radius:14px; padding:20px; }}
            .report header {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #e2e8f0; padding-bottom:12px; margin-bottom:14px; }}
            .logo {{ font-size:22px; font-weight:700; color:#0f4c81; }}
            .meta {{ color:#475569; font-size:13px; text-align:right; }}
            .block {{ margin-bottom:12px; }}
            .block h3 {{ margin:0 0 8px 0; color:#0f172a; font-size:15px; border-left:4px solid #1068DA; padding-left:8px; }}
            table {{ width:100%; border-collapse:collapse; }}
            th, td {{ border:1px solid #e2e8f0; padding:7px; font-size:12px; text-align:left; }}
            th {{ width:35%; background:#f8fafc; }}
            footer {{ margin-top:14px; padding-top:10px; border-top:1px dashed #cbd5e1; color:#334155; }}
        </style>
        """

    def build_pdf_from_report(self, report: ClinicalReport) -> bytes | None:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except Exception:
            return None

        sections = self._section_rows(report)
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        _, height = A4

        y = height - 45
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, "OncoSeq Explorer - Informe de resultados IA")
        y -= 16
        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, report.generated_at)
        y -= 18

        for title, rows in sections:
            if y < 90:
                pdf.showPage()
                y = height - 45
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, title)
            y -= 14
            pdf.setFont("Helvetica", 9)
            for label, value in rows:
                text = f"- {label}: {value}"
                pdf.drawString(46, y, text[:120])
                y -= 12
                if y < 70:
                    pdf.showPage()
                    y = height - 45
                    pdf.setFont("Helvetica", 9)
            y -= 4

        if y < 80:
            pdf.showPage()
            y = height - 45

        pdf.setFont("Helvetica-Oblique", 8)
        disclaimer_lines = [
            DISCLAIMER_TEXT[i:i + 120]
            for i in range(0, len(DISCLAIMER_TEXT), 120)
        ]
        for line in disclaimer_lines:
            pdf.drawString(40, y, line)
            y -= 10

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()
