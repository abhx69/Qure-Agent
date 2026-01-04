# Gaprio Agent

## Setup Instructions

1. Copy `.env.example` to `.env` and fill in your values
2. Install dependencies: `pip install -r requirements.txt`
3. Setup database: `python setup_database.py`
4. Run server: `python main.py`

```mermaid
graph TB
    subgraph Frontend
        A[User Interface]
    end

    subgraph Backend
        B[FastAPI Server]
        C[Agent Brain]
    end

    subgraph AI
        D{Ollama LLM}
        I[Local LLM]
    end

    subgraph Integrations
        F[Asana API]
        G[Gmail API]
    end

    subgraph Database
        E[Database]
        H[MySQL Database]
    end

    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    E --> H
    D --> I

    style A fill:#4CAF50
    style C fill:#2196F3
    style H fill:#FF9800

