# Outcome-blind engineering amendment: record schema compatibility

Date: 2026-08-12 (Europe/Copenhagen)

Scope: record-completeness and adapter compatibility only. No P/C material,
renderer, target, assignment, manifest, binding, model, environment, estimand,
analysis, outcome field, or existing immutable raw record was modified.

## Trigger and compatibility rule

The first four records of the separately authorized retry were valid outputs of
the reused phase-4 runner. They had top-level schema
`publication_followup_phase4_raw_trajectory_v1` plus the adapter extension
`protocol_control_pc_episode_v1`. The reused frozen completeness predicate
accepted only `study3_v3_2_episode_v1`, so it classified all four records as
incomplete and stopped collection.

The amended predicate accepts either:

1. a record accepted by the unchanged frozen Study 3 predicate; or
2. the exact phase-4 schema plus exact P/C extension, provided run ID, start and
   finish timestamps, trajectory list, LLM mapping, and experimental-design
   mapping are present.

No success, score, terminal reason, condition outcome, or effect field enters
this compatibility predicate.

The ledger reconciliation verifies every raw-record SHA-256 before refreshing
only derived technical fields (`record_complete`, `technical_failure`, tokens,
cost, and the amendment marker). It never rewrites a raw record.

## Hash audit

Pre-amendment:

- `src/scheduler.py`: `ef94e78ea105aa4eb960af7a511f7b6cbd8b131f3810ebc38a970c07c4e6c39a`
- `src/execution.py`: `64af6a76e4dbcdfe77aeb3d882e7c74d04761f562f62344f0bff7486b6f695c6`
- `src/episode_adapter.py`: `380c4707ea2fe51a533ec369cfbb4e9b3b85dc1a4b01b50451aac5345a896e7d`
- `tests/test_protocol_control.py`: `6034ca7129c81dd3de18473d4eba742eeecf2198e468a851d0a1c9219d28716d`
- smoke ledger: `1cd7de6e26d060848542bb77be73db1a9e0bb908a41371e9ca463de9b5ba41cc`

Post-amendment validation:

- `src/scheduler.py`: `a1834b4e3ba4dcef0e4131379b0908e00e79c3f2f833f119066966acd2524eb8`
- `src/execution.py`: `f642aa1833e7538e85b591e63f05e2e88fe95ff384929660f6e5f177d2807959`
- `src/smoke_acceptance.py`: `aa63aa75008e507fca3430d6214478091021874236f0bc46c489a82f19e3d8c6`
- `tests/test_protocol_control.py`: `b29e42fbb7794200d8b06d838c597b76d19dcef8600b890887afa3eb22ac8b82`
- reconciled ledger: `6a5901a8cacf780f96e110882f168ed2cdf1c8045785f81931a91f4f5937dd9a`

The four pre-existing immutable record hashes remain:

- `pc-smoke-t01-arm_1-r02`: `f362920a36e91980876109eace638370cd34f3dc49f295611a52018abc4bd7e4`
- `pc-smoke-t02-arm_1-r01`: `1c1bb61534d854a986ea4a9a42e63a9e45403614e20d2ffaa3434a68dbae4c1a`
- `pc-smoke-t02-arm_1-r02`: `104bdcf53275c239fa0a6efb3d1c689f659367364ae9aaa29610b9caa8de603e`
- `pc-smoke-t02-arm_2-r01`: `461e85981f2ef21aa7ac63008f6da607639ae031ab6d62f26df26c4a5ca6882d`

Unchanged scientific artefacts:

- P/C pairs: `dd8b178c03882fcc10d870b033765256950f20200a9efbea63793efb58ce97fd`
- formal manifest: `dd63ef8abb8baeb06581a0b077e8c28afb32579db4f5152f374ff6f311237ee2`
- formal bindings: `6e0fb442e10f1cf921e8a0056b41013bd1a4c0c3ccf5d0e74fa73a59acf6b1b5`
- smoke v2 manifest: `3454d96710f12ac5988c7a30667fce057abe1cb7455cc3fe6b7365432d4b5507`
- smoke v2 bindings: `54c194398a6cff3cc86cb15355f970fef8b0a5702731571a37250dde592eeffc`
- analysis: `7558648da80f0e788215be3e437ff4bb20f93a7588f9d1a7435510909d3b4a5d`

## Outcome-blind validation

- 15 unit tests: PASS.
- New no-provider four-worker local mock v3: PASS.
- Resume, atomic finalization, duplicate-claim, and hard-cap tests: PASS.
- Existing four records revalidated complete: 4/4.
- Existing records with runner technical failure: 0/4.
- Existing record hashes changed: 0/4.
- Ledger completed/active: 4/0.
- Tokens/cost already consumed: 112,133 / USD 0.1794128.
- Provider calls during amendment validation: 0.
- Scientific outcome summaries read or computed: 0.

The user separately authorized continuation after this outcome-blind amendment.
Only the four missing smoke cells may be claimed. Existing output files remain
immutable, total smoke caps remain 8 starts/5M tokens/USD 8, and formal remains
prohibited.
