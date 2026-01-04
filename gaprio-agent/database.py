"""
database.py - Connected to gapriomanagement
"""

import os
import mysql.connector
from typing import Dict, Optional, List
from dotenv import load_dotenv
from mysql.connector import Error
import json

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'gapriomanagement'),
            'raise_on_warnings': True,
            'buffered': True,
            'autocommit': True
        }
        self.connection = None
    
    def connect(self) -> bool:
        try:
            self.connection = mysql.connector.connect(**self.config)
            print(f"✅ AI Agent connected to REAL DB: {self.config['database']}")
            return True
        except Error as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def get_user_token(self, user_id: int, provider: str) -> Optional[Dict]:
        """Fetch tokens from the user_connections table"""
        try:
            cursor = self.connection.cursor(buffered=True, dictionary=True)
            
            # Using 'user_connections' as per your SQL schema
            query = """
                SELECT access_token, refresh_token, expires_at 
                FROM user_connections 
                WHERE user_id = %s AND provider = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """
            cursor.execute(query, (user_id, provider))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                # print(f"   🔑 Found {provider} token for User {user_id}")
                return result
            else:
                print(f"   ⚠️ No {provider} token found for User {user_id}")
                return None
                
        except Error as e:
            print(f"Error fetching token: {e}")
            return None

    def save_chat_message(self, user_id: int, role: str, content: str) -> Optional[int]:
        try:
            cursor = self.connection.cursor(buffered=True)
            query = "INSERT INTO agent_chat_logs (user_id, role, content) VALUES (%s, %s, %s)"
            cursor.execute(query, (user_id, role, content))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error saving chat log: {e}")
            return None

    def create_pending_action(self, user_id: int, provider: str, action_type: str, draft_payload: Dict) -> Optional[int]:
        try:
            cursor = self.connection.cursor(buffered=True)
            query = """
                INSERT INTO ai_pending_actions 
                (user_id, provider, action_type, draft_payload, status)
                VALUES (%s, %s, %s, %s, 'pending')
            """
            # Ensure payload is JSON string
            payload_json = json.dumps(draft_payload) if isinstance(draft_payload, dict) else draft_payload
            
            cursor.execute(query, (user_id, provider, action_type, payload_json))
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error creating pending action: {e}")
            return None

    def get_pending_actions(self, user_id: Optional[int] = None) -> List[Dict]:
        try:
            cursor = self.connection.cursor(buffered=True, dictionary=True)
            if user_id:
                query = "SELECT * FROM ai_pending_actions WHERE user_id = %s AND status = 'pending' ORDER BY created_at DESC"
                cursor.execute(query, (user_id,))
            else:
                query = "SELECT * FROM ai_pending_actions WHERE status = 'pending' ORDER BY created_at DESC"
                cursor.execute(query)
                
            actions = cursor.fetchall()
            
            # Parse JSON strings back to dicts
            for action in actions:
                if isinstance(action.get('draft_payload'), str):
                    try:
                        action['draft_payload'] = json.loads(action['draft_payload'])
                    except:
                        pass # Keep as string if parsing fails
            return actions
        except Error as e:
            print(f"Error fetching actions: {e}")
            return []

    def update_action_status(self, action_id: int, status: str):
        try:
            cursor = self.connection.cursor(buffered=True)
            if status == 'executed':
                query = "UPDATE ai_pending_actions SET status = %s, executed_at = NOW() WHERE id = %s"
            else:
                query = "UPDATE ai_pending_actions SET status = %s WHERE id = %s"
            cursor.execute(query, (status, action_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating action: {e}")
            return False

# Initialize and Connect
db_manager = DatabaseManager()