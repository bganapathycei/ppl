export const EXAMPLES = {
  hello_world: `APP HelloAI

INPUT request
    text: TEXT

AGENT Classifier

    INPUT request

    CLASSIFY request.text AS
        GREETING
        QUESTION
        OTHER

    OUTPUT
        category
        confidence

WORKFLOW Main

    RECEIVE request
    RUN Classifier
    RETURN Classifier.category
`,
  incident: `APP IncidentAdvisor

MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    extraction: extraction-default
    max_retries: 2
    fallback: fallback-default

INPUT incident
    description: TEXT
    application: TEXT
    priority: TEXT

AGENT Analyzer
    INPUT incident
    POLICY EnterpriseDefault

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
        determine whether the incident is repetitive
        OUTPUT:
            repetitive: BOOLEAN
            confidence: CONFIDENCE

    OUTPUT
        category: CLASSIFICATION
        root_cause: TEXT
        resolution: TEXT
        repetitive: BOOLEAN
        confidence: CONFIDENCE

AGENT AutomationAdvisor
    INPUT Analyzer
    POLICY EnterpriseDefault

    REASON
        determine whether this incident is a good candidate for automation
        consider:
            repetition
            resolution complexity
            human intervention
            business risk
        OUTPUT:
            score: NUMBER
            rationale: TEXT
            confidence: CONFIDENCE

    OUTPUT
        score: NUMBER
        rationale: TEXT
        confidence: CONFIDENCE

WORKFLOW Main
    RECEIVE incident
    RUN Analyzer
    RUN AutomationAdvisor

    IF AutomationAdvisor.score >= 80
        RETURN "AUTOMATE"
    ELSE IF AutomationAdvisor.score >= 50
        RETURN "PARTIALLY_AUTOMATE"
    ELSE
        RETURN "KEEP_HUMAN"
`,
  governed_change: `APP GovernedChange

INPUT change
    description: TEXT
    environment: TEXT
    risk: NUMBER

GUARD ProductionSafety
    NEVER execute production changes
        without authorization

AUTHORIZATION production_change
    REQUIRES production.write

BUDGET
    max_cost: 0.10
    max_latency: 5000ms
    max_steps: 10

AGENT RiskAnalyzer

    INPUT change

    REASON
        determine whether the proposed change is safe
        to execute automatically
        OUTPUT:
            safe: BOOLEAN
            confidence: CONFIDENCE
            rationale: TEXT

    OUTPUT
        safe: BOOLEAN
        confidence: CONFIDENCE
        rationale: TEXT

WORKFLOW Main

    RECEIVE change
    RUN RiskAnalyzer

    IF RiskAnalyzer.confidence < 0.90
        HUMAN_APPROVAL

    ELSE IF RiskAnalyzer.safe == TRUE
        RETURN "APPROVED"

    ELSE
        RETURN "REJECTED"
`,
  enterprise_automation: `APP IncidentAutomation

MODEL_POLICY EnterpriseDefault
    reasoning: reasoning-default
    classification: classification-default
    extraction: extraction-default
    max_retries: 2
    fallback: fallback-default

INPUT incident
    description: TEXT
    application: TEXT
    priority: TEXT
    id: TEXT

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

    OUTPUT
        category: CLASSIFICATION
        root_cause: TEXT
        resolution: TEXT
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
`,
};

export async function loadExampleSource(name) {
  try {
    const response = await fetch(`templates/${name}.ppl`);
    if (response.ok) return await response.text();
  } catch {
    // file:// or missing template file
  }
  return EXAMPLES[name] || "";
}
