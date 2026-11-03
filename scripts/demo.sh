#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"
echo '1/5: Service health'
curl -fsS "$BASE/api/health"; echo
echo '2/5: Sample tickets'
curl -fsS "$BASE/api/tickets"; echo
echo '3/5: Triage first ticket (requires human approval)'
curl -fsS -X POST "$BASE/api/tickets/T-1001/triage"; echo
echo '4/5: Patch notification dry-run'
curl -fsS "$BASE/api/patches/plan"; echo
echo '5/5: Meeting migration dry-run'
curl -fsS "$BASE/api/meetings/plan"; echo
