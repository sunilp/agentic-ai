#!/usr/bin/env python3
"""Eval dataset loader and validator for the memory agent.

Loads each YAML eval dataset, validates its structure, and prints
a summary. This is not a full agent runner -- it confirms that the
datasets are well-formed and ready for integration with the agent
evaluation pipeline.
"""

import sys
from pathlib import Path

import yaml


EVAL_DIR = Path(__file__).resolve().parent


def load_yaml(filename: str) -> dict:
    """Load a YAML file from the eval directory."""
    filepath = EVAL_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Eval dataset not found: {filepath}")
    with open(filepath, "r") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty or invalid YAML: {filepath}")
    return data


def run_multiturn_eval() -> None:
    """Load and validate the multi-turn conversation dataset."""
    data = load_yaml("test_queries_multiturn.yaml")
    sequences = data.get("sequences", [])
    print(f"[multiturn]     Loaded {len(sequences)} sequences")
    for seq in sequences:
        assert "id" in seq, f"Missing 'id' in sequence: {seq}"
        assert "turns" in seq, f"Missing 'turns' in sequence: {seq['id']}"
        assert "expected_answer" in seq, f"Missing 'expected_answer' in: {seq['id']}"
        assert "critical_turn" in seq, f"Missing 'critical_turn' in: {seq['id']}"
        print(f"  - {seq['id']}: {len(seq['turns'])} turns, "
              f"critical_turn={seq['critical_turn']}")


def run_learning_eval() -> None:
    """Load and validate the repeated-mistake learning dataset."""
    data = load_yaml("test_queries_learning.yaml")
    scenarios = data.get("scenarios", [])
    print(f"[learning]      Loaded {len(scenarios)} scenarios")
    for sc in scenarios:
        assert "id" in sc, f"Missing 'id' in scenario: {sc}"
        assert "wrong_source" in sc, f"Missing 'wrong_source' in: {sc['id']}"
        assert "correct_source" in sc, f"Missing 'correct_source' in: {sc['id']}"
        assert "expected_answer" in sc, f"Missing 'expected_answer' in: {sc['id']}"
        print(f"  - {sc['id']}: wrong={sc['wrong_source']} -> "
              f"correct={sc['correct_source']}")


def run_coordination_eval() -> None:
    """Load and validate the multi-agent coordination dataset."""
    data = load_yaml("test_queries_coordination.yaml")
    scenarios = data.get("scenarios", [])
    print(f"[coordination]  Loaded {len(scenarios)} scenarios")
    for sc in scenarios:
        assert "id" in sc, f"Missing 'id' in scenario: {sc}"
        assert "agents" in sc, f"Missing 'agents' in: {sc['id']}"
        assert "expected_behavior" in sc, f"Missing 'expected_behavior' in: {sc['id']}"
        agent_names = [a["name"] for a in sc["agents"]]
        print(f"  - {sc['id']}: agents={agent_names}")


def run_poisoning_eval() -> None:
    """Load and validate the memory poisoning attack dataset."""
    data = load_yaml("test_poisoning.yaml")
    attacks = data.get("attacks", [])
    print(f"[poisoning]     Loaded {len(attacks)} attacks")
    valid_types = {"direct", "shared", "sleeper"}
    valid_results = {"blocked", "detected", "flagged"}
    for atk in attacks:
        assert "id" in atk, f"Missing 'id' in attack: {atk}"
        assert "type" in atk, f"Missing 'type' in: {atk['id']}"
        assert atk["type"] in valid_types, (
            f"Invalid type '{atk['type']}' in: {atk['id']}"
        )
        assert "payload" in atk, f"Missing 'payload' in: {atk['id']}"
        assert "expected_result" in atk, f"Missing 'expected_result' in: {atk['id']}"
        assert atk["expected_result"] in valid_results, (
            f"Invalid expected_result '{atk['expected_result']}' in: {atk['id']}"
        )
        print(f"  - {atk['id']}: type={atk['type']}, "
              f"expected={atk['expected_result']}")


def main() -> None:
    """Run all eval dataset validations."""
    print("=" * 60)
    print("Memory Agent Eval Dataset Loader")
    print("=" * 60)
    print()

    # Also validate the rubric
    rubric = load_yaml("rubric.yaml")
    criteria = rubric.get("criteria", [])
    threshold = rubric.get("pass_threshold", "N/A")
    print(f"[rubric]        {len(criteria)} criteria, "
          f"pass_threshold={threshold}")
    for c in criteria:
        print(f"  - {c['name']}: weight={c['weight']}")
    print()

    run_multiturn_eval()
    print()
    run_learning_eval()
    print()
    run_coordination_eval()
    print()
    run_poisoning_eval()
    print()

    print("=" * 60)
    print("All eval datasets loaded successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
