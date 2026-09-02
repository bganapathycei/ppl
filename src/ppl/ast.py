from dataclasses import dataclass, field
from typing import Any


@dataclass
class InputField:
    name: str
    type_name: str


@dataclass
class InputDecl:
    name: str
    fields: list[InputField]


@dataclass
class ClassifyOp:
    target: str
    categories: list[str]
    schema: dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractOp:
    fields: list[str]
    schema: dict[str, str] = field(default_factory=dict)


@dataclass
class ReasonOp:
    instruction: str
    consider: list[str] = field(default_factory=list)
    schema: dict[str, str] = field(default_factory=dict)


@dataclass
class ModelPolicyDecl:
    name: str
    reason_model: str = "reasoning-default"
    classify_model: str = "classification-default"
    extract_model: str = "extraction-default"
    max_retries: int = 1
    fallback_model: str = "fallback-default"


@dataclass
class GuardDecl:
    name: str
    rules: list[str] = field(default_factory=list)


@dataclass
class AuthorizationDecl:
    name: str
    requires: str | None = None


@dataclass
class BudgetDecl:
    max_cost: float | None = None
    max_latency: str | None = None
    max_steps: int | None = None


@dataclass
class EnvironmentDecl:
    name: str
    body: list[str] = field(default_factory=list)


@dataclass
class KnowledgeDecl:
    name: str
    sources: list[str] = field(default_factory=list)


@dataclass
class MemoryDecl:
    name: str
    key: str | None = None
    body: list[str] = field(default_factory=list)


@dataclass
class ToolDecl:
    name: str
    actions: list[str] = field(default_factory=list)
    body: list[str] = field(default_factory=list)


@dataclass
class AgentDecl:
    name: str
    input_name: str | None = None
    policy: str | None = None
    knowledge: list[str] = field(default_factory=list)
    memory: list[str] = field(default_factory=list)
    operations: list[Any] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)


@dataclass
class ReceiveStep:
    name: str


@dataclass
class RunStep:
    name: str


@dataclass
class ReturnStep:
    value: Any
    literal: bool = False


@dataclass
class Condition:
    left: str
    operator: str
    right: Any


@dataclass
class LetStep:
    name: str
    expr: str


@dataclass
class PrintStep:
    expr: str


@dataclass
class ReadStep:
    path: str
    var: str


@dataclass
class WriteStep:
    path: str
    expr: str


@dataclass
class ForStep:
    item: str
    source: str
    body: list[Any] = field(default_factory=list)


@dataclass
class WhileStep:
    condition: str
    body: list[Any] = field(default_factory=list)


@dataclass
class PromptDecl:
    name: str
    body: list[str] = field(default_factory=list)


@dataclass
class PromptUseOp:
    template: str
    bindings: dict[str, str] = field(default_factory=dict)


@dataclass
class ImportDecl:
    module: str


@dataclass
class IfStep:
    condition: Condition | str
    then_steps: list[Any] = field(default_factory=list)
    else_if: list[tuple[Condition | str, list[Any]]] = field(default_factory=list)
    else_steps: list[Any] = field(default_factory=list)


@dataclass
class HumanApprovalStep:
    question: str | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class ParallelStep:
    steps: list[Any] = field(default_factory=list)


@dataclass
class JoinStep:
    names: list[str] = field(default_factory=list)


@dataclass
class WaitStep:
    condition: str = ""


@dataclass
class CheckpointStep:
    name: str = ""


@dataclass
class CallStep:
    target: str
    args: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowDecl:
    name: str
    steps: list[Any] = field(default_factory=list)


@dataclass
class AppDecl:
    name: str


@dataclass
class Program:
    app: AppDecl | None = None
    imports: list[ImportDecl] = field(default_factory=list)
    inputs: list[InputDecl] = field(default_factory=list)
    prompts: list[PromptDecl] = field(default_factory=list)
    model_policies: list[ModelPolicyDecl] = field(default_factory=list)
    guards: list[GuardDecl] = field(default_factory=list)
    authorizations: list[AuthorizationDecl] = field(default_factory=list)
    budgets: list[BudgetDecl] = field(default_factory=list)
    environments: list[EnvironmentDecl] = field(default_factory=list)
    knowledge: list[KnowledgeDecl] = field(default_factory=list)
    memories: list[MemoryDecl] = field(default_factory=list)
    tools: list[ToolDecl] = field(default_factory=list)
    agents: list[AgentDecl] = field(default_factory=list)
    workflows: list[WorkflowDecl] = field(default_factory=list)
