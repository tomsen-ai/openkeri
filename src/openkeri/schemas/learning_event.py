from datetime import datetime

from pydantic import BaseModel

from openkeri.schemas.current_input import CurrentInput
from openkeri.schemas.evidence import Evidence
from openkeri.schemas.teacher_output import TeacherOutput


class LearningEvent(BaseModel):
    event_id: str
    learner_id: str
    session_id: str
    current_input: CurrentInput
    evidence: Evidence
    teacher_output: TeacherOutput
    timestamp: datetime
