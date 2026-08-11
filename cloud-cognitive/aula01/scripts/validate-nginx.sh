#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../terraform"
SSH_KEY_PATH="${SSH_KEY_PATH:-${HOME}/.ssh/id_ed25519}"
SSH_USER="${SSH_USER:-azureuser}"
PUBLIC_IP="$(terraform -chdir="${TERRAFORM_DIR}" output -raw public_ip_address)"
SSH_OPTIONS=(
  -i "${SSH_KEY_PATH}"
  -o BatchMode=yes
  -o ConnectTimeout=10
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
)

for attempt in {1..12}; do
  if ssh "${SSH_OPTIONS[@]}" "${SSH_USER}@${PUBLIC_IP}" true; then
    break
  fi

  if [[ "${attempt}" -eq 12 ]]; then
    echo "SSH indisponível após 12 tentativas." >&2
    exit 1
  fi

  sleep 5
done

ssh "${SSH_OPTIONS[@]}" "${SSH_USER}@${PUBLIC_IP}" 'sudo bash -s' <<'REMOTE'
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx

cat > /var/www/html/index.html <<'HTML'
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <title>Cloud Cognitive Aula 1</title>
  </head>
  <body>
    <h1>Cloud Cognitive funcionando</h1>
    <p>Terraform, SSH, NSG e Nginx validados.</p>
  </body>
</html>
HTML

systemctl enable --now nginx
curl --fail --silent http://127.0.0.1/ | grep -F "Cloud Cognitive funcionando"
REMOTE

response="$(
  curl \
    --fail \
    --silent \
    --show-error \
    --retry 10 \
    --retry-delay 3 \
    "http://${PUBLIC_IP}/"
)"

grep -Fq "Cloud Cognitive funcionando" <<<"${response}"

printf 'ssh=ok\nhttp=200\nurl=http://%s/\n' "${PUBLIC_IP}"
