# PPL 0.3 Enterprise Automation Example

```text
APP IncidentAutomation

MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    extraction: extraction-default
    max_retries: 2
    fallback: fallback-default

KNOWLEDGE ITOperations
    SOURCE runbooks
    SOURCE application_catalog
    SOURCE historical_incidents

MEMORY IncidentHistory
    KEY incident.id
    READ incidents
    WRITE outcomes

TOOL ServiceManagement
    ACTION create_ticket
    INPUT
        title: TEXT
        description: TEXT
        priority: TEXT
    OUTPUT
        ticket_id: ID

AGENT Analyzer
    INPUT incident
    POLICY EnterpriseDefault
    USE KNOWLEDGE ITOperations
    USE MEMORY IncidentHistory

    CLASSIFY incident.description AS
        ACCESS
        NETWORK
        DATABASE
        APPLICATION
        INFRASTRUCTURE
        OTHER

    EXTRACT
        root_cause: TEXT
        resolution: TEXT

    REASON
        determine whether this incident is repetitive
        OUTPUT:
            repetitive: BOOLEAN
            confidence: CONFIDENCE
            evidence: TEXT

WORKFLOW Main
    RECEIVE incident
    RUN Analyzer

    IF Analyzer.confidence < 0.85
        HUMAN_APPROVAL
            QUESTION:
                validate the analysis before continuing
            OPTIONS:
                APPROVE
                REJECT

    CALL ServiceManagement.create_ticket
        title = "Automation candidate"
        description = Analyzer.root_cause
        priority = incident.priority

    RETURN Analyzer.category
```

This file is a language-design example for 0.3. The reference runtime does not yet parse every 0.3 construct; implementation will follow the specification incrementally.
