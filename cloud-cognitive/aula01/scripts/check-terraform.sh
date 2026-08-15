#!/usr/bin/env bash
# Analogia de `tsc --noEmit` para o lab Terraform: fmt + validate, sem apply.

set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT}/terraform"

export TF_VAR_subscription_id="${TF_VAR_subscription_id:-00000000-0000-0000-0000-000000000000}"
export TF_VAR_meu_ip="${TF_VAR_meu_ip:-203.0.113.10}"
export TF_VAR_ssh_public_key="${TF_VAR_ssh_public_key:-ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA validate}"

cd "${TF_DIR}"

terraform fmt -check -recursive
terraform init -backend=false -input=false >/dev/null
terraform validate

printf 'terraform check=ok\n'
