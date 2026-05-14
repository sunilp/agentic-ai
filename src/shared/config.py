"""Environment-based configuration.

Reads from .env file or environment variables.
No magic, no hidden state -- just a typed config object.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ModelConfig(BaseModel):
    """Configuration for the model client."""

    provider: str = os.getenv("MODEL_PROVIDER", "openai")
    api_key: str = os.getenv("OPENAI_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o")
    model_name_cheap: str = os.getenv("MODEL_NAME_CHEAP", "gpt-4o-mini")
    local_url: str = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434/v1")
    temperature: float = 0.0
    max_tokens: int = 4096


class EvalConfig(BaseModel):
    """Configuration for evaluation runs."""

    judge_model: str = os.getenv("EVAL_JUDGE_MODEL", "gpt-4o")
    dataset_path: Path = Path("project/doc-intelligence-agent/evals/dataset.jsonl")
    rubric_path: Path = Path("project/doc-intelligence-agent/evals/rubric.yaml")


def get_model_config() -> ModelConfig:
    return ModelConfig()


def get_eval_config() -> EvalConfig:
    return EvalConfig()
