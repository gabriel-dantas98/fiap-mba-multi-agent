# Codex (codex exec one-shot) -> MCP Quantum em produção

## Instalação (o comando que a homepage gera)
```bash
export QUANTUM_MCP_TOKEN="***"
codex mcp add quantum --url https://mcp-quantum.gabsdevops.workers.dev/mcp --bearer-token-env-var QUANTUM_MCP_TOKEN
```

## config.toml resultante
```toml
[mcp_servers.quantum]
url = "https://mcp-quantum.gabsdevops.workers.dev/mcp"
bearer_token_env_var = "QUANTUM_MCP_TOKEN"
```

## codex mcp list
```
Name     Url                                             Bearer Token Env Var  Status   Auth
quantum  https://mcp-quantum.gabsdevops.workers.dev/mcp  QUANTUM_MCP_TOKEN     enabled  Bearer token
```

## Comando
```bash
codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox --json \
  'Usando somente as tools do servidor MCP "quantum": qual o livro mais barato do catálogo e qual a nota de avaliação dele? ...'
```

Sem `--dangerously-bypass-approvals-and-sandbox`, o `codex exec` (não interativo) bloqueia a chamada MCP por exigir aprovação; no Codex interativo ele pergunta antes de chamar.

## Chamadas MCP feitas pelo agente
mcp_tool_call  quantum.listar_produtos_por_categoria  {"categoria": "livro"}  -> completed
mcp_tool_call  quantum.obter_avaliacao_produto  {"produto": "P019"}  -> completed

## Resposta final
O livro mais barato é **Livro infantil O Sapo Azul**, por **R$ 38,63**.
Sua nota média é **3,46 de 5**, com 8 avaliações.
