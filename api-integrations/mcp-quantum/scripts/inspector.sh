#!/usr/bin/env bash
# Sobe o MCP Inspector já apontado para o servidor, sem configurar nada na UI.
#
#   scripts/inspector.sh cloudflare        # produção (token em .token)
#   scripts/inspector.sh local             # Worker local do `pywrangler dev` (token em .dev.vars)
#   scripts/inspector.sh stdio             # servidor Python direto, sem auth
#
#   scripts/inspector.sh <alvo> check      # sem UI: lista tools/resources/prompts e chama uma tool
set -euo pipefail

cd "$(dirname "$0")/.."

INSPECTOR="@modelcontextprotocol/inspector@2.11.0"
URL_CLOUDFLARE="https://mcp-quantum.gabsdevops.workers.dev/mcp"
URL_LOCAL="http://localhost:8787/mcp"

alvo="${1:-}"
modo="${2:-ui}"

token_de() {
  local valor="$1" origem="$2"
  if [[ -z "$valor" ]]; then
    echo "Token não encontrado em $origem. Veja a seção 'Deploy' do README." >&2
    exit 1
  fi
  printf '%s' "$valor"
}

case "$alvo" in
  cloudflare)
    token=$(token_de "$(cat .token 2>/dev/null || true)" ".token")
    destino=(--transport http --server-url "$URL_CLOUDFLARE" --header "Authorization: Bearer $token")
    ;;
  local)
    token=$(token_de "$(sed -n 's/^MCP_TOKEN=//p' .dev.vars 2>/dev/null || true)" ".dev.vars")
    if ! curl -s -o /dev/null --max-time 2 "$URL_LOCAL"; then
      echo "Nada respondendo em $URL_LOCAL. Rode antes, em outro terminal: uv run pywrangler dev" >&2
      exit 1
    fi
    destino=(--transport http --server-url "$URL_LOCAL" --header "Authorization: Bearer $token")
    ;;
  stdio)
    destino=(--transport stdio --cwd "$PWD" uv run python src/local.py)
    ;;
  *)
    sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac

case "$modo" in
  ui)
    exec npx -y "$INSPECTOR" --web "${destino[@]}"
    ;;
  check)
    cli() { npx -y "$INSPECTOR" --cli "${destino[@]}" "$@"; }
    nomes() { python3 -c "import json,sys; [print('  ' + i['$2']) for i in json.load(sys.stdin)['$1']]"; }
    echo "== tools/list";     cli --method tools/list 2>/dev/null | nomes tools name
    echo "== resources/list"; cli --method resources/list 2>/dev/null | nomes resources uri
    echo "== resources/templates/list"
    cli --method resources/templates/list 2>/dev/null | nomes resourceTemplates uriTemplate
    echo "== prompts/list";   cli --method prompts/list 2>/dev/null | nomes prompts name
    echo "== tools/call obter_avaliacao_produto produto=headset"
    cli --method tools/call --tool-name obter_avaliacao_produto --tool-arg produto=headset 2>/dev/null
    ;;
  *)
    echo "Modo inválido: $modo (use ui ou check)" >&2
    exit 1
    ;;
esac
