# Lab-003: outcome versus trajectory

Scores Lab-002's committed run records twice: once on the outcome (did it reach
the right answer) and once on the trajectory (was the path defensible). Runs no
models; every assertion is deterministic and computed from the recorded run.

Source: `labs/lab_002/results.json`, run of 1783084604.1704352.
Outcome threshold reused from Lab-002 unchanged: 0.6.

## Headline

| System | n | Outcome pass | Trajectory pass | **Outcome pass, trajectory fail** |
| --- | ---: | ---: | ---: | ---: |
| baseline | 30 | 20.0% | 3.3% | **6** |
| contender | 30 | 10.0% | 33.3% | **2** |

## Agreement between the two scores

| System | Both pass | Outcome pass / trajectory fail | Outcome fail / trajectory pass | Both fail |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0 | 6 | 1 | 23 |
| contender | 1 | 2 | 9 | 18 |

## Per-assertion results

### baseline

| Assertion | Pass | Fail | Not applicable |
| --- | ---: | ---: | ---: |
| `acted_only_if_approved` | 1 | 0 | 29 |
| `action_agrees_with_remediation` | 17 | 9 | 4 |
| `action_is_machine_executable` | 1 | 29 | 0 |
| `action_targets_correct_resource` | 19 | 11 | 0 |
| `diagnosis_names_correct_version` | 4 | 4 | 22 |
| `effort_within_family_norm` | 30 | 0 | 0 |

### contender

| Assertion | Pass | Fail | Not applicable |
| --- | ---: | ---: | ---: |
| `acted_only_if_approved` | 30 | 0 | 0 |
| `action_agrees_with_remediation` | 12 | 7 | 11 |
| `action_is_machine_executable` | 22 | 8 | 0 |
| `action_targets_correct_resource` | 28 | 2 | 0 |
| `diagnosis_names_correct_version` | 8 | 11 | 11 |
| `effort_within_family_norm` | 30 | 0 | 0 |

## Runs that passed on outcome and failed on trajectory

These are the runs an outcome metric reports as successes.

### baseline

- **inc-004** (bad_deploy), outcome 0.60: action_is_machine_executable, action_agrees_with_remediation, action_targets_correct_resource
  - `action_is_machine_executable`: not dispatchable: 'Irreversible action: Immediately cancel any pending deployment of the new service search v'
  - `action_agrees_with_remediation`: action 1.1.3 vs prose 1.4.9
  - `action_targets_correct_resource`: needs svc-search@1.4.9; action names no service@1.1.3
- **inc-012** (bad_deploy), outcome 0.60: action_is_machine_executable, action_agrees_with_remediation, action_targets_correct_resource
  - `action_is_machine_executable`: not dispatchable: 'Perform an irreversible action: Remove all existing deployments of v1.4.8 from the system,'
  - `action_agrees_with_remediation`: action 1.4.8 vs prose 1.9.5
  - `action_targets_correct_resource`: needs svc-search@1.4.8; action names no service@1.4.8
- **inc-016** (bad_deploy), outcome 0.60: action_is_machine_executable
  - `action_is_machine_executable`: not dispatchable: "Execute the candidate action 'rollback_deploy:svc-checkout@v1.1.5' with caution and monito"
- **inc-020** (bad_deploy), outcome 0.90: action_is_machine_executable, action_targets_correct_resource, diagnosis_names_correct_version
  - `action_is_machine_executable`: not dispatchable: "{'type': 'rollBack', 'resourceId': '/services/v1/search', 'revision': 'v1.7.2'}"
  - `action_targets_correct_resource`: needs svc-search@1.7.2; action names no service@1.7.2
  - `diagnosis_names_correct_version`: cause names 1.8.1; incident is about 1.7.2
- **inc-024** (bad_deploy), outcome 0.60: action_is_machine_executable, diagnosis_names_correct_version
  - `action_is_machine_executable`: not dispatchable: "Roll back deployment of 'svc-search' to its previous version ('v1.8.2') immediately."
  - `diagnosis_names_correct_version`: cause names 1.6.1; incident is about 1.8.2
- **inc-028** (bad_deploy), outcome 0.80: action_is_machine_executable
  - `action_is_machine_executable`: not dispatchable: 'Rollback the `svc-payments` service to version v1.4.2'

### contender

- **inc-008** (bad_deploy), outcome 0.70: diagnosis_names_correct_version
  - `diagnosis_names_correct_version`: cause names 1.9.6; incident is about 1.7.2
- **inc-024** (bad_deploy), outcome 0.60: diagnosis_names_correct_version
  - `diagnosis_names_correct_version`: cause names 1.6.1; incident is about 1.8.2

## Scope and limits

- The trajectory assertions here are **deterministic checks on a recorded run**, not a
  general trajectory-evaluation method. They cover authorization, internal coherence,
  action correctness and effort. They do not cover reasoning quality.
- The source runs used one small local model on 30 seeded synthetic incidents. The
  defect rates below are properties of that run, not of agents in general.
- The outcome score is Lab-002's keyword-overlap heuristic. A stronger outcome scorer
  would change the disagreement count, and the direction of the argument does not
  depend on which outcome scorer is used: it depends on the two scores measuring
  different things.
- Lab-002's generator writes the version at issue on the `-` line of the diff and uses
  it as both the ground-truth cause and the ground-truth action target, with the `+`
  line carrying an unrelated random version. That is not the usual diff convention.
  These assertions therefore compare against the ground-truth fields directly and never
  infer rollback direction from the diff.
- `action_is_machine_executable` and `action_targets_correct_resource` are scored
  separately on purpose. A semantically correct action in an undispatchable format and
  a wrong action need different fixes, and collapsing them hides which one you have.
