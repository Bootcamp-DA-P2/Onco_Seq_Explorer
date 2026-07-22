# CDSS Redesign Notes

This document summarizes the redesign of Nuevo Paciente and Historico pages with clear CDSS role separation.

## Objective

- Nuevo Paciente handles AI prediction workflow only.
- Historico handles clinical validation and post-analysis lifecycle.
- AI prediction is never treated as confirmed medical diagnosis.

## Responsibilities by Module

### Inference and Case Registration

- `streamlit_app/pages/new_patient.py`
  - Clinical intake form (patient and clinical info)
  - RNA-Seq template generation (.xlsx) based on `feature_names.json`
  - RNA-Seq validation and normalization
  - Guided inference execution with progress stages
  - ClinicalReport creation and HTML/PDF report rendering

- `managers/prediction_manager.py`
  - Loads models and feature names
  - Preprocesses input sample to model-expected schema
  - Executes model 1 and model 2 (if tumor)
  - Persists immutable prediction outputs and context snapshot

- `services/report_generator.py`
  - Single source of truth object: `ClinicalReport`
  - Generates both HTML and PDF views from same object
  - Includes mandatory disclaimer

### Clinical Validation Lifecycle

- `streamlit_app/pages/history.py`
  - Case table with status and actions
  - Diagnosis confirmation form for pending cases
  - Automatic comparison display (correct/incorrect)
  - Manual retraining trigger and model version history view

- `managers/feedback_manager.py`
  - Delegates confirmation trigger to database service

- `streamlit_app/database/cdss_database.py`
  - Stores prediction snapshot, pending/confirmed state, confirmed diagnosis, comparison result
  - Keeps original prediction unchanged after validation
  - Marks confirmed cases as retraining-eligible
  - Stores model version metadata for retraining outputs

### Retraining (Manual)

- `services/retraining.py`
  - Uses only clinically confirmed and eligible cases
  - Builds retraining set from persisted sample snapshots
  - Retrains models on demand only
  - Writes versioned model artifacts and metrics

## Data Model Highlights

The `predictions` table now captures:

- Patient and clinical context at analysis time
- Model 1 and model 2 outputs and probabilities
- Validation summary snapshot
- Clinical validation lifecycle fields:
  - `confirmed_diagnosis`
  - `case_status` (`PENDIENTE_VALIDACION` or `CONFIRMADO`)
  - `comparison_result` (`CORRECTO`/`INCORRECTO`)
  - `is_correct`
  - `retraining_eligible`

## Safety Principle

All reports and UI semantics state results as AI predictions for decision support, not definitive diagnosis.
