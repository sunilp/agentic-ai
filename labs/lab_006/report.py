"""Lab-006 report: renders RESULTS.md, including the factorial contrasts."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
ARMS = ("router", "router_retry", "router_verified", "hier_noverify", "hierarchy")
LABEL = {
    "router": "rule classify, 1 answer",
    "router_retry": "rule classify, 2 answers, no verifier",
    "router_verified": "rule classify, verifier-gated re-answer",
    "hier_noverify": "model classify, 1 answer",
    "hierarchy": "model classify, verifier-gated re-answer",
}


def _pp(a: float, b: float) -> str:
    """Difference in percentage points, signed."""
    return f"{(a - b) * 100:+.1f}pp"


def render(d: dict) -> str:
    S = d["systems"]

    def acc(a: str) -> float:
        return S[a]["accuracy"]

    L = ["# Lab-006: what produced Lab-001's gap, the topology or the extra attempt?", "",
         "Lab-001 compared a rule-based router against a three-agent hierarchy and the",
         "hierarchy scored higher. The two systems differ in two ways at once, so the result",
         "cannot attribute the gap to either. This varies the two factors independently.", "",
         "Everything except the arms is imported from Lab-001 unchanged: dataset, agent",
         "prompts, tool registry, verifier, rubric, judge, weights and pass threshold. The two",
         "original arms are re-run and re-judged here rather than copied, so every number",
         "below comes from one session.", "",
         f"Agent model `{d['agent_model']}`, judge `{d['judge_model']}` at {d['judge_runs']} passes,",
         f"pass threshold {d['pass_threshold']}. "
         f"{S['router']['n']} queries per arm, seed 42.", "",
         "## The five arms", "",
         "| Arm | Classification | Answer attempts | Pass rate | Mean score | Model calls | Misroute |",
         "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
    for a in ARMS:
        s = S[a]
        cls = "model" if a in ("hier_noverify", "hierarchy") else "rule"
        att = ("1" if a in ("router", "hier_noverify")
               else "2, unconditional" if a == "router_retry" else "2, verifier-gated")
        L.append(f"| `{a}` | {cls} | {att} | **{s['accuracy']:.1%}** | {s['avg_score']:.3f} | "
                 f"{s['avg_model_calls']} | {s['misroute_rate']:.0%} |")

    L += ["", "## The contrasts that matter", "",
          "Each row holds one factor fixed and varies the other.", "",
          "| Contrast | Isolates | Effect |", "| --- | --- | ---: |",
          f"| `router_retry` vs `router` | a second answer attempt, no verifier | "
          f"{_pp(acc('router_retry'), acc('router'))} |",
          f"| `router_verified` vs `router` | verifier-gated re-answer | "
          f"{_pp(acc('router_verified'), acc('router'))} |",
          f"| `router_verified` vs `router_retry` | the verifier, given the attempt | "
          f"{_pp(acc('router_verified'), acc('router_retry'))} |",
          f"| `hier_noverify` vs `router` | model classification, one attempt | "
          f"{_pp(acc('hier_noverify'), acc('router'))} |",
          f"| `hierarchy` vs `router_verified` | model classification, verified | "
          f"{_pp(acc('hierarchy'), acc('router_verified'))} |",
          f"| `hierarchy` vs `router` | **both factors, the original comparison** | "
          f"**{_pp(acc('hierarchy'), acc('router'))}** |", ""]

    # Both decomposition paths, because they disagree and the disagreement is the finding.
    attempt = acc("router_retry") - acc("router")
    gating = acc("router_verified") - acc("router_retry")
    classify_verified = acc("hierarchy") - acc("router_verified")
    classify_bare = acc("hier_noverify") - acc("router")
    total = acc("hierarchy") - acc("router")
    L += ["## Reading", "",
          f"The original gap is {total * 100:+.1f} percentage points. It does not decompose cleanly,",
          "and the way it fails to is the result.", "",
          "**A second answer attempt, with no verifier and no extra agent, is worth",
          f"{attempt * 100:+.1f}pp.** That is the arm Lab-001 never had, and it costs two model calls.", "",
          f"**Gating that attempt behind a verifier adds {gating * 100:+.1f}pp** over simply always",
          f"retrying, at {S['router_verified']['avg_model_calls']} model calls against",
          f"{S['router_retry']['avg_model_calls']:.1f}. The verifier rejects the first answer in",
          f"{S['router_verified']['retry_rate']:.0%} of runs, so it is an expensive way to almost",
          "always retry. Its judgement about *when* to retry is worth about one query in a hundred.", "",
          "**Model classification has no stable sign.** On its own it is",
          f"{classify_bare * 100:+.1f}pp; combined with verification it is {classify_verified * 100:+.1f}pp.",
          "The two factors interact strongly, so no additive decomposition of the original gap is",
          "honest, and any single number claiming to attribute it is an artifact of the path chosen",
          "through the table.", "",
          "## The routing metric does not measure what it is named", "",
          "The interaction has an explanation, and it is a warning about the metric rather than a",
          "finding about architecture.", "",
          "| Arm | Misroute rate | Pass when routed | Pass when misrouted |",
          "| --- | ---: | ---: | ---: |"]
    for a in ARMS:
        r = S[a]["records"]
        ok = [x for x in r if not x["flags"]["misroute"]]
        bad = [x for x in r if x["flags"]["misroute"]]
        f = lambda xs: f"{sum(x['passed'] for x in xs) / len(xs):.1%} (n={len(xs)})" if xs else "n/a"
        L.append(f"| `{a}` | {S[a]['misroute_rate']:.0%} | {f(ok)} | {f(bad)} |")
    L += ["", "In the two model-classified arms, queries the classifier sent to a different specialist",
          "than the dataset's label pass **more** often than the ones it agreed on. A routing error",
          "that improves the answer is not a routing error.", "",
          "The dataset's category comes from a keyword map built to organise the corpus, not to",
          "identify which specialist prompt answers a given query best. The rule-based switch agrees",
          "with that map by construction, since both are keyword rules. The model disagrees with it",
          "on two thirds of queries and produces better answers when it does. So `misroute_rate`",
          "measures agreement with a label defined for another purpose, and it should not be read as",
          "routing quality. Lab-001 reported it as though it were.", "",
          "This is the more transferable lesson: a ground-truth label borrowed from how a dataset was",
          "assembled will not automatically serve as a correctness signal for a component that was",
          "not what the label was for.", ""]
    L += ["", "## Scope and limits", "",
          "- One local model on 100 queries from one dataset with one rubric and one judge.",
          "  Every number is a property of that configuration. **This does not rank workflows",
          "  against multi-agent systems**, and the pass rates are far too low for production",
          "  use in any arm.",
          "- Pass rates are a thresholded mean of three judge passes. Differences of one or two",
          "  queries are not meaningful, and no confidence interval is computed here.",
          "- The contrasts are between-arm differences on the same queries, not a fitted",
          "  factorial model, so interaction between the two factors is not separated out.",
          "- The re-answer prompt is identical across arms, including the unconditional one,",
          "  where the phrase 'a reviewer flagged the previous answer' is untrue by",
          "  construction. Changing it would have confounded the comparison with a prompt",
          "  difference; leaving it means that arm receives a mildly misleading instruction.",
          "  Both choices are defensible and this is the one taken.",
          "- The verifier's own quality is not measured here, only what gating on it changes.",
          "- The routed-versus-misrouted split is observational, not randomised: which queries a",
          "  classifier disagrees with the label on is not a random subset, and the correctly-routed",
          "  cell for the model-classified arms holds only 32 queries. The direction is consistent",
          "  across both of those arms and the size of the effect should not be relied on.",
          "- Five arms on one dataset cannot separate 'the label is wrong for this purpose' from",
          "  'the model classifier is better at this task than the keyword rule'. Both readings",
          "  imply the same thing about the misroute metric, which is why the section above argues",
          "  about the metric rather than about the classifier.", ""]
    return "\n".join(L)


def main() -> int:
    d = json.loads((HERE / "results.json").read_text())
    (HERE / "RESULTS.md").write_text(render(d))
    print("wrote RESULTS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
