# Local-only employee laptop onboarding — end-to-end demo

This is a **fictional simulation** designed for demonstrating safe enterprise automation. It never enrolls a device, creates an identity account, installs software, grants administrator access, sends a notification, or contacts Jamf, Intune, Okta, Entra ID, or privilege management platforms. Reviewer names are demo labels, not verified authentication.

## Workflow

1. **Device readiness** — verify the mock device is in inventory, encrypted, compliant, and patched.
2. **Identity provisioning** — simulate an enterprise IdP account and role-based groups with MFA required; the UPN uses the reserved \`example.invalid\` suffix.
3. **Application plan** — choose a fictional Mac or Windows application manifest for the selected role.
4. **Application deployment** — mark local application rows as simulated installations; no software is installed.
5. **Privilege review** — engineering and support profiles require human approval/denial of a fictional 30-minute scoped privilege request. Standard users need no elevation.
6. **Audit and status** — persist every transition to local SQLite; provide a timeline with outcome and simulated expiry.

Each Run Next Step button makes **exactly one** state change. Security readiness is rechecked before each downstream step. Invalid transitions and conflicting retries return HTTP 409.

## Run locally

Prerequisites: Python 3.11+, Git. Docker and Ollama are optional.

\`\`\`bash
cd ~/workplace-ops-ai
git fetch origin
git switch feature/end-to-end-laptop-onboarding
git pull --ff-only
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
WORKPLACE_AI_MODE=deterministic python -m pytest -q
python -m workplace_ops
\`\`\`

Visit **http://127.0.0.1:8000** and find **Workflow 06 · Employee laptop onboarding**. Create \`EMP-1001\` / \`MAC-001\` / \`engineering\`, click **Run next simulated step** five times, then approve or deny the 30-minute fictional privilege request. Check audit history.

To demonstrate blocked security, choose \`EMP-1002\`, \`MAC-002\`, \`engineering\`; it will be blocked before account provisioning. For non-elevated Windows flow, choose \`EMP-1003\`, \`WIN-001\`, \`standard\`.

To replay the same identifiers, stop the app then run \`bash scripts/reset_local.sh --yes\` and restart.

## API walkthrough

\`\`\`bash
curl -s -X POST http://127.0.0.1:8000/api/onboarding \
  -H 'Content-Type: application/json' \
  -d '{"employee_id":"EMP-1001","device_id":"MAC-001","profile":"engineering"}'
\`\`\`

Copy \`run.id\` from the JSON:

\`\`\`bash
RUN_ID='paste-real-run-id-here'
curl -s -X POST "http://127.0.0.1:8000/api/onboarding/$RUN_ID/advance"
\`\`\`

Repeat that \`advance\` request until the status is \`awaiting_privilege_approval\`, then:

\`\`\`bash
curl -s -X POST "http://127.0.0.1:8000/api/onboarding/$RUN_ID/privilege-decision" \
  -H 'Content-Type: application/json' \
  -d '{"reviewer":"Demo Reviewer","decision":"approve"}'
curl -s "http://127.0.0.1:8000/api/onboarding/$RUN_ID" | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/onboarding | python3 -m json.tool
\`\`\`

## Explicit limits

- This demo uses local SQLite fixture records; no real users, devices, or external writes.
- The reviewer is **not authenticated**. Local timestamp expiry is display-only; it does not grant or revoke access on a device.
- SQL-level unique constraints prevent duplicate employee/device assignments. Production needs additional tenant-aware identity, authorization, queueing, retry, audit and lifecycle controls.
- The model integration, when enabled, is for drafting ticket summaries only. **LLMs never issue approval or provisioning commands.**

To productionize: add least-privilege API adapters with rate limits and error handling, policy-based approval, service identity, explicit authorization, durable idempotency keys, audit retention, observability, revocation, and failure recovery.
