# SUP-R6 pre-analysis deviation 01: premature display of the sealed arm map

Recorded: 2026-08-05T16:14:43+02:00 (Europe/Copenhagen)

After SUP-R5 had recorded PASS, but before the final SUP-R6 bundle manifest was
frozen, a schema-inspection command printed the complete `arm_to_condition`
object from the already sealed supplemental condition-map file. This revealed
only the assignment of the three masked arm names to `N2`, `P`, and `R2`.

No formal record was opened by that command. No terminal-success value, score,
trajectory, condition-level descriptive, contrast, p-value, confidence interval,
effect direction, or failure category was inspected or computed. The prospective
analysis module `experiments/study3_sup_analysis.py`, its resampling seeds, the
primary and secondary contrasts, the Holm family, the TOST margin, the failure
taxonomy, and the overlap rules had all been frozen at SUP-R0 and remain byte
unchanged.

The requested order was therefore violated at the label-revelation step even
though no scientific outcome was exposed. The deviation is preserved in the
final SUP-R6 hash bundle. The SUP-R6 wrapper added after discovery is restricted
to mechanical data binding, frozen-hash verification, deterministic descriptive
diagnostics, and a single invocation of the already frozen analysis entry point.
No hypothesis, estimand, exclusion, missing-data rule, inferential method,
resampling seed, multiplicity rule, or interpretation threshold is changed.

