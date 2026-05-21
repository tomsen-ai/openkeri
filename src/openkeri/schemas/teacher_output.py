from pydantic import BaseModel

from openkeri.schemas.diagnosis import Diagnosis
from openkeri.schemas.teaching_action import TeachingAction


class TeacherOutput(BaseModel):
    diagnosis: Diagnosis
    teaching_action: TeachingAction
