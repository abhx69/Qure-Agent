"""
main.py - FastAPI application (Updated for Hybrid Chat)
"""

import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the UPDATED class instance
from agent_brain import agent_brain 
from database import db_manager
from tools.asana_tool import execute_asana_task
from tools.google_tool import send_gmail

load_dotenv()

app = FastAPI(title="Gaprio Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserMessage(BaseModel):
    user_id: int
    message: str

class ActionApproval(BaseModel):
    user_id: int
    action_id: int

class ActionData(BaseModel):
    tool: str
    provider: str
    parameters: Dict

# Routes
@app.get("/")
async def root():
    return {"message": "Gaprio Agent API", "status": "running"}

@app.post("/ask-agent")
async def ask_agent(user_msg: UserMessage):
    """
    Process user message, returns { message: "...", plan: [...] }
    """
    try:
        # Call the NEW method in agent_brain that returns both text and actions
        response = agent_brain.get_agent_response(user_msg.user_id, user_msg.message)
        
        return {
            "status": "success",
            "message": response["message"], # The chat reply (e.g. "I have drafted the email")
            "plan": response["plan"],       # The actions list (if any)
            "requires_approval": len(response["plan"]) > 0
        }
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pending-actions/{user_id}")
async def get_pending_actions(user_id: int):
    """
    Get all pending actions for a user
    """
    try:
        actions = agent_brain.get_pending_actions(user_id)
        return {
            "status": "success", 
            "count": len(actions), 
            "actions": actions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approve-action")
async def approve_action(approval: ActionApproval):
    """
    Approve and execute a pending action
    """
    try:
        result = agent_brain.approve_action(approval.action_id)
        
        if result["success"]:
            return {
                "status": "success", 
                "message": "Action executed successfully", 
                "data": result.get("result")
            }
        else:
            return {
                "status": "error", 
                "message": result.get("error", "Execution failed")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-action")
async def execute_action(action: ActionData):
    """
    Direct action execution (without approval flow)
    """
    try:
        token = db_manager.get_user_token(action.user_id, action.provider)
        
        if not token:
            raise HTTPException(status_code=400, detail=f"No {action.provider} token found")
        
        result = None
        # Handle Asana
        if action.provider == 'asana' and action.tool == 'create_asana_task':
            result = execute_asana_task(token['access_token'], action.parameters)
        
        # Handle Gmail
        elif action.provider == 'google' and action.tool == 'send_gmail':
            result = send_gmail(token['access_token'], action.parameters)
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported action or provider")
        
        return {
            "status": "success", 
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint with proper database connection test"""
    try:
        db_status = "disconnected"
        try:
            # Check DB connection
            if db_manager.connection and db_manager.connection.is_connected():
                cursor = db_manager.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                db_status = "connected"
        except Exception as e:
            print(f"DB Health Check Failed: {e}")
            pass
        
        return {
            "status": "healthy", 
            "database": db_status, 
            "ollama": "configured",
            "version": "1.0.0"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('APP_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)