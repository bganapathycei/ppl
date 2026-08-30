# PPL 0.5 Tutorial

## Lesson 1: classify text

```text
APP ClassifierDemo
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
```

## Lesson 2: add reasoning

```text
AGENT Advisor
    INPUT request
    REASON
        determine the best next action
        OUTPUT:
            action: TEXT
            confidence: CONFIDENCE
```

## Lesson 3: add governance

```text
GUARD SensitiveAction
    NEVER execute sensitive actions
        without authorization

BUDGET
    max_cost: 0.10
    max_steps: 20
```

## Lesson 4: combine capabilities

Use the pattern:

```text
INPUT
 -> KNOWLEDGE / MEMORY
 -> AGENT
 -> TOOL
 -> GUARD
 -> HUMAN_APPROVAL when required
 -> OUTPUT
```

Start with read-only recommendations. Add write-capable tools only after tests and evaluations are in place.
