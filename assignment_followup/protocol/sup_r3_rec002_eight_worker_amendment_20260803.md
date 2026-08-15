# SUP-R3 REC-002: eight-worker execution amendment

Date: 2026-08-03  
Approval status: approved during blind formal collection

## Scope

The user approved increasing the supplemental scheduler from four to eight concurrent workers while retaining the original total limits of 4,812 Agent episode starts, 175,000,000 tokens, and USD 280.

The four-worker REC-001 runner was paused outcome-blind by setting a stop sentinel. Existing active episodes were allowed to finish normally; no request was interrupted and no record was rerun. The pause completed with 21 immutable formal records and zero active claims.

REC-002 changes only the number of scheduler worker processes from four to eight. It does not change:

- the 4,800-cell formal manifest or its order;
- target or source assignments;
- N2, P, or R2 conditions;
- the model snapshot, prompt, renderer, environment, maximum steps, decoding, scorer, or analysis;
- episode, token, or monetary caps;
- the rule that each scientific cell receives at most one immutable record.

Before activation, eight workers must pass a zero-cost local stress test covering simultaneous initial claims, unique ownership, atomic finalisation, clean heartbeats, cap enforcement inherited from REC-001, and complete reconciliation. All eight workers must complete at least one mock record. New hashes are frozen before the stop sentinel is cleared.

The reason for the change is elapsed-time reduction only. No condition outcomes, terminal success, scores, or trajectories were inspected when deciding or implementing the amendment.
