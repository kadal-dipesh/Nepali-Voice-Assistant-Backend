"""
Dialogue policy: decides the next system action
based on dialouge state and NLU result
"""

from typing import Optional
from app.dialogue_manager.state import(
    DialogueState,
    DialoguePlan,
    Intent,
    Action,
)

BOOKING_SLOT_ORDER = [ 
    ("department", Action.ASK_DEPARTMENT, "कुन विभागमा अपोइन्टमेन्ट चाहियो?"),
    ("doctor", Action.ASK_DOCTOR, "कुन डाक्टरसँग अपोइन्टमेन्ट चाहियो?"),
    ("date", Action.ASK_DATE, "कुन मितिमा अपोइन्टमेन्ट चाहियो?"),
    ("time", Action.ASK_TIME, "कुन समयमा अपोइन्टमेन्ट चाहियो?"),
    ("patient_name", Action.ASK_PATIENT_NAME, "तपाईंको नाम भन्नुहोस्।"),
    ("phone", Action.ASK_PHONE, "तपाईंको फोन नम्बर भन्नुहोस्।"),
]

YES_WORDS = {"हो", "हुन्छ", "ठीक", "ठिक", "ठीक छ", "ठिक छ", "ओके", "ok", "okay", "hunchha"}
NO_WORDS = {"होइन", "हुँदैन", "हुन्न", "छैन", "no", "nah"}

def normalize_text(t:str) -> str:
    return " ".join((t or "").strip().lower().split())

def is_yes(text: str) -> bool:
    t = normalize_text(text)
    return t in YES_WORDS

def is_no(text: str) -> bool:
    t = normalize_text(text)
    return t in NO_WORDS

class NLUResult:
    """
    Temporary structure representing NLU output.
    This will later be replaced by real model output.
    """

    def __init__(
        self,
        text: str = "",
        intent: Optional[Intent] = None,
        confidence: float = 0.0,
        entities: Optional[dict] = None,
    ):
        self.text = text
        self.intent = intent
        self.confidence = confidence
        self.entities = entities or {}

def apply_entities_to_slots(state: DialogueState, entities: dict) -> None:
    for key, value in entities.items():
        if hasattr(state.slots, key) and value:
            setattr(state.slots, key, value)

def apply_last_action_answer(state: DialogueState, user_text:str) -> bool:
    """
    If the system last asked for a specific slot, interpret user_text as that slot.
    Return True if we updated any slot.
    """

    t = (user_text or "").strip()
    if not t:
        return False
    
    if state.last_action == Action.ASK_DEPARTMENT.value and not state.slots.department:
        state.slots.department = t
        return True
    
    if state.last_action == Action.ASK_DOCTOR.value and not state.slots.doctor:
        state.slots.doctor = t 
        return True
    
    if state.last_action == Action.ASK_DATE.value and not state.slots.date:
        state.slots.date = t 
        return True

    if state.last_action == Action.ASK_TIME.value and not state.slots.time:
        state.slots.time = t 
        return True

    if state.last_action == Action.ASK_PATIENT_NAME.value and not state.slots.patient_name:
        state.slots.patient_name = t 
        return True

    if state.last_action == Action.ASK_PHONE.value and not state.slots.phone:
        state.slots.phone = t 
        return True
    
    return False

def next_missing_booking_question(state: DialogueState) -> Optional[DialoguePlan]:
    for slot_name, action, prompt in BOOKING_SLOT_ORDER:
        if getattr(state.slots, slot_name) in (None, ""): 
            state.last_action = action.value
            return DialoguePlan(action=action, message=prompt)
    return None
            
def next_plan(state: DialogueState, nlu: NLUResult) -> DialoguePlan:
    """
    Decide the next system action.
    """

    state.turn_index += 1

    #If we are already in the middle of a task, continue it.
    if state.intent_locked and state.intent == Intent.BOOK_APPOINTMENT:
        # 1) Update slots from NLU entities (even if intent is useless)  
        apply_entities_to_slots(state, nlu.entities)
        # if NER didn't extract anything useful, try interpreting the raw text
        if not nlu.entities:
            apply_last_action_answer(state, nlu.text)

        # 2) Ask next missing slot 
        plan = next_missing_booking_question(state)
        if plan:
            return plan
        
        if state.last_action == Action.CONFIRM_BOOK.value:
            if is_yes(nlu.text):
                state.last_action = Action.EXECUTE_BOOK.value
                return DialoguePlan(
                        action=Action.EXECUTE_BOOK,
                        message="ठीक छ। अब तपाईंको अपोइन्टमेन्ट बुक गर्दैछु।",
                        expects_user_input=False,
                )
            if is_no(nlu.text):
                state.last_action = Action.ASK_CLARIFY.value
                return DialoguePlan(
                        action= Action.ASK_CLARIFY,
                        message="ठीक छ। के परिवर्तन गर्न चाहनुहुन्छ? (डाक्टर/विभाग/मिति/समय)",
                )

        # 3) If all slots filled, move to confirmation (we'll implement late)
        state.last_action = Action.CONFIRM_BOOK.value
        return DialoguePlan(
                action=Action.CONFIRM_BOOK,
                message=(
                    f"ठीक छ। विभाग: {state.slots.department}, डाक्टर: {state.slots.doctor}, "
                    f"मिति: {state.slots.date}, समय: {state.slots.time}। "
                    "यो जानकारी ठीक छ?"
                ),
        )
    #1 Greeting
    if nlu.intent == Intent.GREETING and not state.intent_locked:
        state.last_action = Action.GREET.value
        return DialoguePlan(
            action = Action.GREET,
            message = "नमस्ते। म तपाईंको अपोइन्टमेन्ट सहायक हुँ। कसरी सहयोग गर्न सक्छु?",
        )
    #2 Start booking flow
    if nlu.intent == Intent.BOOK_APPOINTMENT and not state.intent_locked:
        state.intent = Intent.BOOK_APPOINTMENT 
        state.intent_locked = True

        #Fill slots from entities (if any)
        apply_entities_to_slots(state, nlu.entities)

        #Ask missing slot
        plan = next_missing_booking_question(state)
        if plan:
            return plan

        #Edge case: everything is already provided
        state.last_action = Action.CONFIRM_BOOK.value
        return DialoguePlan(
            action=Action.CONFIRM_BOOK,
                message="सबै जानकारी प्राप्त भयो। के यो ठीक छ?",
        )
    #3 Clarification
    if nlu.intent == Intent.CLARIFICATION:
        return DialoguePlan(
            action=Action.ASK_CLARIFY,
            message="मलाई स्पष्ट बुझिन। के तपाईं अपोइन्टमेन्ट बुक, क्यान्सल, वा अपडेट गर्न चाहनुहुन्छ?",
        )
    #4 Fallback
    if nlu.intent == Intent.FALLBACK:
        return DialoguePlan(
            action=Action.FALLBACK,
            message="म अपोइन्टमेन्ट सम्बन्धी मात्र सहयोग गर्न सक्छु। कृपया अपोइन्टमेन्टको बारेमा भन्नुहोस्।",
        )
    
    return DialoguePlan(
        action=Action.ASK_CLARIFY,
        message="मैले स्पष्ट बुझिन। के तपाईं अपोइन्टमेन्ट बुक, क्यान्सल, वा अपडेट गर्न चाहनुहुन्छ?",
    )
