# DevOps Incident Analysis Suite — Workflow

View this file in **GitHub**, **VS Code** (Markdown preview), or [Mermaid Live Editor](https://mermaid.live) to render the diagrams.

---

## High-level flow

```mermaid
flowchart TB
    subgraph Input
        UI[Streamlit UI]
        API[FastAPI /upload, /analyze]
        UI --> Raw[Raw log content]
        API --> Raw
    end

    subgraph Pipeline["LangGraph pipeline"]
        direction TB
        Parse[Parse logs]
        Classify[Classify issues]
        Remediate[Find remediations]
        Cookbook[Generate cookbook]
        Parse --> Classify --> Remediate --> Cookbook
    end

    subgraph KB["Knowledge base"]
        RAG[(Remediation KB\nChromaDB / in-memory)]
    end

    subgraph Routing["Conditional routing"]
        Route1{CRITICAL / HIGH / MEDIUM?}
        NotifySlack[Notify Slack]
        Route2{CRITICAL?}
        CreateJira[Create JIRA ticket]
        Cookbook --> Route1
        Route1 -->|Yes| NotifySlack
        Route1 -->|No, LOW only| End1([End])
        NotifySlack --> Route2
        Route2 -->|Yes| CreateJira
        Route2 -->|No| End2([End])
        CreateJira --> End3([End])
    end

    Raw --> Parse
    RAG -.->|RAG search| Remediate
```

## Detailed agent workflow

```mermaid
flowchart LR
    subgraph Step1["1. Parse"]
        A[Log Parser]
        A --> |LogEntry[]| B[Structured entries]
    end

    subgraph Step2["2. Classify"]
        C[Log Classifier Agent]
        C --> |ClassifiedIssue[]| D[Category, severity, services]
    end

    subgraph Step3["3. Remediate"]
        E[Remediation Agent]
        KB[(Runbooks KB)]
        E --> |RemediationPlan[]| F[Steps, time estimate]
        KB --> E
    end

    subgraph Step4["4. Cookbook"]
        G[Cookbook Synthesizer]
        G --> |Markdown| H[Actionable runbook]
    end

    subgraph Step5["5. Notify"]
        I[Slack Notifier]
        J[JIRA Agent]
        I --> |#incidents-*| K[Slack]
        J --> |Ticket / comment| L[JIRA]
    end

    B --> C
    D --> E
    F --> G
    H --> I
    H --> J
```

## State flow (LangGraph)

```mermaid
stateDiagram-v2
    [*] --> parse_logs: raw_logs
    parse_logs --> classify_issues: parsed_entries
    classify_issues --> find_remediations: classified_issues
    find_remediations --> generate_cookbook: remediations
    generate_cookbook --> notify_slack: cookbook (if CRITICAL/HIGH/MEDIUM)
    generate_cookbook --> [*]: (if LOW only)
    notify_slack --> create_jira: (if CRITICAL)
    notify_slack --> [*]: (if not CRITICAL)
    create_jira --> [*]
```

## Components overview

| Component | Role |
|-----------|------|
| **Log Parser** | Detects format (JSON, syslog, Apache, etc.), extracts timestamp, severity, service, message, stack trace. |
| **Log Classifier Agent** | LLM-based: categories (database, network, application, infrastructure), severity (CRITICAL/HIGH/MEDIUM/LOW). |
| **Remediation Agent** | RAG over runbooks KB → maps each issue to steps and time estimate. |
| **Cookbook Synthesizer** | Produces one markdown incident response cookbook. |
| **Slack Notifier** | Block Kit message; channel by severity (#incidents-critical, #incidents-high, #incidents-low). |
| **JIRA Agent** | Creates or comments on ticket for CRITICAL; duplicate detection. |
