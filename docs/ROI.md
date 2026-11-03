# Measuring value without inventing results

A portfolio demo should not claim actual hours saved. Use a small **illustrative scenario** and distinguish assumptions from measured outcomes.

## Baseline method

For two weeks, record these per ticket: initial handling time, time waiting for assignment, evidence-gathering time, reassignment count, false/missing device context, and manual escalation steps. Also log the engineering time to maintain the automation itself.

## Example hypothesis, NOT a measured result

Assume the team handles **40 escalated tickets per week**. If collecting first-pass device context takes a median **12 minutes** manually and a reviewed automation reduces it to **4 minutes**, the theoretical gross improvement is:

`40 tickets × (12 - 4) minutes = 320 minutes/week = 5 hours 20 minutes/week`

This is a *hypothetical* upper-level estimate, not an outcome of the fictional app. Net savings must subtract verification, triage errors, maintenance, outages and changes in ticket mix.

## Useful operational indicators

- Median time from helpdesk escalation to first engineer action.
- Percent of tickets with complete context on first assignment.
- Reassignment rate and incorrect-route rate.
- Percent of approved automation proposals.
- Audit evidence coverage and missing-collection alerts.
- Patch communication coverage with no duplicate messages.
- Change failure rate and rollback/reversal incidents.
- Engineers' subjective trust, plus objective adoption rates.

## Experiment

A/B test a pilot set of low-risk ticket categories using the same on-duty rules. Keep human approvals. Compare the intervention and control using matched ticket priority and device type. Have MDM specialists review incorrect recommendations; make those failures new tests. Only expand scope if quality and measured time savings justify maintenance costs.
