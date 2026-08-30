from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class KnowledgeSource:
    name: str
    documents: dict[str, str] = field(default_factory=dict)

    def retrieve(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        tokens = {t.lower() for t in query.split() if len(t) > 2}
        ranked = []
        for source_id, text in self.documents.items():
            score = len(tokens & set(text.lower().split()))
            if score:
                ranked.append((score, source_id, text))
        ranked.sort(key=lambda x: (-x[0], x[1]))
        return [{"source": sid, "text": text, "score": score} for score, sid, text in ranked[:limit]]

@dataclass
class MemoryStore:
    name: str
    records: dict[str, Any] = field(default_factory=dict)

    def read(self, key: str) -> Any:
        return self.records.get(key)

    def write(self, key: str, value: Any) -> None:
        self.records[key] = value

@dataclass
class ToolAction:
    name: str
    handler: Callable[..., Any]

class ToolRegistry:
    def __init__(self) -> None:
        self.actions: dict[str, ToolAction] = {}

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        self.actions[name] = ToolAction(name, handler)

    def call(self, name: str, **kwargs: Any) -> Any:
        action = self.actions.get(name)
        if not action:
            raise KeyError(f"Unknown tool action: {name}")
        return action.handler(**kwargs)

@dataclass
class HumanDecision:
    execution_id: str
    question: str
    options: list[str]
    status: str = "WAITING_FOR_HUMAN"
    decision: str | None = None

class HumanApproval:
    def request(self, execution_id: str, question: str, options: list[str]) -> HumanDecision:
        if not options:
            raise ValueError("Human approval requires at least one option")
        return HumanDecision(execution_id, question, options)

    def resolve(self, request: HumanDecision, decision: str) -> HumanDecision:
        if decision not in request.options:
            raise ValueError(f"Invalid decision '{decision}'. Options: {request.options}")
        request.decision = decision
        request.status = "RESUMED"
        return request

def build_context(knowledge: list[KnowledgeSource], memory: MemoryStore | None, query: str) -> dict[str, Any]:
    retrieved = []
    for source in knowledge:
        retrieved.extend(source.retrieve(query))
    return {"knowledge": retrieved, "memory": memory.records.copy() if memory else {}}
