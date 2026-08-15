# SUP-R2 pre-outcome amendment 01

Date: 2026-08-03  
Status: approved before any supplemental Agent episode or outcome existed

## Trigger

The first frozen SUP-R2 Monte Carlo run used 10,000 simulations per scenario. The prespecified conservative scenario (800 targets, true risk difference 0.05, target-level difference SD 0.50, and 1% episode missingness) produced estimated two-sided sign-flip-test power of 0.7972, below the literal 0.8000 gate by 0.0028. Its Monte Carlo 95% interval was [0.78921, 0.80497]. The original `sup_r2_power_report.json` is retained unchanged with decision `FAIL`.

An independent, outcome-free 100,000-simulation precision audit using seed 202608039001 estimated power as 0.79715 with Monte Carlo 95% interval [0.79465, 0.79963]. A corresponding zero-effect audit using seed 202608039002 estimated Type-I error as 0.04628 with interval [0.04500, 0.04760]. This established that the shortfall was small but not solely a 10,000-simulation fluctuation.

## Approved amendment

The user approved proceeding with the observed prospective power of 0.7972. The design is not re-powered, resized, or re-simulated to obtain a passing result. The study retains:

- 800 targets;
- N2, P, and R2 conditions;
- two repetitions per target-condition;
- 4,800 formal Agent episodes plus at most 12 excluded smoke-test episodes;
- the Qwen model snapshot, prompts, environment, estimands, 5-percentage-point SESOI, tests, and analysis code frozen at SUP-R0;
- total caps of 4,812 Agent episode starts, 175,000,000 tokens, and USD 280, including model-probe token and monetary usage.

The original 0.80 gate is reported as missed by 0.28 percentage points. The accepted design power is 79.72%, not rounded upward to 80%. The conservative zero-effect TOST power of approximately 76.4% is also disclosed as a limitation. The amendment changes only the decision to proceed; it does not change a scientific outcome, analysis rule, or exclusion rule.

## Audit state at approval

- Supplemental Agent episode starts: 0
- Supplemental Agent outcomes present: no
- Model-probe usage: 465 tokens and USD 0.000744
- Approval text: `批准 SUP-R2 pre-outcome amendment，接受实际功效79.72%，继续SUP-R3。`

The first FAIL report, the precision audit, this amendment, and the approval record must all remain in the reproducibility archive.
