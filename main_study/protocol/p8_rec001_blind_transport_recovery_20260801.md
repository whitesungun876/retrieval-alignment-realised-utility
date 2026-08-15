# P8-REC-001 — Outcome-blind transport-failure recovery

## Trigger

During blind P8 collection, 146 immutable episode records were classified as
technical failures. Two were provider read timeouts and 144 were transport
connection failures concentrated between 2026-08-01 09:14 and 09:16 UTC. No
terminal outcome, score, trajectory, or condition comparison was inspected in
making this classification.

The frozen maximum unresolved episode-failure rate is 1%. Even if every
remaining planned cell completed, 146/5,400 would exceed that threshold.

## Authorization

Immediately after being shown the exact recovery proposal and caps, the user
instructed the system to continue. This instruction authorizes P8-REC-001 with:

- at most 146 mechanically eligible technical replacements;
- at most 5,547 paid episode starts in aggregate, comprising 5,400 planned
  cells, 146 technical replacements, and one previously recorded paid-start
  adjustment;
- the unchanged aggregate cap of 195,000,000 tokens;
- the unchanged aggregate monetary cap of USD 311.88.

## Frozen eligibility rule

A pre-amendment record is eligible if and only if all of the following are
true:

1. the record is structurally complete;
2. its frozen technical classifier marks it as a runner error;
3. the recorded exception states that the LLM request failed after the frozen
   internal attempts because of an HTTPS connection retry exhaustion or read
   timeout.

Recorded usage before the transport interruption may be zero or nonzero and is
fully retained in aggregate budget accounting. It is not an eligibility
criterion because a provider failure can occur after an earlier valid step but
before the episode produces a terminal scientific observation.

Eligibility is computed without reading terminal success, score, actions,
observations, or the sealed condition identity. The eligible set is frozen and
hashed before any replacement call.

## Replacement rules

- Every eligible original remains immutable and auditable.
- Each eligible cell receives at most one replacement record with a distinct
  run identifier.
- Target, masked arm, repetition, environment seed, sealed condition/source
  binding, model, prompt, renderer, and maximum steps remain unchanged.
- A replacement is selected for analysis solely when it is technically valid;
  scientific outcomes cannot affect selection.
- Cells without a frozen eligible technical failure are never replaced.
- Any new technical failure in the amendment epoch triggers an automatic safe
  stop after already-active claims finish.
- All original and replacement calls count against the unchanged token and
  monetary caps.

## Analysis and acceptance

For each eligible cell, P9 uses the technically valid replacement when one
exists; otherwise the cell remains missing. All other cells use their original
record. P9 still requires final unresolved missingness within the frozen 1%
tolerance. P8-REC-001 does not change the research questions, experimental
conditions, target sample, outcome, or statistical analysis.
