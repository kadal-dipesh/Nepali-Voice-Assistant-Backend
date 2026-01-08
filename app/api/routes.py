from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatIn(BaseModel):
    session_id: str
    text: str

@router.post("/chat")
def chat(inp: ChatIn):
    #Placeholder for now
    return {
        "session_id": inp.session_id,
        "text": inp.text,
        "message": "Day 5 started",
    }
