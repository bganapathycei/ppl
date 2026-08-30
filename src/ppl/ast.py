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
class AgentDecl:
    name: str
    input_name: str | None = None
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

@dataclass
class Condition:
    left: str
    operator: str
    right: Any

@dataclass
class IfStep:
    condition: Condition
    then_steps: list[Any] = field(default_factory=list)
    else_if: list[tuple[Condition, list[Any]]] = field(default_factory=list)
    else_steps: list[Any] = field(default_factory=list)

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
    inputs: list[InputDecl] = field(default_factory=list)
    model_policies: list[ModelPolicyDecl] = field(default_factory=list)
    agents: list[AgentDecl] = field(default_factory=list)
    workflows: list[WorkflowDecl] = field(default_factory=list)
