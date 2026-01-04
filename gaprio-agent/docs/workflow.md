# Gaprio Agent Workflow Documentation

##  Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [User Flow](#user-flow)
4. [AI Processing Flow](#ai-processing-flow)
5. [Tick Mark Approval System](#tick-mark-approval-system)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Error Handling](#error-handling)
9. [Security Flow](#security-flow)
10. [Deployment Flow](#deployment-flow)

---

##  Overview

Gaprio Agent is an AI-powered productivity assistant that connects with Asana and Gmail to automate tasks through natural language commands. The system follows a **human-in-the-loop** approach where AI suggests actions but requires human approval before execution.

##  System Architecture

\\\mermaid
graph TB
    A[User Interface] --> B[FastAPI Server]
    B --> C[Agent Brain]
    C --> D{Ollama LLM}
    C --> E[Database]
    C --> F[Asana API]
    C --> G[Gmail API]
    
    E --> H[MySQL Database]
    D --> I[Local LLM]
    
    style A fill:#4CAF50
    style C fill:#2196F3
    style H fill:#FF9800
\\\

**Components:**
- **FastAPI Server**: REST API endpoints
- **Agent Brain**: Core AI decision-making logic
- **Ollama LLM**: Local language model (Llama 3)
- **MySQL Database**: Stores users, tokens, and pending actions
- **API Integrations**: Asana and Gmail

---

##  User Flow

### 1. Initial Setup
\\\
User  OAuth Login  Token Storage  Ready to use
       Google          Database       Can send commands
       Asana
\\\

### 2. Normal Usage Flow
\\\
1. User sends message: "Create task for website review"
2. AI analyzes and creates draft action
3. System shows: "Task created  Approve?"
4. User reviews and clicks 
5. System executes via Asana API
6. User sees: " Task created successfully!"
\\\

### 3. Multi-action Flow
\\\
User: "Create task and email team"
 AI: Creates 2 draft actions
 User: Approves both 
 System: Executes sequentially
 Result: Task created + Email sent
\\\

---

##  AI Processing Flow

### Step 1: Message Analysis
\\\python
Input: "Create task for Q4 planning and email results"
Processing:
1. Intent Detection: ["create_task", "send_email"]
2. Entity Extraction: 
   - Task: "Q4 planning"
   - Email: "results"
3. Tool Selection:
   - create_task  Asana
   - send_email  Gmail
\\\

### Step 2: Context Gathering
\\\python
1. Check user tokens in database
2. Fetch recent chat history
3. Get available Asana projects
4. Check email contacts (if available)
\\\

### Step 3: Action Generation
\\\python
# LLM Prompt Example
"""
User: "Create task for Q4 planning"
Tools: Asana (create_task), Gmail (send_email)
Context: User has 3 Asana projects

Generate JSON action plan:
[
  {
    "tool": "create_asana_task",
    "provider": "asana",
    "parameters": {
      "name": "Q4 Planning",
      "notes": "Plan for Q4 objectives",
      "project_id": "12345"
    }
  }
]
"""
\\\

### Step 4: Response Formatting
\\\json
{
  "status": "pending_approval",
  "actions": [
    {
      "id": 101,
      "type": "create_task",
      "tool": "asana",
      "summary": "Create task: Q4 Planning",
      "parameters": {...}
    }
  ],
  "message": "I'll create a task for Q4 planning.  Approve?"
}
\\\

---

##  Tick Mark Approval System

### Core Concept
Every AI-generated action requires explicit user approval before execution. This ensures safety and control.

### Workflow
\\\
1. AI creates draft  Status: "pending"
2. Stored in: ai_pending_actions table
3. User interface shows pending actions
4. User can:  Approve,  Reject,  Edit
5. On approval  Execute  Status: "executed"
6. On rejection  Status: "rejected"
\\\

### Database State Flow
\\\sql
-- Initial creation
INSERT INTO ai_pending_actions 
VALUES (..., 'pending', NOW(), NULL);

-- User approves
UPDATE ai_pending_actions 
SET status = 'approved', executed_at = NOW()
WHERE id = 101;

-- Execution completes
UPDATE ai_pending_actions 
SET status = 'executed'
WHERE id = 101;
\\\

### User Interface States
\\\

 PENDING ACTIONS (2)                 

 1. Create task: Website Review      
    [ Approve] [ Reject] [ Edit] 
                                     
 2. Send email: Project Update       
    [ Approve] [ Reject] [ Edit] 

\\\

---

##  Database Schema

### Core Tables
\\\sql
-- 1. Users
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. OAuth Tokens
CREATE TABLE user_connections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    provider ENUM('google', 'asana'),
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP
);

-- 3. Chat History (AI Memory)
CREATE TABLE agent_chat_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    role ENUM('user', 'assistant'),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tick Mark System
CREATE TABLE ai_pending_actions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    provider ENUM('google', 'asana'),
    action_type VARCHAR(50),
    draft_payload JSON,
    status ENUM('pending', 'approved', 'rejected', 'executed'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP NULL
);
\\\

### Data Flow Example
\\\sql
-- User sends message
INSERT INTO agent_chat_logs VALUES (1, 1, 'user', 'Create task...', NOW());

-- AI creates draft action
INSERT INTO ai_pending_actions VALUES (
    1, 1, 'asana', 'create_task',
    '{"tool": "create_asana_task", "name": "Task"}',
    'pending', NOW(), NULL
);

-- User approves
UPDATE ai_pending_actions SET status = 'approved' WHERE id = 1;

-- Action executes
UPDATE ai_pending_actions 
SET status = 'executed', executed_at = NOW() 
WHERE id = 1;
\\\

---

##  API Endpoints Flow

### Authentication Flow
\\\
POST /auth/{provider}        # Start OAuth flow
GET  /auth/{provider}/callback  # OAuth callback
POST /auth/refresh          # Refresh expired tokens
\\\

### Core Agent Flow
\\\
1. POST /ask-agent
    Input: {user_id, message}
    Output: {status: "pending", actions: [...], requires_approval: true}

2. GET /pending-actions/{user_id}
    Get all pending actions
    Output: {count: N, actions: [...]}

3. POST /approve-action
    Input: {user_id, action_id}
    Output: {status: "success", result: {...}}

4. POST /reject-action
    Input: {user_id, action_id}
    Output: {status: "success"}
\\\

### Health & Monitoring
\\\
GET  /health                # System status
GET  /metrics               # Performance metrics
GET  /logs                  # System logs
\\\

### Example API Sequence
\\\ash
# 1. Send message
curl -X POST http://localhost:8000/ask-agent \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "message": "Create task"}'

# 2. Check pending actions
curl http://localhost:8000/pending-actions/1

# 3. Approve action
curl -X POST http://localhost:8000/approve-action \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "action_id": 101}'
\\\

---

##  Error Handling Flow

### Error Types & Recovery
\\\python
# 1. LLM Errors
Error: LLM timeout/no response
Recovery: 
  - Retry with shorter prompt
  - Fallback to rule-based parsing
  - Return: "I'm having trouble. Can you rephrase?"

# 2. API Errors (Asana/Gmail)
Error: Invalid/expired token
Recovery:
  - Attempt token refresh
  - If fails: "Please reconnect your Asana account"

Error: Rate limiting
Recovery:
  - Queue request
  - Exponential backoff
  - Notify user of delay

# 3. Database Errors
Error: Connection lost
Recovery:
  - Retry connection
  - Use in-memory cache temporarily
  - Log error for admin

# 4. User Input Errors
Error: Ambiguous request
Recovery:
  - Ask clarifying questions
  - "Did you mean create a task or send email?"
\\\

### Error Response Format
\\\json
{
  "status": "error",
  "error_type": "api_error",
  "message": "Asana API rate limit exceeded",
  "suggestion": "Try again in 60 seconds",
  "action_id": 101,  # If applicable
  "retryable": true
}
\\\

### Logging Strategy
\\\python
# Log levels
DEBUG: Detailed processing steps
INFO: User actions, AI decisions
WARNING: Recoverable errors
ERROR: Critical failures
\\\

---

##  Security Flow

### Authentication Flow
\\\
1. User clicks "Connect Asana"
2. Redirect to Asana OAuth
3. User authorizes app
4. Asana returns auth code
5. Server exchanges code for tokens
6. Tokens stored encrypted in database
\\\

### Token Management
\\\python
# Token refresh flow
def check_token_expiry(token):
    if token.expires_at < now():
        # Refresh token
        new_token = refresh_oauth_token(token.refresh_token)
        update_database(new_token)
    return token.access_token
\\\

### API Security
\\\
Request  API Gateway  Authentication  Authorization  Processing
            Rate limiting    JWT verification   User permissions
\\\

### Data Protection
\\\python
# Sensitive data handling
1. Tokens: Encrypted at rest
2. Database: SSL connections
3. Logs: No sensitive data
4. API Keys: Environment variables only
\\\

---

##  Deployment Flow

### Development Setup
\\\ash
# 1. Clone repository
git clone https://github.com/yourusername/gaprio-agent.git

# 2. Setup environment
cp .env.example .env
# Edit .env with your values

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup database
python setup_database.py

# 5. Start Ollama
ollama serve

# 6. Run server
python main.py
\\\

### Production Deployment
\\\yaml
# Docker Compose Example
version: '3.8'
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DB_HOST=mysql
      - DB_PASSWORD=\
    depends_on:
      - mysql
  
  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=\
      - MYSQL_DATABASE=gaprio_agent
    volumes:
      - mysql_data:/var/lib/mysql

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
\\\

### CI/CD Pipeline
\\\
Push to GitHub  Tests  Build Docker  Deploy to Server  Health Check
                  Unit tests          Staging first     Auto-rollback if fails
                  Integration tests
\\\

---

##  Monitoring & Maintenance

### Key Metrics
\\\
1. Performance:
   - API response time (< 2s)
   - LLM processing time (< 10s)
   - Database query time (< 100ms)

2. Usage:
   - Active users
   - Actions created/approved/rejected
   - Most used commands

3. Errors:
   - Error rate (< 1%)
   - Common error types
   - Recovery success rate
\\\

### Daily Operations
\\\python
# 1. Check system health
GET /health  Should return {"status": "healthy"}

# 2. Monitor logs
tail -f logs/app.log | grep -E "(ERROR|WARNING)"

# 3. Check database
SELECT COUNT(*) FROM ai_pending_actions WHERE status = 'pending';

# 4. Token expiry check
SELECT COUNT(*) FROM user_connections 
WHERE expires_at < NOW() + INTERVAL 1 DAY;
\\\

### Backup Strategy
\\\ash
# Daily database backup
mysqldump -u root -p gaprio_agent_dev > backup_\.sql

# Backup configuration
cp .env backup/env_backup_\

# Rotate backups (keep 7 days)
find ./backup -name "*.sql" -mtime +7 -delete
\\\

---

##  Update & Migration Flow

### Database Migrations
\\\sql
-- Example migration: Add new column
ALTER TABLE ai_pending_actions 
ADD COLUMN error_message TEXT AFTER status;

-- Version tracking
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\\\

### Code Updates
\\\
1. Create feature branch
2. Implement changes
3. Update tests
4. Run test suite
5. Create migration scripts
6. Deploy to staging
7. Test in staging
8. Deploy to production
9. Run migrations
10. Verify functionality
\\\

### Breaking Changes
\\\python
# API versioning for breaking changes
# Version in URL: /v1/ask-agent, /v2/ask-agent

# Deprecation process:
1. Announce deprecation (90 days notice)
2. Support both versions
3. Log usage of old version
4. Remove old version after cutoff
\\\

---

##  Success Criteria

### Technical Metrics
- [ ] API availability: 99.9%
- [ ] Response time: < 2 seconds
- [ ] Error rate: < 1%
- [ ] Token refresh success: > 95%

### User Experience
- [ ] Action approval rate: > 80%
- [ ] User satisfaction: > 4/5 stars
- [ ] Daily active users: Growing
- [ ] Feature adoption: Increasing

### Business Goals
- [ ] Time saved per user: > 30 min/day
- [ ] Task completion rate: Increased
- [ ] User retention: > 70% monthly
- [ ] Positive feedback: > 80%

---

##  Support & Troubleshooting

### Common Issues & Solutions
\\\
Issue: "AI not understanding my request"
Solution: Rephrase more specifically
Example: Instead of "Do the thing" use "Create a task for website review"

Issue: "Action not executing"
Solution: Check token status in settings
Fix: Reconnect Asana/Google account

Issue: "Slow response"
Solution: Check Ollama is running
Fix: Restart Ollama: ollama serve
\\\

### Debug Mode
\\\ash
# Enable verbose logging
export DEBUG=True
python main.py

# Check logs
tail -f app.log

# Test database connection
python -c "from database import db; print(db.connect())"
\\\

---

##  Future Enhancements

### Phase 2: Enhanced Features
1. **Multi-step workflows**: "Plan, execute, and report on project"
2. **Calendar integration**: Schedule meetings automatically
3. **File handling**: Attach files to tasks/emails
4. **Team collaboration**: Multi-user task assignments

### Phase 3: Advanced AI
1. **Learning from corrections**: Improve based on user edits
2. **Proactive suggestions**: "You usually create tasks on Monday"
3. **Context awareness**: Remember project preferences
4. **Multi-modal input**: Voice commands, image analysis

### Phase 4: Scaling
1. **Multi-tenant support**: Teams & organizations
2. **Plugin architecture**: Add new tools easily
3. **Mobile apps**: iOS & Android
4. **Enterprise features**: SSO, audit logs, compliance

---

##  Checklist for New Features

When adding new features:
- [ ] Update this workflow document
- [ ] Add database migrations
- [ ] Create API endpoints
- [ ] Update Agent Brain logic
- [ ] Add error handling
- [ ] Write tests
- [ ] Update documentation
- [ ] Train support team

---

**Last Updated**: 2024-12-28  
**Version**: 1.0.0  
**Maintainer**: Gaprio Team
