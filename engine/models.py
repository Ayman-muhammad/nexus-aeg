"""
Pydantic models for all domain entities.
Validation, type safety, and serialisation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uuid


class Building(BaseModel):
    code: str
    name: str
    capacity: int = Field(gt=0)
    location: Optional[str] = None


class Unit(BaseModel):
    code: str
    name: str
    year: int
    semester: int
    exam_duration_minutes: int = Field(gt=0, le=240)


class Invigilator(BaseModel):
    staff_id: str
    name: str
    email: Optional[str] = None
    max_consecutive_slots: int = Field(default=2, ge=1)


class Assessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    unit_code: str
    student_count: int = Field(gt=0)
    current_room: Optional[str] = None
    current_slot: Optional[str] = None  # Format: "YYYY-MM-DD HH:MM"
    invigilators: List[str] = Field(default_factory=list)

    @validator('current_slot', allow_reuse=True)  # ✅ FIXED
    def validate_slot_format(cls, v):
        if v is None:
            return v

        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError('Slot must be in format "YYYY-MM-DD HH:MM"')

        return v


class ExamSlot(BaseModel):
    datetime: datetime
    building_code: str
    room_code: str
    capacity: int = Field(gt=0)


class ConflictSolution(BaseModel):
    assessment_id: str
    proposed_room: str
    proposed_slot: str
    score: float = Field(ge=0)
    reasoning: Optional[str] = None