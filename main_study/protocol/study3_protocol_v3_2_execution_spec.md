# Study 3 Protocol v3.2

## From Semantic to Structural Experience Retrieval: A Replication-and-Extension Study in TextWorldExpress CookingWorld

**Document purpose:** Executable specification for Codex  
**Protocol status:** Prospective replacement for Protocol v3.1  
**Scientific outcome status:** No Protocol v3.2 formal Agent outcome may be inspected before blind technical acceptance  
**Primary analysis unit:** CookingWorld target task  
**Primary outcome:** Official terminal success  
**Primary comparison:** Hierarchical Structural Retrieval (`H`) minus Raw Semantic Retrieval (`R`)

---

# 1. Study objective

This study evaluates whether adding procedural structure to experience retrieval improves the downstream success of an LLM Agent in TextWorldExpress CookingWorld.

The primary research question is:

> Does a de-lexicalised, graph-re-ranked experience retriever improve terminal task success relative to conventional raw-text semantic retrieval?

The study is a replication-and-extension experiment. Its components have published precedents, but their integration in CookingWorld is new:

| Component | Published precedent | Status in this study |
|---|---|---|
| Inference-time retrieval of past query–execution experience | ExpeL; Experience-Following; ExpRAG | Protocol-level adaptation |
| Fixed Top-1 vector retrieval | Experience-Following AgentDriver implementation | Retained selection rule |
| `BAAI/bge-m3` embedding backbone | SGA-MCTS | Retained encoder family |
| Raw-text versus de-lexicalised retrieval | SGA-MCTS | Simplified Top-1 adaptation |
| Dense Top-\(M\) candidate retrieval followed by graph-kernel re-ranking | RGER | Cross-domain architecture adaptation |
| \(M=64\) candidate depth | One of the settings evaluated by RGER; also present in its official `rerank64` workflow | Frozen published-range setting |
| Weisfeiler–Lehman graph comparison | RGER for richly labelled mathematical reasoning graphs; Shervashidze et al. (2011) | Cross-domain kernel adaptation |
| Ingredient–operation recipe graph | No identical published implementation | CookingWorld-specific operationalisation |
| Common raw-trajectory renderer across retrieval conditions | No specific source required | Experimental control introduced by this study |

The study must not be described as an exact reproduction of RGER, SGA-MCTS, Experience-Following, or any other single system. The correct description is:

> Published retrieval components are integrated and evaluated in a new interactive environment.

# 2. Research questions and hypotheses

## RQ1: Experience utility

> Does a raw-semantically retrieved successful trajectory improve terminal success relative to no retrieved experience?

Comparison: `R − N`  
Status: Secondary

## RQ2: Complete method effect

> Does Hierarchical Structural Retrieval improve terminal success relative to Raw Semantic Retrieval?

Comparison: `H − R`  
Status: Sole primary comparison

## RQ3: Mechanistic decomposition

> Does ingredient-name de-lexicalisation improve retrieval utility, and does explicit recipe-graph re-ranking provide an additional increment?

Comparisons:

- `D − R`: effect of changing the retrieval representation from raw ingredient text to anonymous ingredient roles;
- `H − D`: added effect of graph re-ranking after de-lexicalised semantic retrieval.

Status: Mechanistic secondary family

## Interpretation boundary

`H − R` estimates the effect of the complete retrieval package. It combines de-lexicalisation and structural re-ranking and is not the pure causal effect of the graph component.

`D − R` isolates retrieval-time ingredient de-lexicalisation because the selected trajectory is shown to the Agent in raw form under both conditions.

`H − D` isolates the selection effect of graph re-ranking because `D` and `H` use the same de-lexicalised semantic representation and the same final experience renderer.

No result licenses a claim that the Agent possesses human-like analogical reasoning or general structure-mapping ability.

# 3. Protocol transition from v3.1

Protocol v3.1 used `BAAI/bge-small-en-v1.5` and a Top-40 structural shortlist. Protocol v3.2 changes the embedding backbone to `BAAI/bge-m3` and the structural shortlist to \(M=64\). These changes can alter the sources selected under `R`, `D`, and `H`; v3.1 and v3.2 therefore define different interventions.

Before any v3.2 development:

1. Stop the v3.1 formal runner.
2. Do not inspect v3.1 terminal success, condition summaries, trajectories grouped by condition, or pairwise effects.
3. Preserve all 76 completed v3.1 records, the raw manifest, run order, budget ledger, source hashes, prompt hashes, and software hashes.
4. Record v3.1 as:

   > Superseded after 76 of 2,800 planned episodes, before scientific outcome inspection, because the retrieval backbone and candidate depth were revised for closer methodological alignment with the published component studies.

5. Exclude all v3.1 episodes from v3.2 confirmatory and secondary analyses. Do not reuse the v3.1 Agent outputs for power analysis, target selection, prompt development, or error analysis.
6. Reusing environment code, bank-construction code, the successful experience bank, action interface, logging infrastructure, and replay validation is allowed after their hashes and continued validity are checked.
7. Prefer a fresh v3.2 formal target seed range. If task availability requires reuse of the same target seeds, document that the decision was outcome-blind and rerun every condition from the beginning. Do not combine old and new executions.

The transition note must be written and hashed before v3.2 formal retrieval is generated.

# 4. Environment and task interface

## 4.1 Environment

- Environment: TextWorldExpress `1.1.0`
- Game: CookingWorld
- Experience-bank fold: `train`
- Development and excluded pilot fold: `dev`
- Formal target fold: `test`
- Configuration:

```text
numLocations=3
numIngredients=2
numDistractorItems=0
includeDoors=0
limitInventorySize=0
```

- Maximum episode length: 50 environment actions
- Terminal outcome: the official environment success signal for completing and consuming the required recipe

The exact installed package artefact, Java version, Python version, wrapper version, generation arguments, and environment hash must be recorded. A version label by itself is insufficient.

## 4.2 Cookbook-aligned target specification

The standard CookingWorld initial observation only instructs the Agent to inspect the cookbook; it does not expose the recipe. Using that generic observation as the retrieval query would make `R`, `D`, and `H` procedurally uninformative.

For each frozen seed, use a deterministic cookbook-materialisation function \(\psi\) that returns exactly the cookbook task specification available within that task. The function may expose:

- ingredient names;
- required transformations;
- operation order expressed by the cookbook;
- other text that is part of the cookbook specification.

It must not expose:

- item locations;
- room layout beyond information explicitly written in the cookbook;
- legal-action sequence;
- hidden simulator state;
- gold trajectory;
- terminal outcome;
- target–source structural label;
- retrieval result;
- seed-derived privileged metadata.

The materialised target cookbook must be inserted in the same prompt position and with byte-identical content under `N`, `R`, `D`, and `H`. Cookbook materialisation must not execute an environment action or consume one of the 50 steps.

## 4.3 Action interface

At each environment step:

1. Obtain the current admissible-action list.
2. Sort the actions using one frozen deterministic rule.
3. Display the actions as a zero-based numbered list.
4. Require the Agent to return one integer index.
5. Accept ASCII digits representing an in-range index.
6. Treat malformed or out-of-range outputs as invalid actions according to one frozen rule.

The Agent does not freely generate TextWorld command strings. This control reduces syntax failures and focuses the study on decision selection. It also limits external validity to indexed legal-action choice and must be stated as such.

# 5. Agent policy

Use one formal Agent model:

| Parameter | Frozen value |
|---|---|
| Provider | Alibaba Cloud Model Studio, international endpoint |
| Requested model | `qwen3.7-plus-2026-05-26` |
| Thinking mode | Enabled |
| Temperature | `0.0` |
| Maximum output per request | 2,048 tokens |
| Request timeout | 120 seconds |
| Maximum transport/API retries | 2 |
| Maximum environment steps | 50 |

Record the provider-returned model identifier, date, time, request identifier, token usage, latency, and finish reason for every call. Temperature zero does not guarantee identical reasoning-service outputs; repeated episodes remain necessary.

Retries are permitted only for prespecified technical failures such as transport errors, timeouts without a valid response, or provider-declared transient failures. Never retry because the Agent chose a poor action, produced an invalid index, or failed the task.

# 6. Frozen successful experience bank

Construct one read-only bank from the CookingWorld `train` fold. The target size is approximately 5,000 source experiences; the exact included count and bank hash must be recorded before formal retrieval.

Every bank entry must contain:

- unique source seed and neutral source identifier;
- complete materialised source cookbook;
- one canonical successful trajectory;
- the original sequence of observations and actions;
- official terminal-success record;
- official replay result;
- raw retrieval document;
- de-lexicalised retrieval document;
- recipe graph;
- canonical Agent-facing experience rendering;
- text, trajectory, action, navigation, and transformation counts;
- content and representation hashes.

Every included experience must pass official replay under the same frozen environment version. Replay success must be 100%.

If multiple successful trajectories exist for one source task, select one using a rule frozen before formal target retrieval. Recommended rule:

1. shortest successful action sequence;
2. then lowest invalid-action count;
3. then label-blind hash of canonical trajectory content.

Do not select a source trajectory based on similarity to formal targets or on any downstream Agent outcome.

Deduplicate byte-identical source cookbooks and byte-identical canonical trajectories using a frozen rule. Train/dev/test seeds must be disjoint. Report exact cookbook duplicates or recipe-signature duplicates across train and formal test as diagnostics rather than removing them after retrieval.

# 7. Embedding model

Use the same frozen dense encoder for `R`, `D`, and the semantic stage of `H`:

- model: `BAAI/bge-m3`;
- source: one locally frozen Hugging Face snapshot;
- revision: resolve and record the exact immutable commit hash before creating any v3.2 formal embedding;
- library: freeze the exact `FlagEmbedding`, `transformers`, `torch`, tokenizer, and numerical-library versions;
- retrieval mode: dense embedding only;
- output normalisation: L2;
- similarity: cosine similarity, or equivalently the inner product of L2-normalised vectors;
- precision: use one frozen precision mode for all embeddings;
- batching: deterministic evaluation mode with no dropout;
- input prefix: none for either target or source, unless a different symmetric template is justified and frozen on development data before formal retrieval;
- maximum input length and truncation: record explicitly; formal cookbook truncation must equal zero.

The encoder is inherited from SGA-MCTS, not RGER. RGER uses a task-specific contrastively trained retriever in its main configuration and `all-MiniLM-L6-v2` in an off-the-shelf ablation. The thesis must not claim that RGER used `bge-m3`.

Run a deterministic embedding smoke test twice and verify that the stored vectors and rankings are identical within a frozen numerical tolerance.

# 8. Retrieval documents

## 8.1 Raw document

The raw target query is the complete materialised target cookbook. The raw source key is the complete materialised source cookbook.

Do not embed the target's generic initial “inspect the cookbook” instruction. Do not include the source trajectory in the default retrieval key, because query-to-query retrieval keeps the target and source representations comparable and prevents trajectory length from dominating similarity.

## 8.2 De-lexicalised document

Define a deterministic transformation \(\phi\):

1. identify each recipe ingredient from the visible cookbook grammar;
2. assign `role_1`, `role_2`, and so on according to first appearance in that cookbook;
3. replace every occurrence of the ingredient name consistently;
4. preserve operation words, sentence order, operation order, punctuation, and all non-ingredient content;
5. do not reorder roles, chains, or sentences;
6. do not inspect target–source correspondence, graph score, retrieval output, or Agent outcome.

Example:

```text
Raw:
Chop and fry the carrot. Slice and grill the potato.

De-lexicalised:
Chop and fry role_1. Slice and grill role_2.
```

This manipulation removes concrete ingredient identity; it does not remove every lexical difference. Claims must use “ingredient-name de-lexicalisation,” not the broader phrase “removal of lexical interference.”

# 9. Recipe graph

## 9.1 Graph definition

Construct one directed, discretely labelled graph from each materialised cookbook.

For each recipe ingredient:

- create one unique ingredient node;
- assign the node attribute label `INGREDIENT`;
- do not place the concrete ingredient name in any graph attribute.

For each required transformation:

- create one operation node;
- assign the operation label, for example `CHOP`, `SLICE`, `FRY`, `GRILL`, or `ROAST`;
- create a directed edge from the ingredient node to its first operation;
- create directed edges between successive operations for that ingredient.

Example:

```text
INGREDIENT_A → CHOP → FRY
INGREDIENT_B → SLICE → GRILL
```

`INGREDIENT_A` and `INGREDIENT_B` are unique internal node identifiers, but both carry the same semantic node label `INGREDIENT`. The graph is therefore invariant to concrete ingredient names and arbitrary renaming of ingredient nodes while preserving the grouping and order of operations.

The formal parser must use only the visible materialised cookbook. Gold environment metadata may be used on excluded data to validate the parser but not to construct formal retrieval graphs.

## 9.2 Direction-aware Weisfeiler–Lehman features

Use a frozen normalised Weisfeiler–Lehman subtree-feature implementation suitable for discretely labelled recipe graphs. Because operation order is directional, the implementation must preserve edge direction. At every WL update, incoming and outgoing neighbour labels must be distinguishable. If the selected graph library does not preserve directed neighbourhoods, encode direction explicitly or implement direction-aware WL relabelling.

Freeze:

- graph library and version;
- WL implementation;
- number of WL iterations;
- node-label vocabulary;
- treatment of in-neighbours and out-neighbours;
- feature-vector construction;
- normalisation;
- numerical precision.

Graph similarity is the cosine similarity between normalised WL feature-count vectors, equivalently a normalised WL subtree kernel.

Required unit tests:

1. **Ingredient renaming invariance:** replacing `carrot` with `potato` without changing operations must not change the graph feature representation.
2. **Ingredient-order invariance:** swapping the textual order of two complete ingredient chains must not change graph similarity after anonymous graph construction.
3. **Operation identity sensitivity:** replacing `FRY` with `GRILL` must change graph features.
4. **Operation-order sensitivity:** `CHOP → FRY` must differ from `FRY → CHOP`.
5. **Role-allocation sensitivity:** assigning `FRY` to a different ingredient chain must change the graph when the resulting multiset of chains differs.
6. **Determinism:** repeated construction produces byte-identical serialised graphs and feature vectors.

The WL choice follows RGER's rationale: WL is used for graphs with informative discrete node attributes. CookingWorld recipe graphs have explicit ingredient-role and operation-type labels. This is a principled kernel adaptation, not evidence that RGER used CookingWorld recipe graphs.

# 10. Four experimental conditions

## N — No Memory

Inputs:

- complete target cookbook;
- current observation;
- current admissible-action list;
- explicitly empty experience block.

No retrieval is performed.

## R — Raw Semantic Retrieval

1. Encode the raw target cookbook with frozen `BAAI/bge-m3`.
2. Compare it with all raw source-cookbook embeddings using cosine similarity.
3. Select the highest-scoring source.
4. Resolve exact score ties using the frozen label-blind content hash.
5. Show the selected source through the canonical raw-trajectory renderer.

## D — De-lexicalised Semantic Retrieval

1. Apply \(\phi\) to the target cookbook.
2. Compare its frozen `bge-m3` embedding with all de-lexicalised source-cookbook embeddings.
3. Select cosine Top-1.
4. Resolve exact ties using the same label-blind content hash.
5. Show the selected source through the same canonical raw-trajectory renderer.

`D` changes only the representation used to select a source. It does not show anonymous roles to the Agent.

## H — Hierarchical Structural Retrieval

1. Use the `D` cosine ranking over the complete bank.
2. Retain the first 64 candidates.
3. Calculate direction-aware normalised WL graph similarity between the target recipe graph and each candidate graph.
4. Rank the 64 candidates by:
   - descending graph similarity;
   - then descending `D` cosine similarity;
   - then ascending frozen label-blind hash.
5. Select Top-1.
6. Show the selected source through the same canonical raw-trajectory renderer.

There is no \(\beta\)-weighted semantic–structural formula in this protocol. Semantic retrieval defines the candidate set; graph similarity defines the primary re-ranking score. `H` is hierarchical structural retrieval, not a literal implementation of SGA-MCTS's weighted symbolic–semantic score.

# 11. Canonical experience presentation

After source selection, `R`, `D`, and `H` must use the same deterministic renderer. The renderer includes:

- neutral source label;
- source cookbook;
- selected source observations;
- selected source actions in their original order;
- official indication that the source trajectory succeeded.

It must not include:

- retrieval condition;
- embedding score;
- graph score;
- anonymous roles;
- graph representation;
- target–source mapping;
- `R+` or `R−` labels;
- instructions marking which actions should transfer.

The outer prompt, target cookbook position, action interface, model, context limit, and renderer are identical across retrieval conditions. If two retrieval conditions select the same source, their prompts must be byte-identical, but their formal Agent executions remain independent because the design specifies two repeated executions per condition.

# 12. Partitions

Create and hash mutually disjoint partitions:

| Partition | Purpose |
|---|---|
| Development | Representation code, WL settings, parser development, non-outcome diagnostics |
| Parser validation | Excluded graph and de-lexicalisation validation |
| Experience bank | Successful `train` experiences |
| Engineering pilot | API reliability, cost, variance, and prompt checks |
| Formal target | Primary experiment |
| Reserve | Predefined technical replacement only |

No development, pilot, or bank source task may enter the formal target partition. No formal Agent outcome may influence partition membership.

# 13. P0–P10 execution plan

## P0 — Close v3.1 outcome-blind

Deliverables:

- v3.1 stop note;
- completed-record count;
- preserved manifest and ledger;
- hash inventory;
- written confirmation that no scientific outcome was inspected;
- exclusion rule for all v3.1 episodes.

Pass requirement: transition decision and all preserved artefacts are documented before v3.2 formal retrieval.

## P1 — Freeze environment, partitions, and interfaces

Deliverables:

- environment manifest;
- partition manifest;
- cookbook-materialisation tests;
- action-interface tests;
- canonical renderer snapshot.

Pass requirements:

- cross-partition seed overlap: zero;
- cookbook text matches the task-accessible cookbook: 100%;
- target cookbook bytes identical across all four conditions: 100%;
- hidden fields exposed: zero;
- environment and renderer deterministic.

## P2 — Freeze and validate the experience bank

Deliverables:

- exact bank count;
- official replay report;
- source-selection rule;
- deduplication report;
- final bank hash;
- raw and de-lexicalised documents;
- canonical trajectories.

Pass requirements:

- official replay success: 100% of included sources;
- unresolved malformed records: zero;
- test-fold sources in bank: zero;
- reproducible bank construction: 100%.

## P3 — Freeze BGE-M3 and representations

Deliverables:

- local model snapshot;
- immutable model revision;
- encoder configuration;
- software versions;
- raw/de-lexicalised embeddings;
- embedding hashes and deterministic smoke tests.

Pass requirements:

- same encoder and numerical configuration for `R`, `D`, and `H`;
- repeated embedding rankings identical;
- cookbook truncation: zero;
- ingredient replacement deterministic: 100%;
- gold-label or Agent-outcome access: zero.

## P4 — Validate recipe graphs and WL features

Deliverables:

- parser specification;
- independent labelled validation set;
- exact graph match;
- node and edge precision/recall/F1;
- six required invariance/sensitivity tests;
- graph and WL software hashes.

Recommended pass requirements:

- exact graph match at least 0.95;
- graph-component macro-F1 at least 0.90;
- malformed formal graph rate: zero;
- operation-order sensitivity test: 100%;
- ingredient-renaming and ingredient-order invariance tests: 100%;
- repeated graph/WL output equality: 100%.

Any threshold change requires development work and a new excluded validation set. Do not tune on formal targets.

## P5 — Freeze offline retrieval

Generate complete `R`, `D`, and `H` rankings for every proposed formal target before any v3.2 formal Agent call.

Report:

- Top-1 selections and source hashes;
- `R`/`D`/`H` pairwise agreement;
- Top-64 source overlap;
- structural-match rate using a diagnostic gold recipe signature unavailable to retrievers;
- structural-match Recall@64;
- exact and near ties;
- graph-score tie multiplicity;
- Top-1/Top-2 margins;
- selected-source reuse concentration;
- source-length and recipe-complexity distributions;
- candidate-order permutation stability.

Pass requirements:

- rankings reproducible: 100%;
- candidate-order permutation stability: 100%;
- tie-break independent of condition labels, bank position, and outcomes;
- valid Top-1 source for every target and method;
- Recall@64 sufficiently high for the structural stage to access relevant candidates;
- `H`–`R` intervention variation sufficient for prospective power.

Do not impose a convenient fixed disagreement percentage. Use the observed outcome-blind selection pattern in prospective power simulation.

## P6 — Excluded engineering pilot

Use only excluded pilot targets.

Run `N`, `R`, `D`, and `H` to verify:

- correct prompt assembly;
- correct source injection;
- API validity;
- response parsing;
- scorer consistency;
- prompt length and truncation;
- within-target stochasticity;
- token use;
- cost;
- wall-clock time.

The pilot may estimate baseline success and repetition disagreement. It must not be used to choose targets, retrieval settings, or a protocol version because one condition produced a favourable outcome.

Recommended technical requirements:

- valid API response rate at least 99%;
- complete logs: 100%;
- scorer agreement with official environment: 100%;
- target cookbook mismatch: zero;
- source/condition binding errors: zero;
- prompt truncation: zero.

## P7 — Prospective power, budget, and final freeze

The initial planning design is:

- up to 350 independent formal targets;
- four conditions per target;
- two independent episodes per target × condition;
- up to 2,800 paid episodes.

Do not assume the v3.1 power value of 0.8152 remains valid. Recalculate power using:

- the frozen v3.2 `H`–`R` source-agreement pattern;
- pilot-estimated baseline success;
- target heterogeneity;
- within-target repetition variability;
- two repetitions per condition;
- a two-sided alpha of 0.05;
- SESOI of five percentage points;
- at least 10,000 prospective simulations per design point.

Required power:

- estimated power at least 0.80 for the primary `H − R` test;
- report Monte Carlo uncertainty;
- report sensitivity for 5-, 10-, and 15-percentage-point effects.

If 350 targets do not reach the requirement, do not silently continue. Increase the prospectively selected target count, increase repetitions if justified, or declare No-Go.

Before P8, freeze:

- final target count;
- repetitions;
- formal targets and reserves;
- run order;
- arm masking;
- Agent model;
- all prompts;
- embedding and graph settings;
- analysis code tested on simulated data;
- technical-retry and missing-data rules;
- token and cost ceilings.

Obtain explicit user approval for the final paid-API budget before formal execution.

## P8 — Blind formal collection

For each formal target:

- run `N`, `R`, `D`, and `H`;
- run two independent repetitions per condition;
- randomise and balance condition order within target;
- interleave arms across provider batches and time;
- begin each episode from a fresh model context and identical environment seed;
- use masked labels such as `arm_1`–`arm_4`;
- store the condition map separately from routine monitoring output.

Routine monitoring may expose:

- run completion;
- HTTP/API status;
- tokens;
- cost;
- latency;
- requested and returned model identifiers;
- log completeness.

It must not expose:

- terminal success by arm;
- trajectories grouped by arm;
- `H − R`, `R − N`, `D − R`, or `H − D`;
- condition-specific error summaries.

Stop automatically if any frozen episode, token, or cost ceiling is reached.

## P9 — Blind technical acceptance

Before unblinding, verify:

- planned versus observed episode counts;
- unique run identifiers;
- target × masked-arm × repetition completeness;
- prompt, source, cookbook, model, and configuration hashes;
- correct environment seeds;
- scorer reproducibility from raw trajectories;
- retry compliance;
- technical failures and missingness;
- absence of secret/API keys in stored artefacts.

Classify all deviations while arm labels remain masked. Do not delete records based on scientific outcomes.

Pass requirements:

- every planned cell has a record or preregistered unresolved technical-failure status;
- no source/arm binding errors;
- no silent model or prompt drift;
- scorer reproducibility: 100%;
- final missingness within the frozen tolerance.

## P10 — Unblind and analyse

Only after P9 passes:

1. reveal the condition map;
2. run the frozen analysis script once;
3. generate all tables and figures;
4. preserve the first analysis output and its hash;
5. label any later analysis as sensitivity or exploratory.

# 14. Outcome and statistical analysis

## 14.1 Primary outcome

For each episode:

```text
terminal_success = 1
```

only if the official environment indicates successful completion and consumption of the required recipe within 50 steps. Otherwise:

```text
terminal_success = 0
```

Technical failures are handled by the frozen retry and missing-data policy, not recoded according to whether they favour a condition.

## 14.2 Target-level aggregation

For every target and condition, average the two binary episode outcomes. The resulting target-condition value can be `0`, `0.5`, or `1`.

The independent unit is the target. The two repetitions are nested measurements and must not be analysed as independent tasks.

## 14.3 Primary estimate

For each target, subtract its `R` mean from its `H` mean. Average these target-level differences across all formal targets.

Report:

- risk difference in percentage points;
- 10,000-resample target-cluster bootstrap 95% confidence interval;
- two-sided target-level sign-flip/randomisation p-value;
- exact target count;
- number of targets for which `H` and `R` selected the same source;
- number for which they selected different sources.

The all-target estimate is primary. A disagreement-only subset may be reported as an exploratory mechanism diagnostic but cannot replace or rescue the all-target result.

## 14.4 Secondary comparisons

Estimate:

- `R − N`;
- `D − R`;
- `H − D`.

Use target-level differences and target-cluster confidence intervals. Apply Holm correction across these three non-primary comparisons.

## 14.5 Sensitivity analysis

Fit a logistic mixed-effects model with:

- terminal success as the binary outcome;
- condition as a fixed effect;
- target random intercept;
- repetition nested within target × condition as repeated observation.

This model is a sensitivity analysis and does not replace the target-level primary analysis.

## 14.6 Offline and process diagnostics

Report descriptively:

- structural-match rates of selected sources;
- retrieval agreement;
- graph and semantic score distributions;
- selected-source reuse;
- invalid actions;
- operation-to-ingredient errors;
- within-chain order errors;
- first irreversible recipe error;
- navigation or step-limit failure.

Do not infer a per-target negative-transfer event by arbitrarily pairing two independent stochastic API calls.

# 15. Result interpretation rules

| Observed pattern | Permitted interpretation |
|---|---|
| `R > N` | Raw-semantically retrieved past experience adds utility beyond the complete current cookbook |
| `D > R`, `H ≈ D` | The package improvement is primarily associated with ingredient-name de-lexicalisation |
| `H > D` | Recipe-graph re-ranking adds utility beyond de-lexicalised semantic retrieval |
| `H > R` | The complete de-lexicalised structural retrieval pipeline improves success relative to raw semantic retrieval |
| Offline structural match improves but success does not | Better retrieval alignment does not translate into Agent utility under this interface |
| `H < R` | Structural abstraction or re-ranking discards information useful to raw semantic retrieval |
| All conditions similar | Memory selection may not be the main bottleneck, possibly because the complete cookbook already specifies the target procedure |

Never interpret a null result as proof that structure is irrelevant in all Agent memory systems. Never interpret a positive result as evidence of human-like analogy.

# 16. Required result placeholders

Do not populate these fields until P10.

## Offline retrieval

| Method | Structural-match rate | Unique Top-1 sources | Exact ties | Median source reuse |
|---|---:|---:|---:|---:|
| `R` | [ ] | [ ] | [ ] | [ ] |
| `D` | [ ] | [ ] | [ ] | [ ] |
| `H` | [ ] | [ ] | [ ] | [ ] |

## Formal success

| Condition | Targets | Episodes | Success rate | 95% target-cluster CI |
|---|---:|---:|---:|---:|
| `N` | [ ] | [ ] | [ ] | [ ] |
| `R` | [ ] | [ ] | [ ] | [ ] |
| `D` | [ ] | [ ] | [ ] | [ ] |
| `H` | [ ] | [ ] | [ ] | [ ] |

## Contrasts

| Contrast | Estimate | 95% CI | Raw p | Adjusted p | Status |
|---|---:|---:|---:|---:|---|
| `H − R` | [ ] | [ ] | [ ] | N/A | Primary |
| `R − N` | [ ] | [ ] | [ ] | [ ] | Secondary |
| `D − R` | [ ] | [ ] | [ ] | [ ] | Mechanistic |
| `H − D` | [ ] | [ ] | [ ] | [ ] | Mechanistic |

# 17. Reproducibility artefacts

Archive:

- v3.1 outcome-blind supersession note;
- v3.1 preserved records and hashes;
- v3.2 protocol and hash;
- environment manifest;
- partition manifest;
- successful experience bank and replay report;
- BGE-M3 snapshot revision and software manifest;
- raw and de-lexicalised documents;
- embedding hashes;
- recipe graphs and WL features;
- parser validation;
- complete offline rankings;
- tie and permutation audits;
- pilot report;
- power simulation and code;
- budget approval and ceilings;
- blind formal manifest;
- raw interaction logs;
- technical-acceptance report;
- frozen analysis code;
- final outputs and figures.

Do not store API keys, authentication headers, or other secrets in the reproducibility package.

# 18. Stop conditions for Codex

Codex must stop and request user direction if:

1. accessing or changing the current runner would expose v3.1 scientific outcomes;
2. the exact BGE-M3 revision cannot be frozen;
3. the formal bank or target partitions overlap;
4. official replay is below 100% for included experiences;
5. cookbook materialisation exposes hidden information;
6. the graph implementation fails operation-order sensitivity or ingredient-renaming invariance;
7. the v3.2 offline retrieval pattern cannot support the required prospective power;
8. the required formal target count exceeds available tasks;
9. the projected paid-API budget exceeds the approved ceiling;
10. a model, environment, prompt, or source hash drifts after formal freeze.

Codex must not solve a No-Go condition by inspecting outcomes, deleting inconvenient targets, silently changing thresholds, or lowering the power requirement.

# References

Lin, Y., Zhong, B., Jiang, S., Siebert, J., & Chen, Q. (2025). Reasoning graph enhanced exemplars retrieval for in-context learning. *Proceedings of COLING 2025*, 9737–9759. https://aclanthology.org/2025.coling-main.651/

Shervashidze, N., Schweitzer, P., van Leeuwen, E. J., Mehlhorn, K., & Borgwardt, K. M. (2011). Weisfeiler–Lehman graph kernels. *Journal of Machine Learning Research, 12*, 2539–2561. https://jmlr.org/papers/v12/shervashidze11a.html

Xie, X., Xue, D., Yao, W., Feng, M., Zhou, W., Qi, X., Li, H., & Zhang, P. (2026). SGA-MCTS: Decoupling planning from execution via training-free atomic experience retrieval. *Findings of ACL 2026*, 1176–1193. https://aclanthology.org/2026.findings-acl.60/

Xiong, Z., Lin, Y., Xie, W., He, P., Liu, Z., Tang, J., Lakkaraju, H., & Xiang, Z. (2026). How memory management impacts LLM agents: An empirical study of experience-following behavior. *Proceedings of ACL 2026*, 623–645. https://aclanthology.org/2026.acl-long.27/

Zhao, A., Huang, D., Xu, Q., Lin, M., Liu, Y.-J., & Huang, G. (2024). ExpeL: LLM agents are experiential learners. *Proceedings of the AAAI Conference on Artificial Intelligence, 38*(17), 19632–19642. https://doi.org/10.1609/aaai.v38i17.29936
