# Security model, safety boundaries, and limitations

## Existing protections

- Fully fictional test data (`@example.test` mailboxes); no cloud permissions or production secrets needed.
- Application is started on `127.0.0.1:8000` by the native Python command. Docker publishes only to host loopback.
- There is **no** remote MDM, identity, mail, or calendar write integration.
- The optional LLM endpoint is hard-coded to `127.0.0.1:11434` and generates a string only.
- AI model output cannot approve a proposal or trigger a device/calendar action.
- Routing is deterministic, traceable, and uses an explicit on-duty table with a manual fallback.
- Proposals are unique per ticket; repeated approvals are idempotent.
- Evidence snapshot SHA-256 verification detects file modification relative to its recorded digest.
- Input validation for the demonstration approver name; dashboard HTML escapes displayed text.
- Tests cover important routing, approval, evidence and dry-run properties.

## NOT provided — do not deploy publicly

- Authentication, SSO, actual approvals bound to identities, RBAC or authorization controls.
- Proper data classification and strong PII redaction; the regex scrubber is **only best-effort**.
- HTTPS, CSRF defenses, a hardened reverse proxy, network segmentation, abuse limits or a secrets manager.
- Durable job queue, distributed locking, real idempotency across a third-party service, production alerts, metrics, SLOs or high availability.
- Production-grade compliance reporting, immutable object storage, cryptographic signatures, third-party evidence attestation, approved frameworks or legal audit sufficiency.
- LLM robustness evaluations, trust-policy enforcement for arbitrary real tickets, prompt-injection hardening or guaranteed factual summaries.
- Real Microsoft Graph, Jamf, Intune, Okta, Zoom, Duo or service desk adapters.
- Real email, endpoint policy, calendar, meeting or identity modifications.

## Production threat review checklist

| Threat | Example mitigation needed before production |
|---|---|
| Broad MDM permissions | Dedicated read-only principal for observation, separate narrowly scoped write executor |
| Privileged service accounts | Managed identity/OAuth, secret vault, rotation, least privilege |
| Model prompt injection | Structured tool outputs, content isolation, allowlisted tools, no direct writes, evals |
| Data exfiltration | Classification policy, consent, data minimization, sensitive-field scrubbing, logging policy |
| Double execution | Versioned approvals, idempotency keys, external transaction verification |
| Incorrect meeting updates | Inventory, organizer approval, pilot group, attendee reconciliation, rollback procedure |
| Incomplete audit | Scheduled collection, gap alerts, immutable retention and independent verification |
| Unauthorized local approval | Enterprise authentication, actor binding, RBAC, change-management approvals |

## Prompting model assist safely

The model receives only bounded fictional ticket fields, rule-based classification, curated KB guidance, and selected device facts. The generated draft is advisory and marked for human review. Even in this constrained local demo, model output can be inaccurate. Never put live user tickets or secrets into this example without an approved enterprise security design.
