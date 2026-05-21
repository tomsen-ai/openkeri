from pydantic import BaseModel

from openkeri.schemas.current_input import CurrentInput
from openkeri.schemas.evidence import Evidence
from openkeri.schemas.memory import MemoryContext


class TeachingContext(BaseModel):
    current_input: CurrentInput
    memory_context: MemoryContext
    evidence: Evidence
