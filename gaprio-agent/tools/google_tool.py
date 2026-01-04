"""
tools/google_tool.py - Gmail API operations
"""

import requests
import base64
from email.mime.text import MIMEText
from typing import Dict

def send_gmail(access_token: str, email_data: Dict) -> Dict:
    """Send email using Gmail API"""
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Create email message
    message = MIMEText(email_data.get('body', ''))
    message['to'] = email_data.get('to', '')
    message['subject'] = email_data.get('subject', '')
    
    # Encode the message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    payload = {
        "raw": raw_message
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Gmail API Error: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {"error": str(e)}

def send_gmail_simple(access_token: str, to: str, subject: str, body: str) -> Dict:
    """Simplified email sending"""
    return send_gmail(access_token, {
        "to": to,
        "subject": subject,
        "body": body
    })