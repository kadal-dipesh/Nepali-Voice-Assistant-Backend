"""
Dialogue state schema for the Nepali Voice Assistant Backend

    The file defines:
    -Intent names (task-level)
    -Slot we track across turns
    -DialogueState object stored per session
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

class Intent(str, Enum):
    BOOK_APPOINTMENT = "BookAppointment"
    CANCEL_APPOINTMENT = "CancelAppointment"
    RESCHEDULE_APPOINTMENT = "RescheduleAppointment"
    UPDATE_APPOINTMENT = "UpdateAppointment"
    FAQ_LOOKUP = "FAQLookUp"
    DOCTOR_LOOKUP = "DoctorLookUp"
    GREETING = "Greeting"
    CLARIFICATION = "Clarification"
    FALLBACK = "FallBack"

class Action(str, Enum):
    #Conversation control
    GREET = "GREET"
    ASK_CLARIFY = "ASK_CLARIFY"
    FALLBACK = "FALLBACK"
    END = "END"

    #Slot-filling questions
    ASK_DOCTOR = "ASK_DOCTOR"
    ASK_DEPARTMENT = "ASK_DEPARTMENT"
    ASK_DATE = "ASK_DATE"
    ASK_TIME = "ASK_TIME"
    ASK_PATIENT_NAME = "ASK_PATIENT_NAME"
    ASK_PHONE = "ASK_PHONE"

    #Informational flows
    SHOW_DOCTORS = "SHOW_DOCTORS"       # list doctors (by dept)
    SHOW_AVAILABLE_DOCTORS = "SHOW_AVAILABLE_DOCTORS"      # based on date/time/dept 
    
    # Confirm + execute (later DAY 7-8)
    CONFIRM_BOOK = "CONFIRM_BOOK"
    CONFIRM_CANCEL = "CONFIRM_CANCEL"
    CONFIRM_RESCHEDULE = "CONFIRM_RESCHEDULE"
    CONFIRM_UPDATE = "CONFIRM_UPDATE"

    EXECUTE_BOOK = "EXECUTE_BOOK"
    EXECUTE_CANCEL = "EXECUTE_CANCEL"
    EXECUTE_RESCHEDULE = "EXECUTE_RESCHEDULE"
    EXECUTE_UPDATE = "EXECUTE_UPDATE"
    
    
@dataclass 
class Slots:
    #Appointment-related
    doctor: Optional[str] = None
    department: Optional[str] = None

    #Date and Time:
    #We will store raw text for now (jastai nepali time wala)
    #Later we can normalize into AD ISO date/time
    date: Optional[str] = None
    time: Optional[str] = None

    #Patient info
    patient_name: Optional[str] = None
    phone: Optional[str] = None

@dataclass 
class DialogueState:
    session_id: str

    #Current locked intent (task).
    intent: Optional[Intent] = None
    intent_locked: bool = False

    #slots collected so far
    slots: Slots = field(default_factory=Slots)

    #Track what the system last asked or did, so we can interpret short replies.
    last_action: Optional[str] = None

    #For DoctorLookUp -> Offer booking flow
    candidate_doctors: List[str] = field(default_factory=list)

    #Debug / trace
    turn_index: int = 0
    meta: Dict[str, str] = field(default_factory=dict)

@dataclass
class DialoguePlan:
    action: Action
    message: str

    #Optional: structured payload for UI or caller
    data: Dict[str, object] = field(default_factory=dict)
    
    #Optional: whether this plan expect user to answer something next
    expects_user_input: bool = True

def missing_slots_for_booking(slots: Slots) -> List[str]:
    missing = []
    if not slots.department:
        missing.append("department")
    if not slots.doctor:
        missing.append("doctor")
    if not slots.date:
        missing.append("date")
    if not slots.time:
        missing.append("time")
    if not slots.patient_name:
        missing.append("patient_name")
    if not slots.phone:
        missing.append("phone")
    return missing
