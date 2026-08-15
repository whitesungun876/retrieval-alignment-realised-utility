# Prospective protocol: concurrent P/C active-control supplement

Status: prepared before any P/C outcome exists.  
Independent unit: target.  
Environment: frozen TextWorldExpress CookingWorld v3.2 configuration.  
Targets: the 800 targets and P source assignments frozen in the prior
supplemental permutation. This is a follow-up on a reused target set, not an
independent target-sample replication.

## Question and estimand

For target `i`, let `Y_iar` be terminal success for condition `a in {P,C}` and
repetition `r in {1,2}`. Valid repetitions are first averaged within target and
condition. The estimand is

`Delta = mean_i(mean_r(Y_iPr) - mean_r(Y_iCr))`.

Targets are equally weighted. Episodes are nested measurements and are never
treated as 3,200 independent units.

`P-C` is interpreted as the incremental effect of a concrete, coherent,
replay-verified trajectory over an abstract format-, length-, and phase-matched
worked-protocol scaffold under the same frozen non-target-specific source
assignment. The contrast does not isolate experience in general, source
success, or replay verification. It deliberately includes the concrete
trajectory's natural language, coherence, domain information, and
actionability beyond the abstract scaffold.

## Conditions

Both conditions use an identical neutral memory renderer shell. Agent-visible
text never says `retrieved`, `permuted`, `control`, `sham`, `replay-verified`,
or the condition name.

P uses the frozen source trajectory assigned to the target under the prior P
permutation. The common shell contains the source cookbook text, initial
observation, chronological action-observation turns, and terminal-success
marker, but not source ID or seed.

C is generated deterministically from that same P source. It preserves:

1. the common neutral renderer header and field order;
2. the number and numbering of action-observation turns;
3. a coarse phase label for every turn (`orient`, `inspect`, `acquire`,
   `navigate`, `transform`, `complete`, or `stop`);
4. chronological action-observation alternation;
5. the same terminal-success marker; and
6. a tokenizer-length target of +/-10% relative to P.

C removes or does not expose:

1. source ID, source seed, fold, and task identifier;
2. the source cookbook, recipe, ingredients, directions, and source-specific
   structure signature;
3. concrete entities, locations, devices, tools, ingredients, directions,
   original commands, and original observations;
4. target cookbook, target entity, target source assignment, or any target
   outcome;
5. admissible-action lists or zero-based indices, because P does not contain
   them and the live prompt already states the index convention; and
6. condition labels or evaluative descriptions.

The scaffold uses grammatical phase descriptions, not random or repeated
filler. Length matching is achieved with a finite set of predeclared,
phase-appropriate abstract detail sentences. If a source cannot be brought
within +/-10% without exceeding those sentences, static QA fails; content is
not repeated merely to hit a token quota.

## Design and masking

Every target receives P and C twice. P and C for a target share the same frozen
P donor/source. A seeded run order interleaves all cells. The public manifest
contains only a masked arm, target, repetition, and run order. A private binding
maps the arm to P or C and contains the source seed and experience hash.

The acting model, provider endpoint, environment, target cookbook, system and
user prompt shell, lexicographically ordered admissible commands, zero-based
index instruction, history window, empty-final repair, official scorer, and
50-step limit are held fixed. Four workers are the maximum authorized design;
historical five- and eight-worker attempts triggered rate-limit failures.

The source vector is conditioned on as fixed. Reuse of sources across targets
limits generalization to other experience banks or assignment draws.

## Outcomes and analysis

Primary outcome: official terminal success.

Primary effect report:

1. target-level `P-C` in percentage points;
2. paired target-cluster bootstrap 95% CI with 10,000 resamples;
3. two-sided sign-flip sensitivity test at alpha .05; and
4. paired-difference TOST with the prospectively fixed +/-5 percentage-point
   margin, two one-sided alpha .05 tests, and the corresponding 90% CI.

The difference test and equivalence test are separate. Possible conclusions
are superior only, equivalent only, both statistically different and
practically equivalent, or inconclusive. Failure to reject a difference null
is not evidence of equivalence.

The bootstrap resamples whole targets, carrying both conditions and all valid
repetitions together. A target-condition mean uses available valid repetitions.
A target is omitted from the contrast only if either condition has zero valid
repetitions. Technical missingness is reported by masked arm before unblinding,
and missingness sensitivity is descriptive.

The sign-flip test is a robust paired symmetry sensitivity rather than a claim
of exact design-based randomization inference. TOST is implemented using the
paired target-difference t procedure.

Secondary descriptive process outcomes may include invalid-index responses,
steps to terminal state, premature stopping, failure to stop, and action-phase
patterns. They are not confirmatory mechanism tests.

## Power and sample size

Prospective simulation uses target-level differences on the support created by
two binary repetitions: `{-1,-0.5,0,0.5,1}`. It evaluates difference-test power
and equivalence power separately over plausible SD, missingness, effect, and
target-count grids. It includes null and +/-5-point equivalence boundaries,
Monte Carlo uncertainty, MDE sensitivity, and searches slightly above 800
targets. No new P/C outcome is read.

## Technical intercurrent events

API/network failure, timeout, empty response, parse failure, environment error,
and legitimate unsuccessful terminal state remain distinct. The frozen runner's
transport retry and empty-final repair rules are reused. Scientific failures are
not rerun. A missing cell may be resumed only if no provider output record
exists and the technical rule permits it. Existing immutable records are never
overwritten.

## Static and execution gates

Before paid smoke, all of the following must pass:

- all old frozen artefact hashes remain unchanged;
- 800 targets, 515 P sources, 3,200 unique formal cells, two masked arms, and
  two repetitions per target-arm;
- P and C share the same source for every target;
- P/C common shells are byte-identical after replacing the condition body;
- action-observation turn count and phase count are identical within each pair;
- C-to-P local open-weight Qwen3-family BPE proxy-token ratio is between .90
  and 1.10 for every selected source, and the word-count ratio is independently
  reported; the exact hosted `qwen3.7-plus-2026-05-26` tokenizer identity is
  not claimed because it is not independently available;
- leakage scan finds no source/target IDs, source/target recipes, concrete
  source entities, original commands, or original observations in C;
- renderer and hashes are deterministic;
- four-worker local mock, atomic finalization, resume reconciliation, and hard
  caps pass; and
- the paid-smoke manifest is outcome-excluded and disjoint from formal targets.

Paid smoke and formal execution require separate later explicit authorizations.
Formal execution additionally requires a PASS technical-acceptance report for
the eight-cell outcome-excluded smoke. There is no efficacy interim analysis.
Technical stops are exact-model drift,
prompt truncation, hash mismatch, leakage, greater than 1% unresolved technical
missingness, repeated rate limiting, or any episode/token/cost hard cap.

## Claim boundary to preserve verbatim

“The concurrent P/C contrast estimates the incremental effect of supplying a
concrete, coherent replay-verified trajectory rather than an abstract
format-, length-, and phase-matched worked-protocol scaffold under the same
frozen non-target-specific assignment. It does not identify a pure experience
effect or the causal effect of replay verification.”
