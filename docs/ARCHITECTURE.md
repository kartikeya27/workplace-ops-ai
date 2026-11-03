# Architecture and engineering decisions

## Business goal

Reduce operational toil by improving *handoffs* before attempting production remediation. Typical processes: helpdesk escalation, endpoint patch communication, evidence collection, and collaboration-platform migration planning. Success means a domain expert receives a good starting point faster, while retaining control of impactful changes.

## Request flow: ticket triage

1. Retrieve fictional ticket by ID from SQLite.
2. Run deterministic policy/keyword rules (`triage.classify`) to choose a specialty team.
3. Look up device context from fictional Jamf/Intune-shaped records.
4. Attach an approved curated knowledge article as evidence.
5. Read on-duty staffing table and suggest an owner. If no engineer is on duty, fall back to manual queue.
6. Store one proposal per ticket (unique constraint prevents duplicate proposals on retries).
7. Await a reviewer. The demo approve endpoint only mutates a **fictional local ticket**; repeated approvals are idempotent.
8. Append audit events with actor, action, time, subject and context.

> The reviewer field is only a demo label. It does not authenticate the caller. Production use requires SSO, authorization and a real ticketing adapter.

## AI boundary

An optional on-device Ollama model can draft concise *advice*, using a small, bounded collection of known facts and a curated article. This text never controls ticket classification, access scopes, approvals or tool execution. Even with `WORKPLACE_AI_MODE=ollama`, the model can only generate a string. The tool trace makes the distinction visible.

AI is useful for ambiguous language and drafting. It is *not* needed for: known patch status, audit evidence collection, routing based on an established rota, or enforcing security controls.

A stronger production AI system would add: policy-aware source retrieval, citation validation, structured outputs, adversarial evaluation of prompt injection, a human feedback set, offline fallback, and a refusal path for ungrounded outputs. This repository does **not** claim those are implemented.

## Storage

SQLite is sufficient for a solo, local walkthrough and simple transactions. The database defaults to `artifacts/workplace_ops.db` (ignored by Git). Production would need a managed database, service credentials, separate environments, backup policies, retries, observability, and secure job orchestration.

## Control examples

The evidence collector maps three **illustrative** controls to device facts: `ENCRYPTION`, `MDM_COMPLIANCE`, `PATCH_CURRENCY`. These are not an implementation of a formal compliance framework and should not be described as NIST or FedRAMP compliance.

Each run emits `snapshot.json`, `manifest.json`, and SHA-256 for the JSON bytes. Changing the snapshot after generation makes verification fail. In production, an attacker who can modify both storage and database could rewrite the hashes; real integrity needs independent signatures and tamper-resistant retention.

## Calendar platform limitation

An existing Microsoft Graph event already configured as an online meeting cannot have its `onlineMeetingProvider` simply switched. This demo therefore deliberately creates a **plan** for the owner to recreate/reinvite and verify affected meetings, not a fake automatic migration.

Reference: https://learn.microsoft.com/en-us/graph/outlook-calendar-online-meetings

## Data flow and risks

| Boundary | Current demo | Production target |
|---|---|---|
| Device reads | Seeded SQLite fixtures | Least-privilege Intune/Jamf API client with retries/pagination |
| Ticket actions | Local simulated record write | Authenticated ticketing API + approval and change control |
| AI | Rule template / optional localhost Ollama | Approved tenant model and data classification protections |
| Calendar plan | Synthetic JSON | Scoped Graph read, Zoom creation, organizer approvals, careful exceptions |
| Audit | Local SQLite event table | Central append-only logs, security correlation, retention |
| Evidence | Local JSON and SHA-256 | WORM/immutable storage, trusted signatures and audit control mapping |

## Next engineering increments

1. Add a contract-tested connector interface and fake HTTP server for MDM and ticketing services.
2. Add pagination, backoff, retry budgets, rate-limit handling, correlation IDs and bounded concurrency.
3. Add real user authentication, RBAC and approval workflows.
4. Instrument service-level objectives, alerts, metrics and failure drills.
5. Add evaluation fixtures for misrouting and unsafe model advice.
