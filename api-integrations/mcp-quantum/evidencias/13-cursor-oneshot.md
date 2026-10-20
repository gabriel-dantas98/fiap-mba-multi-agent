# Cursor (cursor-agent one-shot) -> MCP Quantum em produção

## .cursor/mcp.json
{"mcpServers":{"quantum":{"type":"http","url":"https://mcp-quantum.gabsdevops.workers.dev/mcp","headers":{"Authorization":"Bearer ***"}}}}

## Preparação
$ cursor-agent mcp enable quantum
✓ Enabled and approved MCP server: quantum
$ cursor-agent mcp list
quantum: ready
$ cursor-agent mcp list-tools quantum
Tools for quantum (4):
- buscar_produto_por_nome (nome)
- listar_produtos_por_categoria (categoria)
- obter_avaliacao_produto (produto)
- obter_produto (produto_id)

## Comando
cursor-agent -p --trust --approve-mcps --output-format stream-json 'Usando somente as tools do servidor MCP "quantum": qual produto da categoria maquiagem tem a melhor nota média de avaliação? ...'

## Chamadas MCP feitas pelo agente
mcpToolCall  quantum-listar_produtos_por_categoria  {"categoria": "maquiagem"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P021"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P022"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P023"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P024"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P025"}
mcpToolCall  quantum-obter_avaliacao_produto  {"produto": "P026"}

## Resposta final
Vou consultar o MCP Quantum: listar maquiagem e, em seguida, as avaliações de cada produto.**P021 — Paleta de sombras 18 cores Sunset**  
Preço: R$ 80,83 | Nota média: **3,74** (melhor entre os 6 de maquiagem).