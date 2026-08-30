# PPL 0.3 Enterprise Automation Example

> Historical snapshot of the 0.3 program text. The runnable source is [`enterprise_automation.ppl`](enterprise_automation.ppl). Command → input → output: [`docs/EXAMPLES.md`](../docs/EXAMPLES.md) §4. Onboarding: [`docs/GETTING_STARTED.md`](../docs/GETTING_STARTED.md).

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

This example is executable as `examples/enterprise_automation.ppl` with sample documents under `examples/knowledge/`.

