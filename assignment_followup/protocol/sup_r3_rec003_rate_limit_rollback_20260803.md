# SUP-R3 REC-003: rate-limit safety rollback to four workers

Date: 2026-08-03

REC-002 increased scheduler concurrency from four to eight workers after explicit approval. The first eight-worker batch triggered three immutable technical failures caused by HTTP 429 responses after the frozen three-attempt retry sequence. The scheduler stop sentinel was set as soon as the aggregate technical signal was observed. Existing active episodes were allowed to finish; no request was interrupted and no record was rerun.

The eight-worker epoch ended at 32 completed formal records and zero active claims. Three records were technical failures and remain missing scientific observations. They will not be replaced or rerun. Their maximum contribution to planned 4,800-record missingness is 0.0625 percentage points, below the one-percent SUP-R5 validity allowance if subsequent execution remains stable.

REC-003 restores the previously validated four-worker scheduler. This is a safety rollback within the originally frozen execution design and within the user's unchanged total caps. It changes no target, source, condition, prompt, model, environment, analysis, run order, or immutable record. The REC-002 evidence is preserved; it is not deleted or reclassified.

The rollback is based solely on provider/runner technical fields. No condition outcomes, success rates, scores, or trajectories were inspected.
