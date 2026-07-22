import uuid
from typing import Optional

from streamlit_app.database.cdss_database import CDSSDatabase


class FeedbackManager:
    def __init__(self):
        self.db = CDSSDatabase()

    def submit_feedback(self, prediction_id: int, confirmed_diagnosis: str, clinical_notes: str = "", is_correct: Optional[bool] = None):
        feedback_id = str(uuid.uuid4())
        self.db.save_feedback(
            feedback_id=feedback_id,
            prediction_id=prediction_id,
            confirmed_diagnosis=confirmed_diagnosis,
            clinical_notes=clinical_notes,
            is_correct=is_correct,
        )
        return feedback_id
