# A Prospectively Frozen Post-Main-Study Supplemental Random-Baseline Experiment

**Protocol status:** FROZEN AT SUP-R0 — NO SUPPLEMENTAL OUTCOMES EXIST  
**Draft date:** 2026-08-03  
**Freeze date:** 2026-08-03  
**Relation to the main study:** This supplemental experiment was conceived after completion and unblinding of Study 3 Protocol v3.2. It addresses the absence of a random successful-trajectory control. It neither modifies nor reclassifies any v3.2 hypothesis, analysis, result, or conclusion.

## 1. Study objective and claim boundary

The supplemental experiment asks whether the benefit of the Raw Semantic condition in the main study arose from target-specific semantic source assignment or from receiving a successful trajectory irrespective of its assignment to the target. The experiment compares a concurrent no-memory condition (N2), a permuted-source condition (P), and a newly executed raw-semantic condition (R2). P and R2 use exactly the same multiset of successful source trajectories; only the source-to-target assignment differs. Consequently, R2 minus P estimates the incremental utility of target-specific raw-semantic pairing while controlling the marginal distribution and reuse frequency of source experiences.

The experiment is a prospectively frozen post-main-study supplement, not part of the original v3.2 confirmatory design. The old N and R episode outcomes will not enter any supplemental effect estimate or hypothesis test. No supplemental result will change the evidential status of the frozen v3.2 H minus R result. The study does not identify causal mediation, does not test every possible random-memory policy, and does not establish that semantic similarity is generally useful or useless outside this environment, source bank, policy model, and prompt interface.

## 2. Design

The independent experimental unit is the target task. The design contains 800 targets, three concurrent conditions, and two independent Agent executions per target-condition cell, yielding 4,800 formal episodes. The target set consists mechanically of all 675 frozen v3.2 formal targets followed by the first 125 targets in the previously frozen reserve order, subject only to an untouched-use audit. Repetitions improve the precision of the target-condition mean; they are not treated as independent inferential units.

The model, environment, target cookbook presentation, action interface, maximum step count, raw experience renderer, and scorer remain the same as in v3.2. The planned model identifier is `qwen3.7-plus-2026-05-26`; TextWorldExpress version 1.1.0 runs CookingWorld on the test fold with `numLocations=3,numIngredients=2,numDistractorItems=0,includeDoors=0,limitInventorySize=0`, and each episode has at most 50 environment steps. Four workers may execute the frozen manifest concurrently after engineering validation.

N2 receives the same explicit experience wrapper as the memory conditions, with an empty source block. R2 uses the frozen v3.2 Raw Semantic pipeline: raw task text, BGE-M3 at the frozen revision, cosine similarity, the frozen successful source bank, Top-1 selection, and the frozen label-blind tie rule. P receives a source produced by a target-level permutation of the complete R2 source assignment vector. P is therefore a permuted-source control, not a new uniform draw from the source bank.

## 3. Estimands and evidence hierarchy

For target (i) and condition (c), \(\bar Y_{i,c}\) is the mean terminal-success indicator across the valid repetitions available for that target-condition. The primary estimand is

\[
\tau_{R2-P}=\frac{1}{800}\sum_{i=1}^{800}(\bar Y_{i,R2}-\bar Y_{i,P}).
\]

It measures the average incremental utility of target-specific raw-semantic assignment over permutation assignment while holding the source multiset and source reuse frequencies fixed.

The single primary estimand has two prospectively confirmatory inferential objectives. The first is a two-sided difference test of \(H_0:\tau_{R2-P}=0\) at \(\alpha=.05\), reported with the mean target-level risk difference, a target bootstrap 95% confidence interval using 10,000 resamples, and a target-level two-sided sign-flip test using 10,000 resamples. The second is a TOST equivalence analysis with bounds of -0.05 and +0.05. TOST uses the 800 target-level paired differences, two one-sided tests at \(\alpha=.05\), and the equivalent 90% confidence-interval decision rule. Equivalence is concluded only if the complete 90% interval lies inside [-0.05, +0.05]. The difference and equivalence decisions will both be reported; neither will be replaced by the other after observing results.

The secondary estimands are \(\tau_{P-N2}\), which assesses generic successful-trajectory scaffolding, and \(\tau_{R2-N2}\), which provides a concurrent replication of the raw-semantic memory package relative to no memory. Their two-sided sign-flip p-values form one Holm-adjusted secondary family. Unadjusted effect estimates and bootstrap 95% confidence intervals will also be reported.

Offline structural correspondence, ingredient overlap, operation overlap, source reuse, transformation coverage, failure categories, and overlap strata are predeclared diagnostics. They do not determine target inclusion, rerunning, stopping, or the interpretation of the confirmatory R2 minus P test.

## 4. R2 and P construction

R2 will be regenerated once for all 800 targets using the frozen retriever. For the original 675 targets, R2 must reproduce the old R source identifier exactly for every target. The 125 reserve targets receive new R2 selections produced by the same frozen pipeline without inspecting Agent outcomes. Every selected source must belong to the frozen source bank and retain its successful official replay record.

Let \(S=(s_1,\ldots,s_{800})\) be the R2 source vector in frozen target order. A new, not previously used seed will generate a permutation of donor-target indices. A candidate permutation is accepted only if every donor differs from its recipient target and \(P_i\neq R2_i\) for all 800 recipients. It must preserve the R2 source multiset exactly, including the reuse count of every individual source. Candidate permutations may be rejected only for these predeclared collision rules. Ingredient overlap, operation overlap, graph correspondence, similarity score, v3.2 outcomes, or expected Agent performance may not be inspected to accept or reject a candidate. Candidate hashes and mechanical rejection reasons will be retained.

The P condition is expected to contain some accidental exact structural matches. Across the already frozen 675-target source assignment, the signature-frequency expectation is 1.74% without constraints and 1.72% over assignment edges allowed by the two collision rules; the observed R correspondence rate in those targets is 6.52%. These are planning diagnostics, not gates. After the 125 reserve R2 assignments are generated, the same frequency calculation will produce and freeze the final 800-target expectation before the P permutation is drawn. The realised P correspondence rate will be recorded after construction and will not trigger regeneration, exclusion, or redesign.

## 5. Randomisation, masking, and execution order

The public manifest will expose only supplemental run identifier, target identifier, masked arm, repetition, run order, and a design-row hash. A permission-restricted sealed binding file will contain the masked condition, source identifier, source seed, donor target, source trajectory hash, and target cookbook hash. A separately sealed arm map will link masked arms to N2, P, and R2.

Targets will be assigned cyclically to three reverse-balanced two-repetition sequences after a label-blind seeded shuffle: A uses N2-P-R2 and R2-P-N2; B uses P-R2-N2 and N2-R2-P; C uses R2-N2-P and P-N2-R2. This gives 267, 267, and 266 targets in the three sequences. Each target-repetition forms a three-cell block. The 1,600 blocks will receive a frozen random order, and cells within a block follow the assigned sequence. Workers claim individual cells atomically from this immutable schedule.

Routine monitoring is outcome blind. It may expose aggregate completion count, active claims, returned model identifiers, HTTP status, record completeness, technical-failure flags, total tokens, aggregate cost, and worker heartbeat. It may not expose condition labels, individual or condition-level success, score, trajectory text, condition-specific usage, failure categories, or interim effect estimates.

## 6. Analysis and missing-data rules

The primary analysis averages valid repetitions within target-condition before constructing paired target differences. An unresolved technical failure remains missing and is never recoded as task failure. A target contributes to a contrast when both conditions in that contrast have at least one valid repetition. No scientific failure is rerun. Provider transport retries are limited to the frozen internal retry rule and do not constitute scientific reruns.

TOST is implemented on the target-level R2 minus P differences using the paired-difference mean and standard error. The lower one-sided test evaluates \(H_{01}:\tau\leq-0.05\); the upper evaluates \(H_{02}:\tau\geq+0.05\). Equivalence requires rejection of both nulls at \(\alpha=.05\). If the two-sided difference test is not significant and TOST fails, the report will state that evidence was insufficient to establish either superiority or practical equivalence.

The frozen failure taxonomy will classify each unsuccessful episode deterministically as ingredient-operation execution error, premature completion or consumption, navigation or acquisition failure, invalid-action failure, step-limit exhaustion, or other predeclared technical category using only fields defined in the analysis specification. The overlap analysis will define no-transformation targets, zero operation overlap, partial coverage, and complete coverage before unblinding. These rules, their precedence order, and the interpretation matrix in Section 9 will be included in the SUP-R0 hash bundle.

## 7. Power and budget

Power will be estimated prospectively with at least 10,000 Monte Carlo replicates per scenario using the exact target-level analysis decisions planned above. Difference-test power and TOST power will appear as separate rows. The simulation will examine 675, 750, and 800 targets; effects of 0, 0.025, 0.05, 0.075, and 0.10; target-level difference standard deviations of 0.36, 0.40, 0.45, 0.475, 0.49, and 0.50; episode missingness of 0%, 0.5%, and 1%; and plausible baseline success and within-target repetition dependence. Monte Carlo 95% confidence intervals and a Type I error audit will be reported.

The standard-deviation range is anchored to v3.2 rather than invented. The observed target-level difference SD was 0.359786 for H minus R and 0.495344 for R minus N. R2 minus P is expected to fall between these values, but the full sensitivity table is retained. The 5-percentage-point SESOI is fixed independently of the observed supplemental effect. For the two-sided difference test, the formal design gate requires at least 0.80 power at an effect of 0.05, SD 0.50, and 1% missingness. TOST power under a true difference of zero is a separately reported design property; it is not silently substituted with difference-test power. If the 800-target design does not attain 0.80 TOST power in the most conservative SD scenario, the protocol will disclose that limitation and may claim equivalence only if the frozen TOST criterion is actually met.

The proposed global supplemental caps are 4,812 paid episode starts, 175,000,000 total tokens, and USD 280. The first 12 episode starts are reserved for an excluded engineering smoke test and cannot enter the 4,800 formal records. The three model-survival probes are provider requests rather than Agent episode starts; their tokens and monetary cost must nevertheless be charged to the global supplemental token and cost caps. The token, monetary, and episode caps must be enforced jointly in one supplemental ledger. No P8 authorization carries forward. No paid call, including the model-survival probe, is allowed until a new user authorization is recorded in the supplemental authorization directory.

## 8. Concurrent replication rule

The new R2 minus N2 estimate and the old v3.2 R minus N estimate of +20.59 percentage points will always be presented as separate cohort-specific estimates; they will not be pooled. Their difference is descriptive and is not a gate, hypothesis test, sample-size adaptation rule, or rerun trigger. An absolute cross-batch difference below 5 percentage points will be described as practically consistent at the prespecified SESOI scale. An absolute difference of at least 5 percentage points will trigger explicit separate narrative presentation as cross-batch divergence, with calendar period and independently regenerated target subset noted as possible explanations. Either result leaves the R2 minus P primary analysis unchanged.

## 9. Frozen interpretation matrix

If P exceeds N2 and R2 exceeds P, the evidence supports both generic successful-trajectory scaffolding and incremental target-specific semantic pairing. If P exceeds N2 and R2 and P satisfy TOST equivalence, the main memory benefit is consistent with generic scaffolding and the semantic-assignment increment is smaller than the 5-point bound. If P is practically similar to N2 while R2 exceeds P, the memory benefit is consistent with target-specific retrieval. If P is below N2 while R2 exceeds P, permuted experience may produce negative transfer and semantic pairing may reduce that harm. If R2 minus P is significantly negative, the report will examine predeclared alignment diagnostics but will not redefine the primary question. If the difference interval crosses zero and TOST fails, the result is inconclusive rather than evidence of no semantic increment.

## 10. Abort rule and deadline amendment

Until the supervisor supplies the official submission deadline, the protocol uses 2026-09-01 as a conservative assumed submission date. SUP-R5 must record PASS no later than 2026-08-18 at 23:59:59 Europe/Copenhagen, fourteen calendar days before that assumed date. If SUP-R5 has not passed by that timestamp, collection and analysis are unconditionally aborted; the frozen protocol and hash bundle are archived in the thesis appendix, and the random-baseline experiment is reported only as future work. A supervisor-confirmed submission date may update this date only through a timestamped, outcome-blind amendment made before unblinding; the calculation remains submission date minus fourteen calendar days.

## 11. Stage gates and acceptance criteria

### Day 0 model-survival gate

Before SUP-R0 is frozen, three small paid probe calls must return the exact identifier `qwen3.7-plus-2026-05-26`. The probe stores only request configuration, returned identifier, provider usage, cost estimate, timestamps, response hash, and PASS/FAIL. A missing endpoint, non-exact identifier, or silent alias produces FAIL and terminates the supplemental plan before any material freeze.

### SUP-R0 protocol freeze

SUP-R0 passes only when the model-survival probe has passed, separate supplemental budget approval is recorded, the estimands and evidence hierarchy above are complete, the TOST rule and separate power row are present, the SD anchors are verified, the replication divergence rule is fixed, the P correspondence expectation is documented as diagnostic only, the abort date is fixed, and the protocol, analysis skeleton, failure taxonomy, overlap rules, interpretation matrix, and authorization record have a manifest of SHA-256 hashes. No supplemental outcome may exist.

### SUP-R1 materials and assignment freeze

SUP-R1 passes only when exactly 800 target rows are present; the 125 reserve targets pass the untouched audit; all 675 old R sources are reproduced; all 800 R2 sources are valid successful bank experiences; the new permutation preserves the source multiset and per-source reuse counts exactly; all 800 P sources differ from R2; donor fixed points are zero; construction examines none of the forbidden matching or outcome variables; and public manifest, sealed bindings, inventory, seeds, candidate hashes, and rejection reasons are archived.

### SUP-R2 power and budget freeze

SUP-R2 passes only when the planned target-level difference test and TOST have separate simulated power estimates; the 5-point effect, SD 0.50, and 1% missingness difference-test scenario reaches 0.80 power; the zero-effect two-sided rejection rate lies between 4.5% and 5.5%; Monte Carlo intervals, full sensitivity results, code, package versions, and random seeds are archived; the design remains 800 targets and two repetitions; and the approved episode, token, and monetary caps match the runner configuration.

### SUP-R3 engineering preflight

SUP-R3 passes only when a four-worker local mock shows no duplicate claims or overwrites, atomic finalisation and resume reconciliation work, caps stop new claims, and 12 paid excluded episodes cover every condition and repetition without using a formal target. All excluded responses must return the exact frozen model identifier; prompt context must not truncate; environment and scorer must agree; P and R2 prompts must be byte-identical after replacement of the source block by a constant token; N2 must use the same empty wrapper; and no condition success summary may be inspected.

### SUP-R4 blind formal collection

SUP-R4 uses only the immutable manifest and frozen four-worker runner. Any model identifier drift, prompt or binding hash drift, environment drift, unresolved duplicate claim, public condition leakage, or imminent cap violation stops new claims. Scientific failure, invalid action, and step-limit exhaustion remain outcomes and are never rerun.

### SUP-R5 blind technical acceptance

SUP-R5 passes only when the manifest contains exactly 4,800 unique cells with three conditions and two repetitions for every target; every cell has one technical state; at least 99% are valid; the maximum condition missingness difference is no more than one percentage point; every target-condition has at least one valid record; all returned identifiers and frozen hashes match; no unauthorised scientific rerun occurred; every paid call appears in the single supplemental ledger; all caps were respected; and the report remains free of condition outcomes and effect directions.

### SUP-R6 single frozen analysis

After SUP-R5 PASS, the analysis bundle receives its final SHA-256 manifest and runs once. It produces the R2 minus P effect, two-sided test, bootstrap interval, TOST, Holm-adjusted secondary family, and predeclared diagnostics. Any reconstruction or correction after this run requires a transparent amendment and preservation of the first output. Failure and overlap diagnostics remain descriptive.

### SUP-R7 reporting

The thesis will describe the study as “a prospectively frozen post-main-study supplemental random-baseline experiment.” Results will appear in a self-contained section that can be removed without changing the v3.2 Methods, Results, or Discussion claims. The report will state that the protocol and assignments were frozen after the main study but before any supplemental outcomes existed.
