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

class NLUResult:
    """
    Temporary structure representing NLU output.
    This will later be replaced by real model output.
    """

    def __init__(
        self,
        intent: Optional[Intent] = None,
        confidence: float = 0.0,
        entities: Optional[dict] = None,
    ):
        self.intent = intent
        self.confidence = confidence
        self.entities = entities or {}

def next_plan(state: DialogueState, nlu: NLUResult) -> DialoguePlan:
    """
    Decide the next system action.
    """

    state.turn_index += 1

    #1 Greeting
    if nlu.intent == Intent.GREETING and not state.intent_locked:
        return DialoguePlan(
            action = Action.GREET,
            message = "नमस्ते। म तपाईंको अपोइन्टमेन्ट सहायक हुँ। कसरी सहयोग गर्न सक्छु?",
        )
    #2 Start booking flow
    if nlu.intent == Intent.BOOK_APPOINTMENT and not state.intent_locked:
        state.intent = Intent.BOOK_APPOINTMENT 
        state.intent_locked = True

        #Fill slots from entities (if any)
        for key, value in nlu.entities.items():
            if hasattr(state.slots, key):
                setattr(state.slots, key, value)

        return DialoguePlan(
            action=Action.ASK_DEPARTMENT,
                message="कुन विभागमा अपोइन्टमेन्ट चाहियो?",
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
        message="मलाई बुझ्न समस्या भयो। कृपया फेरि भन्नुहोस्।",
    )
