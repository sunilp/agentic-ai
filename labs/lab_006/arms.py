"""Lab-006 arms: a factorial ablation of Lab-001's router-versus-hierarchy comparison.

Lab-001 compared a rule-based router against a three-agent hierarchy and the hierarchy
scored higher. The two systems differ in two ways at once, so the result cannot say
which difference produced the gap:

  classification   a deterministic keyword switch, or a model call
  answer attempts  one, or a verifier that can trigger a re-answer

`retry_confound.py` in Lab-001 bounded the second factor from the committed records and
found it sufficient on its own to explain the whole gap. Bounding is not measuring. This
lab varies the two factors independently.

Everything else is imported from Lab-001 unchanged: the dataset, the agent prompts, the
tool registry, the verifier, the rubric and the judge. If any of those differed, the new
arms would not be comparable to the originals, and the originals are re-run here rather
than copied so that every number comes from one session.

    rule classify + 1 answer                  router            (replicates Lab-001)
    rule classify + 1 unconditional re-answer router_retry      <- the isolating arm
    rule classify + verifier-gated re-answer  router_verified
    LLM classify  + 1 answer                  hier_noverify
    LLM classify  + verifier-gated re-answer  hierarchy         (replicates Lab-001)
"""
from __future__ import annotations

from labs.lab_001.systems import (
    _AGENT_SYSTEM,
    _aggregate,
    _answer_with_tools,
    _classify_llm,
    _verify_llm,
    StepRecord,
    SystemResult,
    ToolRegistry,
    rule_classify,
)
from src.shared.model_client import ModelClient

ARMS = ("router", "router_retry", "router_verified", "hier_noverify", "hierarchy")

# The re-answer prompt is Lab-001's, word for word. The unconditional-retry arm has no
# verifier, so nothing "flagged" its answer; the wording is kept identical anyway,
# because changing it would confound the comparison with a prompt difference.
_FOLLOWUP = (
    "{query}\n\nA reviewer flagged the previous answer. Re-answer the question "
    "directly using the knowledge base."
)


async def _classify(client: ModelClient, query: str, use_model: bool):
    """Returns (category, steps). The first factor."""
    if not use_model:
        return rule_classify(query), []
    category, step = await _classify_llm(client, query)
    return category, [step]


async def run_arm(
    arm: str, client: ModelClient, query: str, query_id: str, category_true: str,
    max_rounds: int = 2,
) -> SystemResult:
    use_model_classify = arm in ("hier_noverify", "hierarchy")
    verified = arm in ("router_verified", "hierarchy")
    unconditional_retry = arm == "router_retry"

    registry = ToolRegistry()
    steps: list[StepRecord] = []

    category, clf_steps = await _classify(client, query, use_model_classify)
    steps.extend(clf_steps)

    answer, worker_steps = await _answer_with_tools(
        client, _AGENT_SYSTEM[category], query, category, registry, registry.schemas
    )
    steps.extend(worker_steps)

    verifier_passed = None
    retried = False

    if unconditional_retry:
        # Exactly one extra answer attempt, no verifier, no gate on whether it was
        # needed. This is the arm that isolates the attempt from the verification.
        retried = True
        answer, redo_steps = await _answer_with_tools(
            client, _AGENT_SYSTEM[category], _FOLLOWUP.format(query=query),
            category, registry, registry.schemas,
        )
        steps.extend(redo_steps)

    elif verified:
        verifier_passed = False
        rounds = 0
        while rounds < max_rounds:
            ok, ver_step = await _verify_llm(client, query, answer)
            steps.append(ver_step)
            rounds += 1
            if ok:
                verifier_passed = True
                break
            retried = True
            answer, redo_steps = await _answer_with_tools(
                client, _AGENT_SYSTEM[category], _FOLLOWUP.format(query=query),
                category, registry, registry.schemas,
            )
            steps.extend(redo_steps)

    result = SystemResult(
        system=arm,
        query_id=query_id,
        category_true=category_true,
        category_used=category,
        answer=answer,
        steps=steps,
        flags={
            "misroute": category != category_true,
            "model_classify": use_model_classify,
            "verified": verified,
            "retried": retried,
            "verifier_passed": verifier_passed,
        },
    )
    _aggregate(result)
    return result
