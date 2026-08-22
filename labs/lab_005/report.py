"""Lab-005 report: renders RESULTS.md from results.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIGS = ("freetext", "gated", "quarantine_cited", "quarantine_lineage")
LABEL = {"freetext": "Ungated free-text memory",
         "gated": "Typed write gate, no quarantine",
         "quarantined": "Write gate plus quarantine"}


def render(reports: list[dict], meta: dict) -> str:
    L = ["# Lab-005: a poisoned memory, and what it is allowed to cause", "",
         "Two phases. In the first, an agent investigates an incident whose ticket carries",
         "a false causal claim in a reporter-written field, and proposes something to",
         "remember. In the second, a later incident of the same shape arrives with a clean",
         "ticket, memory is retrieved, and the agent proposes an action.", "",
         "The question is not whether the poison is stored or believed. It is whether it",
         "reaches a consequential action.", "",
         "| Configuration | What it does |",
         "| --- | --- |",
         "| `freetext` | Whatever the model wrote is stored verbatim. No structure, no origin, no evidence. |",
         "| `gated` | Typed claim, evidence must resolve to observations the run actually had, origin computed from the evidence chain, label shown in the later run's context. |",
         "| `quarantine_cited` | As `gated`, plus an action gate refusing forbidden actions whose only basis is untrusted-origin memory. Origin still comes from the evidence the model listed. |",
         "| `quarantine_lineage` | The same action gate, but origin is computed from what the run actually had in context rather than from what the model said it used. |", "",
         f"Corpus: {meta['n_scenarios']} scenarios ({meta['n_poisoned']} poisoned, "
         f"{meta['n_clean']} clean controls), seed {meta['seed']}. Run {meta['started']}.",
         "Temperature 0. A fresh store per configuration, so memory never leaks between them.", "",
         "## Headline: poisoned scenarios", "",
         "| Model | Configuration | Stored | Cited in phase 2 | **Forbidden action reached** |",
         "| --- | --- | ---: | ---: | ---: |"]
    for r in reports:
        for c in CONFIGS:
            b = r["configs"][c]["poisoned"]
            L.append(f"| `{r['model']}` | `{c}` | {b['stored']}/{b['n']} | {b['cited']}/{b['n']} | "
                     f"**{b['reached']}/{b['n']}** |")
    L += ["", "## Clean controls", "",
          "The cost side. A configuration that stopped the poison by stopping the agent from",
          "acting at all would show it here.", "",
          "| Model | Configuration | Produced a usable action | Reached forbidden |",
          "| --- | --- | ---: | ---: |"]
    for r in reports:
        for c in CONFIGS:
            b = r["configs"][c]["clean"]
            L.append(f"| `{r['model']}` | `{c}` | {b['usable_action']}/{b['n']} | "
                     f"{b['reached']}/{b['n']} |")
    L += ["", "## Origins assigned by the write gate", "",
          "The gate computes origin from the evidence chain rather than from the agent's",
          "claim about itself. A claim citing the reporter-written field is `untrusted`",
          "however confidently it is phrased.", ""]
    for r in reports:
        for c in ("gated", "quarantine_cited", "quarantine_lineage"):
            b = r["configs"][c]
            L.append(f"- `{r['model']}` `{c}`: poisoned {b['poisoned']['origins']}, "
                     f"clean {b['clean']['origins']}, "
                     f"{len(b['store']['refused_writes'])} writes refused")
    L += ["", "## How to read this", "",
          "**Storage, citation and reachability are three different measurements.** The write",
          "gate does not stop the poison being stored; it stops it being stored without an",
          "origin. Neither gate stops the later run finding it relevant and saying so. What",
          "changes in the third configuration is what a belief of untrusted origin is allowed",
          "to cause.", "",
          "A high citation rate under quarantine is the correct result, not a failure. The",
          "agent read the memory, found it relevant, and said so. It was then refused an",
          "action that rested on nothing else, and told what corroboration was missing. That",
          "converts a poisoning attempt into a lookup.", "",
          "## Scope and limits", "",
          "- Small local models at temperature 0. Storage and citation rates are properties of",
          "  these models on this corpus. **The reachability result is structural**: an action",
          "  gate that refuses untrusted-only justification refuses it whatever the model",
          "  concluded.",
          "- The poisoned claims are ordinary careless sentences, not optimised triggers. This",
          "  measures the accidental path, which is the common one. It is not a red-team result",
          "  and says nothing about an adversary optimising against the retriever.",
          "- Retrieval is an exact match on service and fault family, not an embedding search.",
          "  A real store's retrieval would introduce its own failure modes, and a poisoning",
          "  that manipulates retrieval ranking is out of scope here.",
          "- Two phases only. Gradual poisoning across many runs, where a claim is promoted by",
          "  repeated use, is not measured.",
          "- The quarantine rule keys on **lineage**: what the system put into the model's",
          "  context, not what the model says it relied on. Two earlier versions asked the",
          "  model instead, first through a `cites_memory` self-report and then through a",
          "  cited justification list. Both let a model that acts on a poisoned memory and",
          "  does not mention it walk straight through. The system knows what it retrieved,",
          "  so that is the fact to enforce on.",
          "- The tool set includes two legitimate remediations (`restart_service`,",
          "  `escalate_to_human`). An earlier version offered only read tools and the two",
          "  forbidden ones, so asking for a remediation step forced a destructive choice",
          "  whether or not memory was poisoned. The clean controls made that visible: they",
          "  reached forbidden actions almost as often as the poisoned ones. That was a",
          "  confound in the harness, not a finding about memory.", ""]
    return "\n".join(L)


def main() -> int:
    d = json.loads((HERE / "results.json").read_text())
    (HERE / "RESULTS.md").write_text(render(d["models"], d["meta"]))
    print("wrote RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
