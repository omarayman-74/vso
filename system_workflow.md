# Chatbot System Workflow

This diagram describes the complete processing flow of the real estate chatbot, including security filtering, semantic intent classification, cross-validation, and post-processing.

```mermaid
graph TD
    User([User Message]) --> Safety[Guard Agent: Security Check]
    
    Safety -- Unsafe --> Reject[End: Security Block]
    Safety -- Safe --> Lang[Language Detection]
    
    Lang --> Intent[Pre-Classifier: Semantic Intent Detection]
    Intent --> Orch1[Orchestrator: Initial Routing & Execution]
    
    Orch1 --> Decide{Cross-Validation}
    
    Decide -- "Disagreement OR Low Confidence (<70%)" --> Retry[Re-invoke Orchestrator with Validation Context]
    Decide -- "Agreement & High Confidence" --> Post[Post-Processing]
    
    Retry --> Post
    
    subgraph "Specialist Agent Layer"
        SQL[SQL Search Agent]
        RAG[RAG Knowledge Agent]
        Chat[Chat Agent/Scope Guard]
    end
    
    Orch1 -.-> Specialist
    Retry -.-> Specialist
    
    Post --> ImageClean[Clean Image Markdown]
    ImageClean --> Carousel{New Results?}
    Carousel -- Yes --> InjectCarousel[Inject Property Carousel Data]
    Carousel -- No --> Detail{Detail Request?}
    
    InjectCarousel --> Final[Final Response Text]
    Detail -- Yes --> InjectDetail[Inject Unit Detail Layout]
    Detail -- No --> Final
    InjectDetail --> Final
    
    Final --> Log[Log to chat_log.txt]
    Log --> UserOutput([Response Sent to User])

    style Retry fill:#fff4dd,stroke:#d4a017
    style Safety fill:#ffdddd,stroke:#c0392b
    style Orch1 fill:#e1f5fe,stroke:#01579b
    style Decide fill:#f3e5f5,stroke:#4a148c
```

## Logic Breakdown

1.  **Security Guard**: Fast filtering to block malicious or harmful input.
2.  **Semantic Intent Pre-Classifier**: Uses a lightweight LLM call to predict if the user wants information (`rag`), search (`sql`), or general chat (`chat`).
3.  **Initial Orchestration**: The LangChain agent chooses a tool.
4.  **Cross-Validation (The "Check")**:
    *   If the Pre-Classifier and Orchestrator **disagree**, or if the pre-classifier's **confidence is low**, the system re-invokes the orchestrator with an explicit "Validation Required" prompt.
    *   This forces the LLM to rethink its routing decision before providing a final answer.
5.  **Post-Processing**:
    *   Cleans up forbidden image links/markdown.
    *   Detects if new units were searched and injects structured JSON for the frontend carousel.
    *   Detects if specific unit details were requested and injects the detailed view layout.
6.  **Scope Guard (In-Agent)**: Even within the specialists, strict real estate scope is enforced at the prompt level.
