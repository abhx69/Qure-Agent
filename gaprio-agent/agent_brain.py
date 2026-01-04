"""
agent_brain.py - Hybrid Chat & Action Logic (Fixed)
"""

import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from database import db_manager
from tools.asana_tool import AsanaAPI

load_dotenv()

class AgentBrain:
    """
    Main AI Brain.
    Handles:
    1. Chatting with the user.
    2. Parsing commands into actions.
    3. Saving actions to the database.
    """
    
    def __init__(self, model: str = None):
        self.model = model or os.getenv('LLM_MODEL', 'llama3:instruct')
        print(f"🧠 Initializing Agent Brain with model: {self.model}")
        self.llm = OllamaLLM(model=self.model, format="json")
        
        # Connect to database
        if not db_manager.connect():
            print("⚠️ Running in limited mode (no database connection)")
    
    def get_agent_response(self, user_id: int, user_message: str) -> Dict:
        """
        Process user message and return both a chat reply and any actions.
        """
        print(f"\n📨 Processing message from user {user_id}: {user_message}")
        
        # 1. Get user's available tools
        asana_token = db_manager.get_user_token(user_id, 'asana')
        gmail_token = db_manager.get_user_token(user_id, 'google')
        
        has_asana = bool(asana_token)
        has_gmail = bool(gmail_token)
        
        print(f"   Available tools: Asana={has_asana}, Gmail={has_gmail}")
        
        # 2. Build the Hybrid Prompt
        prompt = self._build_hybrid_prompt(user_message, has_asana, has_gmail)
        
        try:
            print("🤖 Thinking (Chat + Action)...")
            response = self.llm.invoke(prompt)
            print(f"   LLM Raw Response: {response[:200]}...")
            
            # 3. Parse Response
            result = self._parse_llm_response(response)
            
            actions = result.get('actions', [])
            message = result.get('message', "I processed your request.")

            # 4. Save Actions to DB (if any)
            saved_actions = []
            for action in actions:
                # --- CRITICAL FIX: MAP GMAIL TO GOOGLE ---
                # The LLM might say "gmail", but your DB requires "google"
                if action.get('provider') == 'gmail': 
                    action['provider'] = 'google'
                
                # Check for Asana mapping too just in case
                if action.get('provider') == 'asana_api':
                    action['provider'] = 'asana'

                saved_id = self._save_pending_action(user_id, action)
                
                if saved_id:
                    action['id'] = saved_id # Attach the DB ID to the response object
                    saved_actions.append(action)
            
            print(f"✅ Response: '{message}' | Actions Created: {len(saved_actions)}")
            
            return {
                "message": message,
                "plan": saved_actions
            }
            
        except Exception as e:
            print(f"❌ Error in get_agent_response: {e}")
            return {
                "message": "I encountered an internal error while thinking. Please try again.",
                "plan": []
            }
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response expecting { message: str, actions: [] }"""
        try:
            # Clean markdown if present
            response = response.strip()
            if response.startswith('```'):
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            data = json.loads(response)
            
            # Normalization logic
            if not isinstance(data, dict):
                # Fallback if LLM returns just a list of actions
                if isinstance(data, list):
                    return {"message": "I've prepared the actions you requested:", "actions": data}
                # Fallback if LLM returns just a string (rare with format="json")
                return {"message": str(data), "actions": []}
                
            return {
                "message": data.get("message", "Done."),
                "actions": data.get("actions", [])
            }
        except Exception as e:
            print(f"Warning: JSON Parse Error: {e}")
            return {"message": "I couldn't understand the AI output.", "actions": []}
    
    def _build_hybrid_prompt(self, user_message: str, has_asana: bool, has_gmail: bool) -> str:
        """
        Builds a prompt that enforces a specific JSON structure.
        """
        
        available_tools = []
        if has_asana:
            available_tools.append("- create_asana_task (provider: 'asana'): Create a task. Params: name, notes")
        if has_gmail:
            available_tools.append("- send_gmail (provider: 'google'): Send email. Params: to, subject, body")
        
        tools_str = "\n".join(available_tools) if available_tools else "No tools connected."
        
        return f"""
        You are Gaprio, an intelligent AI assistant for enterprise work.
        
        USER SAYS: "{user_message}"
        
        AVAILABLE TOOLS:
        {tools_str}
        
        INSTRUCTIONS:
        1. If the user is just chatting (e.g., "Hi", "How are you", "Thanks"), reply naturally in the "message" field and keep "actions" empty.
        2. If the user wants a task done (email, asana), GENERATE the JSON object in "actions".
        3. If you generate actions, set "message" to something like "I have prepared the actions for you."
        4. ALWAYS return valid JSON.
        
        RESPONSE FORMAT:
        {{
            "message": "Your conversational reply here",
            "actions": [
                {{
                    "tool": "tool_name",
                    "provider": "google OR asana", 
                    "parameters": {{ "key": "value" }}
                }}
            ]
        }}
        
        Note: 'provider' must be exactly 'google' or 'asana'. Do not use 'gmail'.
        
        Generate JSON response now:
        """
    
    def _save_pending_action(self, user_id: int, action: Dict) -> Optional[int]:
        """Save action to pending actions table"""
        try:
            tool = action.get('tool', '')
            provider = action.get('provider', '')
            
            # Map tool to database action_type
            action_type = tool 
            if tool == 'create_asana_task': action_type = 'create_task'
            if tool == 'send_gmail': action_type = 'send_email'
            
            return db_manager.create_pending_action(
                user_id=user_id,
                provider=provider,
                action_type=action_type,
                draft_payload=action
            )
        except Exception as e:
            print(f"Error saving pending action: {e}")
            return None

    def get_pending_actions(self, user_id: int) -> List[Dict]:
        """Get pending actions for a user"""
        return db_manager.get_pending_actions(user_id)

    def approve_action(self, action_id: int) -> Dict:
        """Approve and execute a pending action"""
        try:
            print(f"⚡ Approving action {action_id}...")
            actions = db_manager.get_pending_actions()
            action = next((a for a in actions if a['id'] == action_id), None)
            
            if not action: return {"success": False, "error": "Action not found"}
            
            user_id = action['user_id']
            provider = action['provider']
            draft_payload = action.get('draft_payload', {})
            
            # Get Token
            token_data = db_manager.get_user_token(user_id, provider)
            if not token_data: return {"success": False, "error": f"No {provider} token found"}
            
            # Execute Action Logic
            result = None
            if provider == 'asana':
                asana_api = AsanaAPI(token_data['access_token'])
                # Handle different Asana tools
                if draft_payload.get('tool') == 'create_asana_task':
                    result = asana_api.create_task(draft_payload.get('parameters', {}))
            
            elif provider == 'google':
                from tools.google_tool import send_gmail
                # Handle different Google tools
                if draft_payload.get('tool') == 'send_gmail':
                    result = send_gmail(token_data['access_token'], draft_payload.get('parameters', {}))
                
            status = 'executed' if result and 'error' not in result else 'rejected'
            db_manager.update_action_status(action_id, status)
            
            return {"success": status == 'executed', "result": result}
        except Exception as e:
            print(f"Error executing action: {e}")
            return {"success": False, "error": str(e)}

# Create Global Instance
agent_brain = AgentBrain()

# Legacy function wrapper (keeps older imports working)
def get_agent_plan(user_id: int, user_message: str) -> List[Dict]:
    """Wrapper: Returns just the plan list for backward compatibility"""
    response = agent_brain.get_agent_response(user_id, user_message)
    return response.get('plan', [])