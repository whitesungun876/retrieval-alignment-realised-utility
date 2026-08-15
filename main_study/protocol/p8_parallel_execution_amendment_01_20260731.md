# P8 Prospective Execution Amendment 01: Serial-to-Parallel Collection

Date frozen: 2026-07-31  
Applies to: Study 3 Protocol v3.2, P8 formal collection  
Status at amendment: outcomes and condition-level summaries remain blinded

## Purpose

This amendment changes only the execution scheduler used for the unfinished
portion of P8. The serial executor was stopped after the currently active
episode had produced its immutable raw record. Parallel collection is adopted
to reduce wall-clock time without changing the scientific design.

## Prospective switch point

- Serial epoch: all immutable formal records present at the final blind cutoff,
  comprising 914 contiguous public-manifest run identifiers.
- Parallel epoch: every as-yet unobserved public-manifest run identifier claimed
  after this amendment and its validation artefacts have been frozen.
- The exact cutoff is recorded in
  `reports/p8_serial_to_parallel_cutoff_20260731.json`.
- The switch decision was made without reading terminal success, scores,
  trajectories by condition, or condition-level aggregates.

Completion order may differ from public-manifest run order after the switch.
Eligibility, target assignment, masked arm, repetition, and the set of planned
records remain exactly those in the original 5,400-row public manifest.

## Invariants

The following remain unchanged:

- exact model and provider configuration;
- prompt renderer and experience interface;
- target tasks, source bindings, masked arms, and repetitions;
- TextWorldExpress configuration and 50-step episode limit;
- public manifest and sealed execution bindings;
- frozen episode adapter and scientific analysis plan;
- prohibition on scientific reruns and outcome-dependent decisions;
- approved episode, token, and monetary caps.

The original frozen files are not edited. A new parallel scheduler is layered
around the frozen single-episode adapter.

## Parallel execution controls

Formal parallel execution uses exactly four independent worker processes.
Processes are required because the frozen episode adapter temporarily replaces
module-level policy functions and is not thread-safe.

Before starting an episode, a worker must acquire one global file lock and make
an atomic claim in the single shared budget ledger. The claim records a masked
run identifier, public run order, worker identifier, claim timestamp, execution
epoch, and conservative token/cost reserve. It contains no condition or outcome.
The ledger refuses a claim when the episode cap or the observed-plus-reserved
token or monetary cap would be exceeded.

Each worker writes a heartbeat at least every 15 seconds while an episode is
active. Heartbeats contain only worker, process, claim, timestamp, and technical
state. They contain no condition, action, success, score, or trajectory field.

An existing raw record is immutable and is never claimed or rerun. A claim with
an output record is reconciled into the ledger without another API call. A stale
claim without an output record is not automatically reclaimed: collection
halts for prospective technical adjudication. Technical provider failures are
handled only under the already-frozen retry policy; model task failure and the
50-step limit remain scientific outcomes and are never rerun.

A stop request prevents new claims. Workers already holding claims finish their
current episode and finalize its technical accounting before exiting.

## Validation gates before formal resumption

### Gate A: local four-worker mock stress test

Acceptance requires:

- exactly four process workers participate;
- no run identifier is claimed more than once;
- all mock outputs are complete and uniquely named;
- the ledger exactly equals the records on disk;
- active conservative reservations prevent over-claiming;
- stop, stale-claim, and output-before-finalization recovery behaviours pass;
- heartbeats and routine reports contain no scientific fields.

### Gate B: paid excluded-task four-worker stress test

Sixteen new technical executions are drawn only from the permanently excluded
development-task set, with four process workers and the same frozen model,
prompt renderer, environment configuration, and 50-step limit. They are never
eligible for formal analysis.

Acceptance requires:

- exactly 16 unique, complete records and zero overwrites;
- every worker completes at least one record;
- no unresolved technical failures;
- exact requested and returned model identity;
- 100% ledger/record reconciliation;
- no active or stale claims after completion;
- all episode, token, and monetary limits respected;
- excluded worker outputs never enter the formal raw-record directory;
- no success or condition-level aggregate is produced or inspected.

If either gate fails, formal execution remains stopped until a new prospective
amendment resolves the failure. The stress-test results cannot be used to alter
the hypothesis, tasks, prompts, conditions, or analysis.

### Prospective validation clarification after the zero-call v1 rejection

The first excluded-test launch was rejected by the ledger before any claim or
API call because the USD 4 validation cap was smaller than a reserve computed
as 50 full context windows. This was an execution-configuration failure, not a
model or environment result. Its FAIL_BEFORE_API report is retained. Excluded
stress v2 retains the USD 4 hard cap and reserves USD 1 and 1,000,000 tokens for
each of four simultaneously active excluded episodes. These values are far
above the observed per-episode use but permit the concurrency path to be tested.
The formal ledger continues to use the original full worst-case reserve formula.

Excluded stress v2 then identified a scheduler-state distinction after five
complete excluded records: budget headroom occupied by other active claims must
cause a worker to wait, not terminate. The five records are retained and never
rerun. No outcomes were inspected. The final scheduler introduces an explicit
technical waiting state and is tested using new v3 run identifiers. Both failed
validation attempts remain in the audit trail and are excluded from analysis.

## Formal resumption and reporting

After both gates pass and scheduler hashes are frozen, the remaining public
manifest records are collected with four workers. Routine output is restricted
to masked run identifiers, run order, worker health, record completeness,
provider/model identity, aggregate token/cost accounting, and technical errors.

The P8 technical report will disclose two execution epochs:

1. serial execution through the 914-record blind cutoff; and
2. four-worker parallel execution thereafter.

Execution epoch and worker identifier are operational provenance variables,
not treatment variables. No scientific comparison by epoch will be performed
before the frozen main analysis. Any later epoch-sensitivity check must be
labelled exploratory.

## Serial-restart incident before formal parallel resumption

During excluded stress v3, a distinct serial executor was detected writing the
formal directory. It was not a child of the excluded scheduler. Before it was
terminated it added eight complete records, extending the contiguous serial
epoch from public run order 906 through 914. No outcome or condition summary was
read. The original excluded stress report is retained as FAIL because its global
formal-count check detected this change; a separate technical adjudication
records that all scheduler-specific checks passed and that no excluded run
identifier entered the formal directory. Formal parallel execution begins only
after the revised 914-record cutoff and a fresh preflight.
