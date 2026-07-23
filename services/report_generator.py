"""Clinical report generation with a single HTML source for both UI and PDF."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Any, Dict


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

    def render_html_report(self, report: ClinicalReport) -> str:
        validation = report.sample_validation or {}
        is_tumor = str(report.model1_result.get("normal_tumoral", "")).strip().lower() == "tumoral"
        principal_result = (
            str(report.model2_result.get("predicted_cancer", "No aplica")) if is_tumor else "Sin evidencia tumoral"
        )
        principal_probability = (
            str(report.model2_result.get("probability", "No aplica")) if is_tumor else str(report.model1_result.get("probability", "-"))
        )

        patient_name = f"{report.patient.get('first_name', '')} {report.patient.get('last_name', '')}".strip() or "No especificado"
        patient_id = str(report.patient.get("patient_id", "No disponible"))
        age = str(report.patient.get("age", "N/D"))
        sex = str(report.patient.get("sex", "N/D"))
        smoker_status = str(report.clinical_info.get("smoker_status", "N/D"))
        bmi = report.clinical_info.get("bmi")
        bmi_text = f"{bmi}" if bmi is not None else "N/D"

        validation_status = str(validation.get("status", "N/D"))
        sample_quality = "Adecuada" if validation_status in {"VALIDA", "VALIDA_CON_AJUSTES"} else "Revisar"
        missing_count = int(validation.get("missing_count", 0) or 0)
        extra_count = int(validation.get("extra_count", 0) or 0)
        quality_notes = "Sin incidencias" if (missing_count == 0 and extra_count == 0) else "Se aplicaron ajustes automáticos"

        notes = escape(str(report.observations or "Sin observaciones clínicas."))
        principal_result = escape(principal_result)
        principal_probability = escape(principal_probability)
        patient_name = escape(patient_name)
        patient_id = escape(patient_id)
        age = escape(age)
        sex = escape(sex)
        smoker_status = escape(smoker_status)
        bmi_text = escape(bmi_text)
        validation_status = escape(validation_status)
        sample_quality = escape(sample_quality)
        quality_notes = escape(quality_notes)

        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
                body {{
                    margin: 0;
                    font-family: "Segoe UI", Arial, sans-serif;
                    background: #f4f7fb;
                    color: #0b1220;
                }}
                .report {{
                    max-width: 940px;
                    margin: 0 auto;
                    padding: 24px;
                }}
                .header {{
                    background: #ffffff;
                    border: 1px solid #d9e2ec;
                    border-radius: 18px;
                    padding: 18px 20px;
                    margin-bottom: 14px;
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    box-shadow: 0 8px 28px rgba(13, 26, 38, 0.06);
                }}
                .brand {{
                    font-size: 22px;
                    font-weight: 700;
                    color: #0e3b63;
                }}
                .meta {{
                    text-align: right;
                    font-size: 12px;
                    color: #4b5563;
                }}
                .result-hero {{
                    background: linear-gradient(160deg, #ffffff 0%, #f8fbff 100%);
                    border: 1px solid #d7e7f8;
                    border-radius: 18px;
                    padding: 16px 18px;
                    margin-bottom: 14px;
                }}
                .hero-title {{
                    font-size: 13px;
                    color: #3b5b7b;
                    margin-bottom: 8px;
                    font-weight: 600;
                }}
                .hero-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                }}
                .card {{
                    background: #ffffff;
                    border: 1px solid #e3e8ef;
                    border-radius: 14px;
                    padding: 14px;
                    margin-bottom: 10px;
                }}
                .kpi-label {{
                    font-size: 11px;
                    color: #4b5563;
                    text-transform: uppercase;
                    letter-spacing: 0.6px;
                }}
                .kpi-value {{
                    font-size: 30px;
                    font-weight: 700;
                    color: #0d3f67;
                    line-height: 1.12;
                    margin-top: 2px;
                }}
                .muted {{
                    font-size: 12px;
                    color: #6b7280;
                }}
                .card h3 {{
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #0f3759;
                    font-weight: 600;
                }}
                .mini-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 8px 12px;
                    font-size: 12px;
                }}
                .mini-grid div {{ color: #1f2937; }}
                .footer {{
                    margin-top: 14px;
                    background: #fff;
                    border: 1px dashed #cbd5e1;
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 11px;
                    color: #334155;
                    line-height: 1.45;
                }}
            </style>
        </head>
        <body>
            <main class="report">
                <section class="header">
                    <div>
                        <div class="brand">OncoSeq Explorer</div>
                        <div class="muted">Informe clínico de apoyo a la decisión</div>
                    </div>
                    <div class="meta">Fecha del analisis<br>{report.generated_at}</div>
                </section>

                <section class="result-hero">
                    <div class="hero-title">Resultado principal</div>
                    <div class="hero-grid">
                        <div>
                            <div class="kpi-label">Tipo de cáncer estimado</div>
                            <div class="kpi-value">{principal_result}</div>
                        </div>
                        <div>
                            <div class="kpi-label">Probabilidad</div>
                            <div class="kpi-value">{principal_probability}</div>
                        </div>
                    </div>
                </section>

                <section class="card">
                    <h3>Paciente</h3>
                    <div class="mini-grid">
                        <div><strong>ID:</strong> {patient_id}</div>
                        <div><strong>Nombre:</strong> {patient_name}</div>
                        <div><strong>Edad:</strong> {age}</div>
                        <div><strong>Sexo:</strong> {sex}</div>
                    </div>
                </section>

                <section class="card">
                    <h3>Contexto clínico</h3>
                    <div class="mini-grid">
                        <div><strong>IMC:</strong> {bmi_text}</div>
                        <div><strong>Tabaquismo:</strong> {smoker_status}</div>
                        <div><strong>Estado muestra:</strong> {validation_status}</div>
                        <div><strong>Calidad global:</strong> {sample_quality}</div>
                    </div>
                    <div class="muted" style="margin-top:8px;">{quality_notes}</div>
                </section>

                <section class="card">
                    <h3>Observaciones clínicas</h3>
                    <div class="muted" style="font-size:12px; color:#1f2937;">{notes}</div>
                </section>

                <section class="footer">
                    {DISCLAIMER_TEXT}
                </section>
            </main>
        </body>
        </html>
        """

    def build_pdf_from_html(self, html: str) -> bytes | None:
        # Primary engine: WeasyPrint (best CSS fidelity when native deps are available).
        try:
            from weasyprint import HTML
            return HTML(string=html).write_pdf()
        except Exception:
            pass

        # Fallback engine: xhtml2pdf keeps the same HTML source without duplicating report logic.
        try:
            from io import BytesIO
            from xhtml2pdf import pisa

            output = BytesIO()
            result = pisa.CreatePDF(html, dest=output)
            if result.err:
                return None
            return output.getvalue()
        except Exception:
            return None

    def build_pdf_from_report(self, report: ClinicalReport) -> bytes | None:
        html = self.render_html_report(report)
        return self.build_pdf_from_html(html)
