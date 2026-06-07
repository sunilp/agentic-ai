"""Build and load the query set for Lab-001.

Source: the Bitext customer-support dataset (CC-BY 4.0), single-turn support
requests with category labels. We map its fine-grained categories onto the four
router buckets, take a deterministic balanced sample (seed 42), and commit the
result as queries.json so the run is reproducible without re-downloading.

Run `python -m labs.lab_001.dataset` to (re)build queries.json.
"""

from __future__ import annotations

import csv
import io
import json
import random
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
QUERIES_PATH = HERE / "queries.json"

BITEXT_URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-customer-support-llm-chatbot-training-dataset/resolve/main/"
    "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
)
LICENSE = "CC-BY-4.0 (Bitext)"

# Bitext fine-grained category -> our four router buckets.
CATEGORY_MAP: dict[str, str] = {
    "INVOICE": "billing",
    "PAYMENT": "billing",
    "REFUND": "billing",
    "CANCELLATION_FEE": "billing",
    "DELIVERY": "technical",
    "ORDER": "technical",
    "SHIPPING_ADDRESS": "technical",
    "ACCOUNT": "account",
    "NEWSLETTER": "account",
    "SUBSCRIPTION": "account",
    "CONTACT": "account",
    "FEEDBACK": "escalation",
}
BUCKETS = ["billing", "technical", "account", "escalation"]

# Clearly-labeled synthetic fallback, used ONLY if Bitext is unreachable at build
# time. The report records when the fallback was used so numbers are not mistaken
# for a real-dataset run.
_FALLBACK = [
    ("billing", "I was charged twice on my last invoice, how do I get a refund?",
     "Refunds for duplicate charges go to the original payment method in 5 to 7 business days."),
    ("billing", "How long does a refund take to reach my card?",
     "Refunds are processed to the original payment method within 5 to 7 business days."),
    ("technical", "Where can I track my order after it ships?",
     "Tracking is available from the Orders page once the item ships."),
    ("technical", "Can I change my delivery address after ordering?",
     "Address changes are only possible before an order enters the shipped state."),
    ("account", "How do I unsubscribe from the newsletter?",
     "Update newsletter preferences under Account Settings; changes apply immediately."),
    ("account", "I forgot my password and cannot log in.",
     "Reset your password from the login page under Account Settings."),
    ("escalation", "This is unacceptable, I want to speak to a manager about a disputed charge.",
     "Disputed charges are escalated to a human specialist with a ticket and a 24 hour response."),
    ("escalation", "I have complained three times and nobody has fixed my issue.",
     "Unresolved complaints are routed to a specialist with a ticket reference."),
]


def _fetch_rows() -> list[dict]:
    req = urllib.request.Request(BITEXT_URL, headers={"User-Agent": "lab-001/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted host)
        raw = resp.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    return list(reader)


def build(n: int = 100, seed: int = 42, out_path: Path = QUERIES_PATH) -> dict:
    """Build a balanced sample and write queries.json. Returns the written object."""
    rng = random.Random(seed)
    used_fallback = False

    by_bucket: dict[str, list[dict]] = {b: [] for b in BUCKETS}
    try:
        rows = _fetch_rows()
        for row in rows:
            cat = (row.get("category") or "").strip().upper()
            bucket = CATEGORY_MAP.get(cat)
            instruction = (row.get("instruction") or "").strip()
            response = (row.get("response") or "").strip()
            if not bucket or not instruction:
                continue
            by_bucket[bucket].append(
                {
                    "query": instruction,
                    "reference_answer": response,
                    "source_category": cat,
                    "intent": (row.get("intent") or "").strip(),
                }
            )
    except Exception as exc:  # network unavailable or schema drift
        used_fallback = True
        print(f"[dataset] Bitext fetch failed ({exc}); using labeled synthetic fallback.")
        for bucket, query, ref in _FALLBACK:
            by_bucket[bucket].append(
                {"query": query, "reference_answer": ref, "source_category": "FALLBACK", "intent": ""}
            )

    per_bucket = max(1, n // len(BUCKETS))
    sampled: list[dict] = []
    for bucket in BUCKETS:
        pool = by_bucket[bucket]
        rng.shuffle(pool)
        take = pool[:per_bucket]
        for item in take:
            item["category"] = bucket
            sampled.append(item)

    # Stable, seeded final order and ids.
    rng.shuffle(sampled)
    for i, item in enumerate(sampled):
        item["id"] = f"q{i:03d}"

    obj = {
        "meta": {
            "source": "Bitext customer-support dataset" if not used_fallback else "synthetic fallback",
            "url": BITEXT_URL if not used_fallback else "",
            "license": LICENSE if not used_fallback else "n/a (synthetic)",
            "seed": seed,
            "requested_n": n,
            "actual_n": len(sampled),
            "buckets": BUCKETS,
            "used_fallback": used_fallback,
            "category_map": CATEGORY_MAP,
        },
        "queries": sampled,
    }
    out_path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    print(f"[dataset] wrote {len(sampled)} queries to {out_path} (fallback={used_fallback})")
    return obj


def load(path: Path = QUERIES_PATH) -> dict:
    return json.loads(Path(path).read_text())


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    build(n=n)
