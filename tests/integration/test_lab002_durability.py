import httpx
import pytest

from labs.lab_002.dataset import generate
from labs.lab_002.metrics import durability_savings


def _ollama_up() -> bool:
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=1.0)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ollama_up(), reason="needs local Ollama")


@pytest.mark.asyncio
async def test_resume_skips_completed_work_and_applies_once(tmp_path):
    from google.adk.models.lite_llm import LiteLlm

    from labs.lab_002.durability import run_with_crash
    inc = generate(4, seed=42)[0]
    db = str(tmp_path / "sess.db")
    pre, post = await run_with_crash(inc, LiteLlm(model="ollama_chat/llama3.2:3b"), db)
    # pre-interrupt did the expensive investigation; post-resume ran far fewer calls
    assert pre.model_calls > post.model_calls          # dedup skipped completed nodes
    assert post.remediation_applied is True            # resumed to completion
    saved = durability_savings(pre, post)
    assert saved["model_calls_saved"] == pre.model_calls
