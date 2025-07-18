from app.graph.event_scheduler_graph import graph
from langchain_core.messages import HumanMessage

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
load_dotenv()
import os 

router = APIRouter(tags=["mail"])

class UserInput(BaseModel):
    messages: List[str]

@router.post("/interact/")
async def interact(user_input: UserInput):
    config = {"configurable": {"thread_id": "1"}}
    responses = []
    
    for s in graph.stream({"messages": [HumanMessage(content=msg) for msg in user_input.messages]}, config):
        if 'supervisor' in s:
            # Supervisor detected, skipping...
            continue
        
        res = None  # Initialize `res` to handle cases where it might not be set
        
        # Try to access content and print it
        for key, value in s.items():
            if isinstance(value, dict) and 'messages' in value:
                for message in value['messages']:
                    res = message.content
                    print(res)  # Debug print

        if res:  # Only append if `res` was set
            responses.append(res)
    
    if not responses:
        raise HTTPException(status_code=400, detail="No response generated.")
    
    return {"response": responses}

@router.get("/")
def read_root():
    return {"message": "Welcome to the LangChain API!"}