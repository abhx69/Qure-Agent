"""
run.py - Simple server runner (Fixed .env loading)
"""

import os
import sys
import time
from dotenv import load_dotenv
from pathlib import Path

# 👇 FIX: Explicitly find the .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def main():
    print("🚀 Starting Gaprio Agent Server")
    print("=" * 50)
    
    # Debug: Check if password is loaded (Don't print the actual password!)
    db_pass = os.getenv('DB_PASSWORD')
    if not db_pass:
        print("❌ ERROR: Could not read DB_PASSWORD from .env file.")
        print(f"   -> Looking for .env at: {env_path.absolute()}")
        print("   -> Make sure the file exists and contains DB_PASSWORD=...")
        return
    else:
        print("✅ .env file loaded successfully (Password found)")

    # Check database connection first
    try:
        import mysql.connector
        
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_name = os.getenv('DB_NAME', 'gapriomanagement')

        print(f"   Connecting to MySQL at {db_host} as {db_user}...")

        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name
        )
        conn.close()
        print(f"✅ Database: Connected to '{db_name}'")
    except Exception as e:
        print(f"❌ Database: Failed - {e}")
        print("   -> Ensure your MySQL server is running and the password is correct.")
        return
    
    # Check Ollama
    try:
        import requests
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        response = requests.get(ollama_url, timeout=2)
        print("✅ Ollama: Running")
    except:
        print("⚠️  Ollama: Not detected (AI features may be limited)")
    
    # Start server
    port = int(os.getenv('APP_PORT', 8000))
    print("\n🌐 Starting web server...")
    print(f"   Server will be available at: http://localhost:{port}")
    print("   Press Ctrl+C to stop\n")
    
    # Import and run
    try:
        import uvicorn
        from main import app
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")

if __name__ == "__main__":
    main()