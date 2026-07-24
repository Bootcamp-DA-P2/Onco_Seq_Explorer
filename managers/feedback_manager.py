from database.cdss_database import CDSSDatabase


class FeedbackManager:
    def __init__(self):
        self.db = CDSSDatabase()

    def submit_feedback(self, prediction_id: int, confirmed_diagnosis: str, clinical_notes: str = ""):
        return self.db.confirm_case_validation(
            prediction_id=prediction_id,
            confirmed_diagnosis=confirmed_diagnosis,
            clinical_notes=clinical_notes,
        )
