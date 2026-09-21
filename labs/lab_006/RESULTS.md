# Lab-006: what produced Lab-001's gap, the topology or the extra attempt?

Lab-001 compared a rule-based router against a three-agent hierarchy and the
hierarchy scored higher. The two systems differ in two ways at once, so the result
cannot attribute the gap to either. This varies the two factors independently.

Everything except the arms is imported from Lab-001 unchanged: dataset, agent
prompts, tool registry, verifier, rubric, judge, weights and pass threshold. The two
original arms are re-run and re-judged here rather than copied, so every number
below comes from one session.

Agent model `llama3.2:3b`, judge `qwen2.5:14b` at 3 passes,
pass threshold 0.7. 100 queries per arm, seed 42.

## The five arms

| Arm | Classification | Answer attempts | Pass rate | Mean score | Model calls | Misroute |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `router` | rule | 1 | **23.0%** | 0.382 | 2 | 33% |
| `router_retry` | rule | 2, unconditional | **29.0%** | 0.430 | 4 | 33% |
| `router_verified` | rule | 2, verifier-gated | **30.0%** | 0.433 | 7.73 | 33% |
| `hier_noverify` | model | 1 | **15.0%** | 0.319 | 3 | 68% |
| `hierarchy` | model | 2, verifier-gated | **40.0%** | 0.508 | 8.69 | 68% |

## The contrasts that matter

Each row holds one factor fixed and varies the other.

| Contrast | Isolates | Effect |
| --- | --- | ---: |
| `router_retry` vs `router` | a second answer attempt, no verifier | +6.0pp |
| `router_verified` vs `router` | verifier-gated re-answer | +7.0pp |
| `router_verified` vs `router_retry` | the verifier, given the attempt | +1.0pp |
| `hier_noverify` vs `router` | model classification, one attempt | -8.0pp |
| `hierarchy` vs `router_verified` | model classification, verified | +10.0pp |
| `hierarchy` vs `router` | **both factors, the original comparison** | **+17.0pp** |

## Reading

The original gap is +17.0 percentage points. It does not decompose cleanly,
and the way it fails to is the result.

**A second answer attempt, with no verifier and no extra agent, is worth
+6.0pp.** That is the arm Lab-001 never had, and it costs two model calls.

**Gating that attempt behind a verifier adds +1.0pp** over simply always
retrying, at 7.73 model calls against
4.0. The verifier rejects the first answer in
95% of runs, so it is an expensive way to almost
always retry. Its judgement about *when* to retry is worth about one query in a hundred.

**Model classification has no stable sign.** On its own it is
-8.0pp; combined with verification it is +10.0pp.
The two factors interact strongly, so no additive decomposition of the original gap is
honest, and any single number claiming to attribute it is an artifact of the path chosen
through the table.

## The routing metric does not measure what it is named

The interaction has an explanation, and it is a warning about the metric rather than a
finding about architecture.

| Arm | Misroute rate | Pass when routed | Pass when misrouted |
| --- | ---: | ---: | ---: |
| `router` | 33% | 23.9% (n=67) | 21.2% (n=33) |
| `router_retry` | 33% | 28.4% (n=67) | 30.3% (n=33) |
| `router_verified` | 33% | 28.4% (n=67) | 33.3% (n=33) |
| `hier_noverify` | 68% | 25.0% (n=32) | 10.3% (n=68) |
| `hierarchy` | 68% | 31.2% (n=32) | 44.1% (n=68) |

In the two model-classified arms, queries the classifier sent to a different specialist
than the dataset's label pass **more** often than the ones it agreed on. A routing error
that improves the answer is not a routing error.

The dataset's category comes from a keyword map built to organise the corpus, not to
identify which specialist prompt answers a given query best. The rule-based switch agrees
with that map by construction, since both are keyword rules. The model disagrees with it
on two thirds of queries and produces better answers when it does. So `misroute_rate`
measures agreement with a label defined for another purpose, and it should not be read as
routing quality. Lab-001 reported it as though it were.

This is the more transferable lesson: a ground-truth label borrowed from how a dataset was
assembled will not automatically serve as a correctness signal for a component that was
not what the label was for.


## Scope and limits

- One local model on 100 queries from one dataset with one rubric and one judge.
  Every number is a property of that configuration. **This does not rank workflows
  against multi-agent systems**, and the pass rates are far too low for production
  use in any arm.
- Pass rates are a thresholded mean of three judge passes. Differences of one or two
  queries are not meaningful, and no confidence interval is computed here.
- The contrasts are between-arm differences on the same queries, not a fitted
  factorial model, so interaction between the two factors is not separated out.
- The re-answer prompt is identical across arms, including the unconditional one,
  where the phrase 'a reviewer flagged the previous answer' is untrue by
  construction. Changing it would have confounded the comparison with a prompt
  difference; leaving it means that arm receives a mildly misleading instruction.
  Both choices are defensible and this is the one taken.
- The verifier's own quality is not measured here, only what gating on it changes.
- The routed-versus-misrouted split is observational, not randomised: which queries a
  classifier disagrees with the label on is not a random subset, and the correctly-routed
  cell for the model-classified arms holds only 32 queries. The direction is consistent
  across both of those arms and the size of the effect should not be relied on.
- Five arms on one dataset cannot separate 'the label is wrong for this purpose' from
  'the model classifier is better at this task than the keyword rule'. Both readings
  imply the same thing about the misroute metric, which is why the section above argues
  about the metric rather than about the classifier.
