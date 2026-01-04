# Qure-Agent

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

