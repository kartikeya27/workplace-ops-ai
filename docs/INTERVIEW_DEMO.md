# Hiring-manager walkthrough (3–5 minutes)

## Before the call

- Start the app: `python -m workplace_ops`.
- Verify `/api/health` and `python -m pytest -q`.
- Reset fictional data before recording screenshots: stop server → `bash scripts/reset_local.sh --yes` → restart.
- Open browser dashboard and `/docs` in separate tabs.
- Use **deterministic mode** during a live interview; local LLM inference depends on model download and machine performance.

## Script

**0:00–0:30 — Problem and discovery**

“Workplace engineers frequently spend time collecting device state, triaging escalation tickets, assembling audit evidence and communicating patch status. I built this fictional local prototype to show how I'd approach those workflows: observe the manual process, normalize the data, automate the deterministic parts and require review before any consequential change.”

**0:30–1:45 — Ticket triage (lead with this)**

- Choose `T-1001`, a Mac encryption escalation.
- Click **Analyze selected ticket**.
- Explain that the API gathered the local Jamf-shaped device record, checked `encrypted=false` and `compliant=false`, matched the endpoint team, retrieved curated KB advice, and found an on-duty engineer.
- Emphasize that it's a proposal and won't assign automatically.
- Approve the *fictional local assignment*, show the audit event, then repeat the operation to discuss idempotence.
- Mention that fallback is manual when no on-duty engineer exists.

**1:45–2:30 — Audit evidence**

- Click **Generate evidence package** and **Verify latest package**.
- Explain normalizing Mac and Windows, illustrative control mapping, collection timestamps, source metadata and SHA-256 verification.
- Be explicit: hash alone is not immutable evidence or certification.

**2:30–3:15 — Migration example**

- Click **Build safe migration plan**.
- Point out the high-risk recurring/external meetings and required owner review.
- Explain that simply flipping a Microsoft Graph Teams event to Zoom is not supported; real migration needs inventory, communication, creation/reinvite, reconciliation, safeguards and pilot cohorts.

**3:15–4:00 — Engineering quality**

- Show `/docs` and `.github/workflows/ci.yml`.
- Show the tests, the optional local LLM draft (do not claim it is actually using a model unless `WORKPLACE_AI_MODE=ollama` is enabled), and the no-live-write boundary.
- Ask how their team currently tracks on-duty rotations and escalation ownership, rather than claiming your toy rules match their real process.

## Questions to invite discussion

1. Which escalation types have the highest manual handling time, and how do you measure that baseline?
2. Is there an authoritative on-call rota, and should routing suggest an owner before assigning them?
3. What proportion of compliance evidence comes directly from MDM reports versus manually assembled screenshots?
4. Is the first priority reducing daily ticket toil or meeting a specific audit evidence deadline?
5. What approval and pilot policies would apply to any automation that can change device state?

## Avoid these claims

- “This integrates with real Jamf, Intune, Okta, Microsoft Graph or Zoom.” It does not.
- “This is a production-ready AI agent.” It is a demonstration with optional local model narration.
- “The controls prove government compliance.” They do not.
- “This automatically converts Teams meetings to Zoom.” It only produces a safe fictional plan.
- “The dashboard shows time saved.” Time savings need measured real-process baselines.
