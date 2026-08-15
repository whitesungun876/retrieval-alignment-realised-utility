# From Retrieval Alignment to Realised Utility

Public reproduction materials for Jieyu Lian's MSc thesis, **Evaluating Experience Retrieval for an LLM Agent in TextWorldExpress CookingWorld**.

The thesis reports one retained three-condition main-study analysis and two sequential follow-ups:

1. **Main study:** No Memory (N), Raw Semantic retrieval (R), and De-lexicalised Semantic retrieval (D).
2. **Assignment follow-up:** target-specific Raw Semantic assignment (R2) versus a distribution-matched permutation of the same source vector (P), with concurrent No Memory (N2).
3. **Trajectory-control follow-up:** a concrete permuted trajectory (P) versus a paired abstract scaffold (C).

The original main-study protocol also included a Hybrid (H) condition. Because H and D produced byte-identical prompts for all 675 formal targets, H does not identify a graph-stage intervention. Its frozen outputs are retained only where needed to preserve the original audit record.

## Repository contents

- `main_study/`: frozen protocol, manifests, retrieval selections, derived episode outcomes, analysis outputs, and analysis code.
- `assignment_followup/`: frozen supplemental protocol, realised derangement, manifests, derived episode outcomes, analysis outputs, and analysis code.
- `trajectory_control_followup/`: frozen P/C protocol, paired materials, manifests, a public outcome-only episode file, analysis outputs, and analysis code.
- `figures/`: figure-generation code and final graph-free figures.
- `thesis/`: the final submitted thesis PDF.
- `verify_reported_results.py`: recomputes the principal target-weighted point estimates from the public outcome files.
- `MANIFEST.sha256`: SHA-256 inventory of the copied frozen artefacts.

## Public-data boundary

This repository intentionally excludes provider raw response payloads, API credentials, signed service URLs, keychain contents, emails, authorisation correspondence, transient worker state, and local service logs. The included `*_episode_outcomes*.jsonl` files contain only experimental identifiers, condition labels, repetition numbers, technical-missingness flags, and terminal-success outcomes. They are sufficient to recompute the reported target-weighted point estimates, but not to replay the paid hosted-model calls.

Some frozen files preserve historical local paths or environment-variable names as provenance. They contain no credential values.

## Verify the reported point estimates

The verification script uses only the Python standard library:

```bash
python verify_reported_results.py
```

Expected principal output:

- main `R−N`: `+20.592593` percentage points;
- main `D−R`: `+0.888889` percentage points;
- assignment `R2−P`: `+1.375000` percentage points;
- assignment `P−N2`: `+21.312500` percentage points;
- trajectory control `P−C`: `+20.062500` percentage points.

Confidence intervals, sign-flip tests, Holm correction, and TOST outputs are preserved in the frozen result files and their corresponding analysis code.

## Software environment

The experiments used TextWorldExpress 1.1.0, BGE-M3 for retrieval representations, and the hosted snapshot `qwen3.7-plus-2026-05-26`. Exact experiment settings are recorded in the configuration and manifest files for each study.

## Citation

See `CITATION.cff`. No software or data licence is granted by this repository unless one is added explicitly by the author.
