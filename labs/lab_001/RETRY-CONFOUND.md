# Lab-001 follow-up: the retry confound, bounded

The original comparison gave the hierarchy a verifier that can trigger a re-answer
round and gave the router one attempt. This bounds how much of the pass-rate gap
that difference could account for, using only the records the original run
committed. **No models were run.**

| | n | Pass rate | Mean model calls |
| --- | ---: | ---: | ---: |
| router | 100 | 23.0% | 2 |
| hierarchy, all | 100 | 40.0% | 8.69 |
| hierarchy, verifier retried | 95 | 41.1% | |
| hierarchy, answered once | 5 | 20.0% | |

## What this shows

**The verifier rejected the first answer in 95 of 100 runs.** The hierarchy
is therefore not a system that occasionally retries. It is a system that almost always
takes two attempts, and the single-attempt case is the rare one.

**The 5 runs that answered once passed at 20.0%,** against the router's
23.0%. That subset is tiny and it is not a random sample, since a run reaches it
only by satisfying the verifier first time, so it cannot carry much weight in either
direction. It does not support the hierarchy.

**The gap to explain is 17.0%.** If every retried run that passed owed its pass entirely
to the second attempt, the retry would account for 39.0% of all hierarchy runs, which
exceeds the gap. The extra attempt is sufficient on its own to explain the whole
difference. It is an upper bound and not an estimate, and the point is that the
original data cannot rule the explanation out.

**Routing got worse, not better.** The hierarchy's LLM classifier misrouted
68% of queries against 33% for the rule-based
switch. So the hierarchy scored higher while being worse at the one thing the extra
agents were added to do, which points further at the answer attempts rather than the
topology.

## What would settle it

A third arm: the router given the same number of answer attempts, with no verifier.
If it matches the hierarchy, the topology bought nothing on this task. If the
hierarchy still leads, the verification is doing work. That arm has not been run, and
until it is, the honest reading of the original result is that a difference in attempt
budget is at least as plausible an explanation as the architecture.
