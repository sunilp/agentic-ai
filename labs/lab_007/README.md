# Lab-007: what a corpus has to be before calibration means anything

Builds the instrument that later labs use to ask whether a detector's stated
probability is worth anything, and establishes what that instrument cannot see.

**Runs no models.** Everything here is synthetic detectors with known
calibration and closed-form arithmetic. That makes it free, instant and exactly
reproducible. Pointing it at a real detector is Lab-004's job, not this one's.

## Why

A detector that says 0.8 should be right 80% of the time. Vendors are starting
to sell calibration as a feature, and ARCH-002 says not to threshold on a
model's self-reported confidence. Both claims need one instrument to settle
them, and an instrument that has not been tested against a known answer is not
evidence.

## What it found

**Expected calibration error is biased upward, and the bias is large enough to
swallow most published corpora. It is an expected value with a wide spread, not
a floor.**

A *perfectly calibrated* detector still reads a non-zero ECE, because every
bin's observed rate carries sampling noise and the metric takes the absolute
value of each gap, so noise cannot cancel. That floor shrinks with corpus size:

| Rows | Mean ECE for a perfect detector | Range over 30 trials | Corpus at this scale |
| ---: | ---: | --- |
| 50 | 0.104 | 0.036 to 0.224 | `lab_004` corpus as it stands |
| 200 | 0.053 | 0.026 to 0.083 | JBB-Behaviors |
| 569 | 0.031 | 0.012 to 0.048 | R-Judge |
| 1,000 | 0.021 | 0.013 to 0.043 | deepset/prompt-injections |
| 4,000 | 0.011 | n/a | |
| 10,000 | 0.007 | 0.003 to 0.015 | wildguardmix |
| 20,000 | 0.005 | n/a | |

Read that against the signal. A synthetic detector that overstates every claim
by 0.35 reads about 0.20, so even 50 rows catches a gross liar. A detector that
is off by 0.05, which is the interesting case, cannot be told from a perfect one
below roughly a thousand rows.

**So the corpus decides the question before the detector does.** Lab-004's
50-ticket corpus is sufficient to measure reachability, which is what it was
built for, and nowhere near sufficient to measure calibration. Most public
agent-safety benchmarks are in the same position: they can catch a detector
that is badly wrong and cannot certify one that is nearly right.

**The instrument passes its own gate.** A calibrated synthetic reads under 0.02
at 4,000 rows across all twelve seeds tried (0.0057 to 0.0164), while an
overconfident one reads 0.20. The separation is real and not seed luck.

## Scope and limits

- The floor is computed on a six-value probability grid with ten bins. A
  detector that concentrates its output differently will have a different
  floor. Compute the floor for your own output distribution rather than reusing
  this table.
- At 4,000 rows the bootstrap interval on the calibrated arm runs 0.0063 to
  0.0235, so the point estimate clears a 0.02 gate while the interval does not.
  Published readings should carry the interval, not the point.
- ECE with equal-width bins is one of several definitions. Adaptive binning and
  class-conditional variants will move these numbers.
- Nothing here says a calibrated detector is a useful detector. Calibration is
  about whether a probability is honest, not about whether it separates classes.
  Precision at a declared base rate answers that, and lives in `metrics.py`.

## One error made during development, recorded here

`operating_point` was first written with `base_rate=None` defaulting to the
corpus's own prevalence. No test drove that branch, and it was deleted rather
than kept. The deletion improved the design: inheriting whatever mix a corpus
happens to have is precisely the mistake this lab exists to measure, so the
convenient default was also the wrong one. `base_rate` is now required.

## Phase B: what a local model says when asked for its own confidence

ARCH-002 says not to threshold on a model's self-reported confidence. Three
models that run on a laptop, screening lab_004's corpus at temperature 0, asked
for a probability between 0 and 1.

| Model | Parsed | Distinct values | Share at exactly 0 or 1 | Median latency |
| --- | ---: | ---: | ---: | ---: |
| `llama3.2:3b` | 50/50 | 3 | 90% | 223 ms |
| `qwen2.5:7b` | 50/50 | 6 | 88% | 341 ms |
| `gemma4:e2b` | 50/50 | 4 | 90% | 4,142 ms |

**The number is a label with a decimal point.** Asked for a probability, all
three answer almost entirely 0.0 or 1.0. `llama3.2:3b` used three values in
fifty tickets. That does not make it uncalibratable: a map can attach an
empirical rate to each of three values. What calibration cannot recover is a
distinction the detector never made, so every ticket scoring 1.0 receives the
same number however different those tickets were. More rows would buy confidence
in the three values and no further resolution.

That is a sharper claim than ARCH-002 currently makes. The blueprint says the
confidence is not calibrated. On these models it is not a probability at all.

**And the precision column is a trap.** Every model produced zero false
positives on twenty clean tickets, so measured precision reads 1.00 at every
base rate. Zero events in twenty trials does not bound the false-positive rate
at zero, it bounds it at roughly 3/20:

| Model | Base rate | Recall | Precision (measured) | Precision (FPR at bound) |
| --- | ---: | ---: | ---: | ---: |
| `llama3.2:3b` | 1% | 0.47 | 1.00 | **0.03** |
| `qwen2.5:7b` | 1% | 0.37 | 1.00 | **0.02** |
| `gemma4:e2b` | 1% | 0.60 | 1.00 | **0.04** |

A detector that looks perfect on the corpus is a detector whose false-positive
rate the corpus never measured. At a realistic base rate the difference between
those two columns is the difference between shipping it and not.

### Scope and limits, Phase B

- Three small local models, one 50-ticket corpus, single-turn, temperature 0. None of this transfers to a frontier model or to a model trained for calibrated output, which is the open question Phase C exists to answer.
- Clean tickets in lab_004's corpus are bland templates with nothing injection-shaped in them. Zero false positives says as much about that as about the models.
- The corpus has six injection texts repeated with different service names and numbers. Scaling the generator adds rows, not diversity, so it cannot buy the statistical power Phase A says calibration needs.
- Asking for a probability in text is one elicitation method. Token logprobs would be another and would likely read differently.

### An error made in Phase B, recorded here

The token cap was first set to 400. `gemma4:e2b` thinks before it answers, so
twelve of its fifty replies were cut off and scored as unparseable, which read
as a model that would not answer. This is the same mistake lab_004 records in
its own README, repeated by someone who had read that README the same day. The
cap is now 700, matching lab_004, `done_reason` is carried through to the
verdict, and truncation is reported separately from a failure to parse. At 700
the model parses 50 of 50.

The general shape is worth keeping: a limit in the harness read as a property
of the thing being measured. It flattered the result both times.

## Phase C: a model built to emit probabilities, on the same corpus

`typesafe/jev` (`jev-1.13.0`), asked the same question in the same words, through
Cloudflare Workers AI.

| Detector | Distinct values | Share at exactly 0 or 1 | Recall | Mean p on injected | Mean p on clean |
| --- | ---: | ---: | ---: | ---: | ---: |
| `llama3.2:3b` | 3 | 90% | 0.47 | 0.38 | 0.00 |
| `qwen2.5:7b` | 6 | 88% | 0.37 | 0.34 | 0.00 |
| `gemma4:e2b` | 4 | 90% | 0.60 | 0.50 | 0.00 |
| `jev-1.13.0` | 9 | **0%** | **1.00** | 0.93 | 0.03 |

**The scale is used.** Not one of Jev's fifty answers sat at 0 or 1. It answered
0.03 and 0.04 on clean tickets and 0.77 to 0.97 on injected ones. Every local
model put nearly all its mass on the two endpoints. Whatever else is true, these
are different kinds of output: one is a distribution, the other is a label.

**And the calibration claim is still not tested.** Resolution is not calibration.
A coarse detector can be calibrated and a granular one can be
badly wrong; granularity and calibration are independent. At fifty rows the ECE floor is 0.104, so this corpus cannot tell a
calibrated detector from a moderately miscalibrated one whatever it emits. The
claim that a stated 0.93 is right 93% of the time remains unmeasured here.

**The precision trap catches Jev too.** Recall 1.00 and zero false positives on
twenty clean tickets reads as precision 1.00 at every base rate. At the
rule-of-three bound and a 1% base rate it is 0.06. Better than the local models'
0.02 to 0.04, and still not a number anyone should ship on.

### What this cost, and what it does not measure

Fifty tickets took 18,380 input tokens. At TypeSafe's published $0.042/MTok that
is under a tenth of a cent; Cloudflare does not publish a partner-model rate.

Median round trip was 745 ms from Pune through a Cloudflare gateway. TypeSafe
measured 70 to 500 ms from their own laptops on the West Coast. These two numbers
are not comparable and nothing here refutes theirs. **This lab does not test the
latency claim** and no latency figure from it should be quoted as if it did.

### Reaching a partner model at all

Two things cost an hour and are worth writing down.

The documented `/ai/run/{model}` path returns `7000 No route for that URI` for
`typesafe/jev`, while working normally for `@cf/meta/llama-3.1-8b-instruct`.
Partner models take the model in the body:

```
POST /client/v4/accounts/{account_id}/ai/run
{"model": "typesafe/jev", "input": {"state": ..., "questions": {...}}}
```

And partner models do not draw on the Workers AI free neuron allocation. They
bill through AI Gateway, which returns `2021 Insufficient balance; add money to
your gateway or use BYOK` until the account has credit. Cloudflare's Workers AI
pricing page documents `@cf/` models only and says nothing about either point.

### Not taken: the open-weight path

`jaredpalmer/kev-4b` is an Apache-2.0 LoRA adapter on Qwen3.5-4B-Base that serves
TypeSafe's `/v1/systemone` contract locally, so the same client reaches it by
changing a base URL. Its card publishes an out-of-domain ECE of 0.122 raw and
0.048 at temperature 2.0. Running it would make the whole comparison reproducible
without an account, and it is the obvious next step. It is not in these numbers.

## Phase D: the same contract, open weights, on a laptop

`jaredpalmer/kev-0.8b` is Apache-2.0, a LoRA adapter on Qwen3.5-0.8B-Base, and it
serves TypeSafe's `/v1/systemone` contract. The detector differs from the Jev one
by a base URL and the absence of a Cloudflare envelope.

| Detector | Params | Distinct values | Share at exactly 0 or 1 | Recall | Median latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `llama3.2:3b`, asked to state a number | 3B | 3 | 90% | 0.47 | 223 ms |
| `qwen2.5:7b`, asked to state a number | 7B | 6 | 88% | 0.37 | 339 ms |
| `gemma4:e2b`, asked to state a number | e2b | 4 | 90% | 0.60 | 4,088 ms |
| `kev-0.8b`, typed decision model | **0.8B** | **20** | **0%** | 0.53 | **149 ms** |
| `jev-1.13.0`, typed decision model | undisclosed | 9 | 0% | 1.00 | 674 ms |

**Granularity did not track model size.** Kev-0.8B is the smallest model in the
table, four to nine times smaller than the general models it sits under, and it
produced the most granular output of any of them: twenty distinct values against
three, and nothing at the endpoints.

Be careful what that licenses. These systems differ in base model, training and
output mechanism at once, and no same-model ablation was run, so this does not
isolate the typed output head as the cause. The supported claim is narrower: if
granularity came from using a bigger or better general model, this column would
not look like this.

**Granularity and detection moved independently.** Kev-0.8B's recall at a 0.5
threshold, 0.53, sits between the general models' 0.37 and 0.60, while its
distinct-value count is more than three times any of theirs. Recall at a single
threshold is a thin measurement and does not establish equivalent detection, but
nothing here suggests the granular detector bought its granularity by being
better at the task.

That also means the interesting part of this lab costs nothing to reproduce.
Fifty tickets in 8 seconds on a laptop, Apache-2.0 weights, no account, no key,
no credit balance. Jev's recall of 1.00 is the one number here that needs a
vendor, and it is a number this corpus is too small and too templated to
generalise from.

### Still not calibration

Every caveat from Phase C stands. Twenty distinct values is resolution. Whether a
stated 0.62 is right 62% of the time is unmeasured, because at fifty rows the ECE
floor is 0.104. Kev's own model card reports an out-of-domain ECE of 0.122 raw
and 0.048 at temperature 2.0, on a 764-record suite, which is the sort of corpus
this question actually needs. Verifying that figure with this instrument is the
obvious next lab.

### A second error, recorded here

The first five-detector run died after four and a half minutes with a bare
`HTTPError 401`, discarding three local models that had already been measured.
Wrangler's OAuth token had expired six minutes earlier, mid-run, and reading the
token straight off disk bypasses the refresh that any `wrangler` command
performs.

Two fixes, both kept: `screen_all` records a failed call as an unparsed verdict
instead of raising, so one expiry can no longer throw away a run, and the
wrangler fallback now forces a refresh before reading. The documented path is
still `CLOUDFLARE_API_TOKEN`, because a dashboard token does not expire under a
long run at all.

The shape is the same one Phase B recorded: an artefact of the harness presenting
as a result. There it flattered a model, here it destroyed a run.

## Phase E: one forward pass, read two ways

Phases B to D compared different systems, so none of them could say what caused
the difference in granularity. This arm changes one thing, after the model has
already answered.

The model is asked a single Yes or No question. At temperature 0 the token it
emits is the argmax of its own distribution, so both readouts come from one
forward pass: one takes the word, the other takes the probability mass on Yes
against Yes plus No. Same prompt, same call, same weights.

| Model | Readout | Distinct values | At exactly 0 or 1 | AUC [95% CI] |
| --- | --- | ---: | ---: | ---: |
| `llama3.2:3b` | word | 1 | 100% | 0.500 [0.500, 0.500] |
| `llama3.2:3b` | **logprob** | **50** | **0%** | **1.000 [1.000, 1.000]** |
| `qwen2.5:7b` | word | 2 | 100% | 0.583 [0.527, 0.667] |
| `qwen2.5:7b` | **logprob** | 29 | 60% | **0.967 [0.914, 1.000]** |
| `gemma4:e2b` | word | parsed 0/50 | | n/a |
| `gemma4:e2b` | **logprob** | 28 | 46% | **0.950 [0.893, 1.000]** |

AUC is used because the readouts put their scores in different places, and
ranking is the only comparison that survives that. It measures ordering and says
nothing about calibration.

**`llama3.2:3b` said "No" to all fifty tickets.** One value, AUC 0.500, no
information at all. The distribution over that same token ranks all fifty
correctly. The graded belief was there; reading it as a word discarded every bit.

Three cautions on that table. The 1.000 intervals are degenerate, because a
bootstrap resampling perfectly separated observations preserves the separation,
so those bounds are an artefact of the method rather than independent evidence.
`gemma4:e2b` emits a reasoning token before any answer, so its word readout parses
nothing. And the two readouts share one call, so only one latency exists per
model; the runner attributes it to the word row and records zero for the other.

**The scale moved.** The logprob readout averages 0.106 on injected tickets and
0.007 on clean ones. Ranking is perfect and a 0.5 threshold catches nothing. A
readout change is a detector change and every threshold tuned against the old one
is invalid.

### Limits of this arm

- One prompt. A different question might narrow or widen the gap; this measures one ordinary way of asking, not the best possible one.
- The readout works only where the answer lands in the first generated token. A model that reasons first puts almost no mass on either answer token, which is why `qwen2.5:7b` and `gemma4:e2b` still show 60% and 46% at the endpoints: their ratios rank at very small magnitudes.
- Still fifty tickets from six injection texts. AUC 1.000 is a statement about this corpus and nothing else.
- Recovering the distribution costs nothing extra here because Ollama returns it on request. A runtime that does not expose token probabilities cannot do this at all, and one that does may charge for it.

### Production note

`jev` parsed 49 of 50 on this run. One call failed and was recorded as an
unparsed verdict rather than raising, which is the fix added after an expired
token destroyed an earlier run. It behaved as intended.

## Files

| File | What it is |
| --- | --- |
| `metrics.py` | ECE, reliability curve, operating point at a declared base rate, seeded bootstrap intervals |
| `synthetic.py` | Detectors with known calibration, and the noise floor they establish |
| `detectors.py` | The `Verdict` shape, `LocalJudge` over Ollama, and the transport |
| `run.py` | Phase A: writes `results.json` and `RESULTS.md` |
| `baseline.py` | Phases B, C and D: writes `baseline.json` and `BASELINE.md` |

## Reproduce

```bash
python -m labs.lab_007.run                  # phase A, no models, seconds
python -m labs.lab_007.run --out /tmp/x     # write somewhere else instead
python -m labs.lab_007.baseline             # phase B, needs ollama, about 4 minutes
python -m labs.lab_007.baseline --jev       # adds phase C, needs CLOUDFLARE_* env
python -m labs.lab_007.baseline --logprob   # adds phase E, the readout ablation, local
python -m labs.lab_007.baseline --kev       # adds phase D, needs a local kev server:
#   git clone https://github.com/jaredpalmer/kev && cd kev && uv sync --extra serve
#   KEV_DTYPE=bf16 uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
python -m labs.lab_007.baseline --render-only   # re-render from baseline.json
python -m pytest tests/unit/test_lab007_{metrics,synthetic,detectors}.py
```

Phase A needs nothing. Phase B needs `ollama serve` and the three models. No API keys either way.
