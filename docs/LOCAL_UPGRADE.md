# Local upgrade — simulated endpoint provisioning and Ollama diagnostics

This adds two features to the original offline demonstration. It does **not** add live Jamf, Intune, Autopilot, Apple Business Manager, EPM, or other external integrations.

## Setup and test

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m workplace_ops
```

In a second Terminal:

```bash
curl -s http://127.0.0.1:8000/api/ai/diagnostics | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/provisioning/devices/MAC-001/readiness | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/provisioning/devices/MAC-002/readiness | python3 -m json.tool
curl -s -X POST http://127.0.0.1:8000/api/provisioning/devices/MAC-001/request | python3 -m json.tool
```

To approve, copy the `request.id` from the last response:

```bash
curl -s -X POST http://127.0.0.1:8000/api/provisioning/requests/PASTE_REQUEST_ID_HERE/approve \
  -H 'Content-Type: application/json' -d '{"reviewer":"Demo Reviewer"}' | python3 -m json.tool
```

Alternatively use the **Laptop provisioning readiness** panel on the dashboard. A compliant device can proceed to a *simulated* approval; an out-of-policy device is blocked with reasons. There are no real endpoint writes.

## Ollama setup

```bash
ollama list
export WORKPLACE_AI_MODE=ollama
export WORKPLACE_OLLAMA_MODEL=llama3.2:1b
python -m workplace_ops
```

`GET /api/ai/diagnostics` now tells you whether Ollama is reachable and whether the configured model name matches an installed local model. A `200` from the deterministic draft endpoint **does not** prove a model ran. Use `model_used` in `/api/tickets/{ticket_id}/ai-summary` to distinguish them.

## Safety

This is a fictional local-only portfolio demo. `reviewer` is a text label, **not authentication**; do not expose this app on the internet or present the approval as a real identity control. Readiness checks use simulated flags, not real enrollment or hardware state. For production, an identity, permissions, device attestation, actual vendor API integration, durable job states, and observable change execution would be required.
