# Real connector extension plan (not implemented)

**Nothing in this file means the demo has access to any live service.** Each integration requires approval, a non-production tenant, terms review, security review, and vendor-specific validation.

## Intune / Microsoft Graph

Start with scoped read-only inventory. Microsoft documents `GET /deviceManagement/managedDevices` under Graph v1.0 and the least-privileged read permission `DeviceManagementManagedDevices.Read.All`. An active Intune license and authorized tenant are required.

Official source: https://learn.microsoft.com/en-us/graph/api/intune-devices-manageddevice-list?view=graph-rest-1.0

Implementation approach: separate adapter interface; OAuth credential provider; configuration not in source; pagination (`@odata.nextLink`); 429 backoff and retry cap; rate budget; response normalization; field minimization and redaction; contract tests with saved fictional HTTP responses.

## Jamf Pro

Use Jamf's supported API reference and validate the exact endpoints against the deployed Jamf Pro version. Avoid assuming preview endpoints are stable. Authenticate with a dedicated minimally privileged API client and test on a non-production inventory scope.

Official source: https://developer.jamf.com/jamf-pro/reference/jamf-pro-api

Implementation approach: versioned response adapter; only necessary computer inventory and compliance fields; authorization design with the MDM team; paginated requests where supported; tenant isolation; tests for missing/expired device records.

## Identity platform

Integrate identity state only after the endpoint team approves the data flow. Use a service app with appropriately limited OAuth scopes and role assignments; do not create broadly privileged API tokens for convenience.

Official source for an Okta OAuth service app: https://developer.okta.com/docs/guides/implement-oauth-for-okta-serviceapp/-/main/

## Calendar collaboration migration

Microsoft Graph says `onlineMeetingProvider` can't be changed once an online meeting is enabled. A real Teams→Zoom migration must be designed as a multi-system process with an approved mapping, organizer/attendee notifications, Zoom meeting creation, safe invitation updates or cancellations/recreations, handling of recurring exceptions, idempotency, and rollback/incident procedures.

Official limitation: https://learn.microsoft.com/en-us/graph/outlook-calendar-online-meetings

## Generic support desk

Implement a `TicketAdapter` for the actual vendor and its API (vendor not assumed). Separate `read_ticket`, `append_context`, `propose_assignment`, and `commit_assignment`. Add `idempotency_key`, expected ticket version, on-duty source-of-truth, auditable approver, and a failure path to the shared queue. Do not couple a language model to ticket-writing permissions.
