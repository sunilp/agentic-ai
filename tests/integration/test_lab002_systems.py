import httpx
import pytest

from labs.lab_002.dataset import generate
from labs.lab_002.systems import build_baseline, run_baseline


def _ollama_up() -> bool:
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=1.0)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ollama_up(), reason="needs local Ollama")


@pytest.mark.asyncio
async def test_baseline_produces_a_finding():
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    inc = generate(4, seed=42)[0]
    agent = build_baseline(LiteLlm(model="ollama_chat/llama3.2:3b"))
    rec = await run_baseline(agent, inc, InMemorySessionService())
    assert rec.system == "baseline"
    assert rec.finding is not None
    assert rec.model_calls >= 1


@pytest.mark.asyncio
async def test_contender_pauses_before_remediation():
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.sessions.in_memory_session_service import InMemorySessionService

    from labs.lab_002.systems import build_contender, run_contender
    inc = generate(4, seed=42)[0]
    wf = build_contender(LiteLlm(model="ollama_chat/llama3.2:3b"))
    # auto_approve=False: run only up to the human gate
    rec = await run_contender(wf, inc, InMemorySessionService(), auto_approve=False)
    assert rec.remediation_applied is False  # gate not resolved -> nothing applied
    assert rec.finding is not None           # investigation completed to a finding


@pytest.mark.asyncio
async def test_contender_resumes_and_applies_remediation():
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.sessions.in_memory_session_service import InMemorySessionService

    from labs.lab_002.systems import build_contender, run_contender
    inc = generate(4, seed=42)[1]
    wf = build_contender(LiteLlm(model="ollama_chat/llama3.2:3b"))
    rec = await run_contender(wf, inc, InMemorySessionService(), auto_approve=True)
    assert rec.finding is not None
    assert rec.remediation_applied is True
    assert rec.approved is True
