"""PPL 0.3 runtime primitives: knowledge, memory, tools and human approval."""
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class KnowledgeSource:
    name: str
    documents: dict[str, str] = field(default_factory=dict)

    def retrieve(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        q = {w.lower() for w in query.split() if len(w) > 2}
        scored = []
        for source_id, text in self.documents.items():
            words = set(text.lower().split())
            score = len(q & words)
            if score:
                scored.append((score, source_id, text))
        scored.sort(reverse=True)
        return [{"source": sid, "text": text, "score": str(score)} for score, sid, text in scored[:limit]]

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

@dataclass
class ToolRegistry:
    actions: dict[str, ToolAction] = field(default_factory=dict)

    def register(self, name: str, handler: Callable[..., Any]) -> None:
        self.actions[name] = ToolAction(name, handler)

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self.actions:
            raise KeyError(f"Unknown tool action: {name}")
        return self.actions[name].handler(**kwargs)

@dataclass
class HumanDecision:
    execution_id: str
    question: str
    options: list[str]
    decision: str | None = None

class HumanApproval:
    def request(self, execution_id: str, question: str, options: list[str]) -> HumanDecision:
        return HumanDecision(execution_id, question, options)

    def resolve(self, decision: HumanDecision, value: str) -> HumanDecision:
        if value not in decision.options:
            raise ValueError(f"Invalid decision: {value}")
        decision.decision = value
        return decision
