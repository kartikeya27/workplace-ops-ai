#!/usr/bin/env bash
set -euo pipefail
if [ "${1:-}" != '--yes' ]; then
  echo 'This deletes your local fictional database and evidence packages. To proceed: bash scripts/reset_local.sh --yes'
  exit 1
fi
rm -rf artifacts
mkdir -p artifacts
echo 'Reset complete. Restart the server to reseed demo data.'
