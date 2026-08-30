from .ai_gateway import ModelPolicy

BUILTIN_POLICIES = {
    "EnterpriseDefault": ModelPolicy(
        name="EnterpriseDefault",
        reasoning_model="reasoning-default",
        classification_model="classification-default",
        extraction_model="extraction-default",
        max_retries=1,
        fallback_model="fallback-default",
    ),
    "CostOptimized": ModelPolicy(
        name="CostOptimized",
        reasoning_model="fast-reasoning",
        classification_model="fast-classifier",
        extraction_model="fast-extractor",
        max_retries=1,
        fallback_model="fast-fallback",
    ),
}

def resolve_policy(name: str | None) -> ModelPolicy:
    if not name:
        return BUILTIN_POLICIES["EnterpriseDefault"]
    return BUILTIN_POLICIES.get(name, ModelPolicy(name=name))
