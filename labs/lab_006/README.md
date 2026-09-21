# Lab-006: what produced Lab-001's gap?

Lab-001 compared a rule-based workflow router against a three-agent hierarchy on 100
customer-support queries. The hierarchy passed 40.0% against the router's 23.0%.

That comparison changes two things at once:

| Factor | Router | Hierarchy |
| --- | --- | --- |
| Classification | deterministic keyword switch, no model call | a model call |
| Answer attempts | one | a verifier that can trigger a re-answer |

So the 17-point gap cannot be attributed to the topology. `labs/lab_001/retry_confound.py`
bounded the second factor from the committed records and found it sufficient on its own to
explain the whole difference: the verifier rejected the first answer in 95 of 100 runs, and
retried-and-passed runs were 39% of all hierarchy runs.

Bounding is not measuring. This lab varies the two factors independently.

## The design

|  | 1 answer attempt | verifier-gated re-answer |
| --- | --- | --- |
| **rule classify** | `router` | `router_verified` |
| **model classify** | `hier_noverify` | `hierarchy` |

Plus a fifth arm, `router_retry`: rule classify with one **unconditional** re-answer and no
verifier. It is the arm that separates *having a second attempt* from *deciding when to take
one*, and it is the one the book owed.

`router` and `hierarchy` replicate Lab-001's two systems.

## What is held constant

Everything except the arms is imported from Lab-001 rather than copied: the dataset and its
seed, the agent system prompts, the tool registry, the verifier prompt, the re-answer prompt,
the rubric, the weights, the pass threshold and the judge. If any of those differed, the new
arms would not be comparable to the originals.

The two original arms are **re-run and re-judged in the same session** rather than compared
against Lab-001's stored numbers. That makes every contrast internal to one run and removes
any dependence on the older figures reproducing.

## Reproduce

```bash
ollama serve                                  # llama3.2:3b and qwen2.5:14b
python -m labs.lab_006.run                    # transcripts for all five arms
python -m labs.lab_006.evaluate --runs 3      # judge, write RESULTS.md
python -m labs.lab_006.report                 # re-render without re-judging
```

Transcripts land in `runs/<arm>/<id>.json` and are committed, so the scoring stage can be
replayed without re-running the agents.

## What it found

| Arm | Pass | Model calls | Misroute |
| --- | ---: | ---: | ---: |
| `router` | 23.0% | 2 | 33% |
| `router_retry` | 29.0% | 4 | 33% |
| `router_verified` | 30.0% | 7.73 | 33% |
| `hier_noverify` | 15.0% | 3 | 68% |
| `hierarchy` | 40.0% | 8.69 | 68% |

Both replicated arms reproduce Lab-001 exactly: 23.0% and 40.0% pass, 8.69 mean calls for the
hierarchy. That is the check that the rebuild is faithful.

**A second answer attempt is worth +6.0pp on its own,** with no verifier and no extra agent.

**Gating that attempt behind a verifier adds +1.0pp,** at 7.73 model calls against 4. The verifier
rejects the first answer in 95% of runs, so it is an expensive way to almost always retry. Its
judgement about *when* is worth roughly one query in a hundred.

**Model classification has no stable sign:** -8.0pp on its own, +10.0pp combined with verification.
The factors interact, so no additive decomposition of the original 17-point gap is honest.

**And the routing metric does not measure routing quality.** In both model-classified arms, queries
the classifier sent somewhere other than the dataset's label pass *more* often than the ones it
agreed on (44.1% against 31.2% in the hierarchy). The dataset's category comes from a keyword map
built to organise the corpus; the rule-based switch agrees with it by construction because both are
keyword rules. `misroute_rate` measures agreement with a label defined for another purpose. Lab-001
reported it as though it were routing quality.

## Honest limits

This settles which factor carries the gap **in this configuration**. It does not rank
workflows against multi-agent systems, and every arm's pass rate is far too low for
production use. The contrasts are between-arm differences on the same queries rather than
terms in a fitted factorial model, so interaction between the two factors is not separated.

One deliberate imperfection: the unconditional-retry arm uses Lab-001's re-answer prompt
verbatim, which says "a reviewer flagged the previous answer" when no reviewer did. Rewording
it would have confounded the comparison with a prompt difference. Leaving it means that arm
gets a mildly misleading instruction. The trade is recorded rather than hidden.

## Files

| File | What it is |
| --- | --- |
| `arms.py` | The five arms, built from Lab-001's primitives |
| `run.py` | Records transcripts per arm per query |
| `evaluate.py` | Judges with Lab-001's rubric and judge, writes results |
| `report.py` | Renders `RESULTS.md`, including the factorial contrasts |
| `runs/` | Committed transcripts |
