"""
tools/asana_tool.py - Asana API operations
"""

import requests
import json
from typing import List, Dict, Optional

class AsanaAPI:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://app.asana.com/api/1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def fetch_workspaces(self) -> List[Dict]:
        """Fetch all workspaces"""
        url = f"{self.base_url}/workspaces"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                workspaces = response.json().get('data', [])
                return [{"id": w['gid'], "name": w['name']} for w in workspaces]
            return []
        except Exception as e:
            print(f"Asana workspaces error: {e}")
            return []
    
    def fetch_projects(self, workspace_id: Optional[str] = None) -> List[Dict]:
        """Fetch projects"""
        url = f"{self.base_url}/projects"
        params = {}
        
        if workspace_id:
            params['workspace'] = workspace_id
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                projects = response.json().get('data', [])
                return [{"id": p['gid'], "name": p['name']} for p in projects]
            return []
        except Exception as e:
            print(f"Asana projects error: {e}")
            return []
    
    def fetch_metadata(self) -> Dict:
        """Fetch comprehensive metadata"""
        return {
            "workspaces": self.fetch_workspaces(),
            "projects": self.fetch_projects()
        }
    
    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        url = f"{self.base_url}/tasks"
        
        payload = {
            "data": {
                "name": task_data.get('name', ''),
                "notes": task_data.get('notes', ''),
            }
        }
        
        # Add project if specified
        if 'project_id' in task_data and task_data['project_id']:
            payload["data"]["projects"] = [task_data['project_id']]
        
        # Add workspace if specified
        if 'workspace' in task_data:
            payload["data"]["workspace"] = task_data['workspace']
        
        # Add optional fields
        optional_fields = ['due_on', 'due_at', 'assignee', 'parent', 'memberships']
        for field in optional_fields:
            if field in task_data:
                payload["data"][field] = task_data[field]
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {
                    "error": f"API Error: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {"error": str(e)}
    
    def get_task(self, task_id: str) -> Dict:
        """Fetch a specific task"""
        url = f"{self.base_url}/tasks/{task_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.json() if response.status_code == 200 else {"error": "Task not found"}
        except Exception as e:
            return {"error": str(e)}

# Helper functions
def fetch_asana_metadata(access_token: str) -> List[Dict]:
    """Legacy function - fetches projects"""
    asana = AsanaAPI(access_token)
    return asana.fetch_projects()

def execute_asana_task(access_token: str, task_data: Dict) -> Dict:
    """Legacy function - creates task"""
    asana = AsanaAPI(access_token)
    return asana.create_task(task_data)