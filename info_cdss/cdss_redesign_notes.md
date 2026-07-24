# CDSS Redesign Notes

# Rediseño del flujo clínico del CDSS

Este documento resume el rediseño de las páginas **Nuevo Paciente** e **Histórico**, estableciendo una separación clara de responsabilidades dentro del Sistema de Soporte a la Decisión Clínica (CDSS).

## Objetivo

- **Nuevo Paciente** gestiona exclusivamente el flujo de predicción mediante Inteligencia Artificial.
- **Histórico** gestiona la validación clínica y todo el ciclo de vida posterior al análisis.
- La predicción generada por la IA **nunca se considera un diagnóstico médico confirmado**.

## Responsabilidades por módulo

### Inferencia y registro de casos

- `streamlit_app/pages/new_patient.py`
  - Formulario de recogida de datos clínicos y del paciente.
  - Generación de la plantilla de RNA-Seq (.xlsx) basada en `feature_names.json`.
  - Validación y normalización de los datos de RNA-Seq.
  - Ejecución guiada de la inferencia con indicadores de progreso.
  - Creación del `ClinicalReport` y generación de informes en formato HTML y PDF.

- `managers/prediction_manager.py`
  - Carga de los modelos y de los nombres de las variables (`feature_names`).
  - Preprocesamiento de la muestra de entrada para adaptarla al formato esperado por el modelo.
  - Ejecución del Modelo 1 y, en caso de detectar un tumor, del Modelo 2.
  - Almacenamiento persistente de las predicciones y de una instantánea inmutable del contexto del análisis.

- `services/report_generator.py`
  - Define el objeto `ClinicalReport` como única fuente de información del informe.
  - Genera tanto la versión HTML como la PDF a partir del mismo objeto.
  - Incluye el aviso legal (disclaimer) obligatorio.

### Ciclo de vida de la validación clínica

- `streamlit_app/pages/history.py`
  - Tabla de casos con su estado y acciones disponibles.
  - Formulario de confirmación del diagnóstico para los casos pendientes.
  - Comparación automática entre la predicción y el diagnóstico confirmado (correcto/incorrecto).
  - Ejecución manual del reentrenamiento y visualización del historial de versiones de los modelos.

- `managers/feedback_manager.py`
  - Delega el proceso de confirmación del diagnóstico al servicio de base de datos.

- `streamlit_app/database/cdss_database.py`
  - Almacena la instantánea de la predicción, el estado del caso (pendiente o confirmado), el diagnóstico confirmado y el resultado de la comparación.
  - Conserva la predicción original sin modificaciones tras la validación clínica.
  - Marca los casos confirmados como aptos para el reentrenamiento.
  - Guarda la información de versionado de los modelos generados tras el reentrenamiento.

### Reentrenamiento (manual)

- `services/retraining.py`
  - Utiliza únicamente los casos clínicamente confirmados y marcados como aptos para el reentrenamiento.
  - Construye el conjunto de datos de reentrenamiento a partir de las muestras almacenadas.
  - Reentrena los modelos únicamente bajo demanda.
  - Genera nuevas versiones de los modelos junto con sus métricas de rendimiento.

## Aspectos principales del modelo de datos

La tabla `predictions` almacena:

- Información del paciente y del contexto clínico en el momento del análisis.
- Resultados y probabilidades del Modelo 1 y del Modelo 2.
- Resumen del proceso de validación.
- Campos asociados al ciclo de validación clínica:
  - `confirmed_diagnosis`
  - `case_status` (`PENDIENTE_VALIDACION` o `CONFIRMADO`)
  - `comparison_result` (`CORRECTO` o `INCORRECTO`)
  - `is_correct`
  - `retraining_eligible`

## Principio de seguridad

Todos los informes y elementos de la interfaz presentan los resultados como **predicciones generadas por Inteligencia Artificial para apoyar la toma de decisiones clínicas**, y **nunca como un diagnóstico médico definitivo**.