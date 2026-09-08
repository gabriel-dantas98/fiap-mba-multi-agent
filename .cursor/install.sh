#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap. Tools live in the Dockerfile; this refreshes
# repo-bound deps and prints versions for quick health checks.
set -euo pipefail

cd /workspace

if [[ -f pyproject.toml && -f uv.lock ]]; then
  uv sync --frozen
fi

terraform version
az version --output table >/dev/null
az version --query '"azure-cli"' -o tsv

printf 'cloud-agent install=ok (terraform + azure-cli ready)\n'
printf 'secrets needed for plan/apply: ARM_CLIENT_ID ARM_CLIENT_SECRET ARM_TENANT_ID ARM_SUBSCRIPTION_ID\n'
