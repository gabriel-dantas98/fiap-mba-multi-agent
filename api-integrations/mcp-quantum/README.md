# MCP Quantum — catálogo de produtos

Servidor MCP do desafio Quantum (Integration Architecture & Connectors). Feito com
FastMCP (SDK oficial `mcp` 1.x), roda como **Cloudflare Python Worker** no plano free,
com transporte **Streamable HTTP** e Bearer token. O mesmo código roda localmente via
stdio.

Produção: `https://mcp-quantum.gabsdevops.workers.dev/mcp`

## Como uma chamada percorre o sistema

![Fluxo de uma chamada MCP](diagramas/fluxo-chamada.png)

Fonte editável: `diagramas/fluxo-chamada.html` (exportado com Chrome headless, 2x).

## O que o servidor expõe

| Tipo | Nome | Item do desafio |
|---|---|---|
| tool | `listar_produtos_por_categoria(categoria)` | 1. listar produtos por categoria |
| tool | `obter_produto(produto_id)` | 2. dados do produto pelo ID |
| tool | `buscar_produto_por_nome(nome)` | 3. busca pelo nome |
| tool | `obter_avaliacao_produto(produto)` | 4. nota de avaliação (aceita ID ou nome) |
| resource | `catalogo://produtos` | catálogo completo (JSON) |
| resource template | `produto://{produto_id}` | detalhe do produto |
| prompt | `recomendar_produto(necessidade, orcamento?, categoria?)` | recomendação |
| prompt | `analisar_produto(produto_id)` | análise de custo-benefício |

Buscas ignoram acento e maiúsculas (`GAME` acha `game`, `pelucia` acha `Pelúcia`). Entradas
inválidas voltam como erro de tool (`isError: true`) com a lista de opções válidas.

## Dados

A fonte é `dados/quantum-commerce-chamados.xlsx`: **200 reclamações** de clientes de um
marketplace, com os dados do produto repetidos em cada linha. O `scripts/gerar_dados.py`
corrige a acentuação (a planilha veio com UTF-8 lido como Latin-1, `PreÃ§o`), salva uma
cópia limpa em `dados/quantum-commerce-chamados.csv` e agrega por `id_produto`:

| Campo | Na planilha | No catálogo |
|---|---|---|
| nome, descrição, categoria | fixos por produto | iguais |
| preço | varia por vendedor | `preco` = média, `preco_min`/`preco_max` = faixa |
| vendedor | vários por produto | lista `vendedores` |
| `avaliacao_produto` | uma nota por chamado | `nota` (média), `nota_min`/`nota_max`, `num_avaliacoes` |
| `classe` | tipo da reclamação | `reclamacoes_por_classe` |

Resultado: **33 produtos** em 5 categorias (`brinquedo`, `game`, `livro`, `maquiagem`,
`outros`). O `tests/test_dados.py` confere os agregados contra a planilha.

## Estrutura

```
dados/                    planilha original + CSV com acentos corrigidos
scripts/gerar_dados.py    XLSX/CSV -> src/dados.py (o Worker não lê arquivo do disco)
src/catalogo.py           consultas, Python puro
src/servidor.py           tools, resources e prompts (FastMCP)
src/main.py               entrypoint do Worker + checagem do Bearer token
src/local.py              mesmo servidor via stdio/HTTP local
tests/                    unitários, consistência com a planilha e E2E em produção
diagramas/                fluxo da chamada (HTML + PNG)
evidencias/               saídas de teste, prints do Inspector, Claude Code e Cursor
```

## Rodar

Pré-requisitos: `uv` >= 0.12.3 (exigido pelo `pywrangler`) e Node (para `npx`).

```bash
uv sync
uv run pytest -q                                  # 19 testes (E2E é pulado sem MCP_URL)

# Regerar o catálogo a partir da planilha
uv run python scripts/gerar_dados.py dados/quantum-commerce-chamados.xlsx

# Local via stdio, sem auth
npx @modelcontextprotocol/inspector uv run python src/local.py

# Worker local (porta 8787), com auth
echo "MCP_TOKEN=$(openssl rand -hex 24)" > .dev.vars
uv run pywrangler dev
```

## Deploy na Cloudflare

```bash
npx wrangler login
uv run pywrangler deploy
openssl rand -hex 24 | tee .token | npx wrangler secret put MCP_TOKEN
```

No Inspector (v2): Add Servers → streamable-http com a URL de produção; em Settings →
Custom Headers, `Authorization: Bearer <conteúdo de .token>`.

## Testes e evidências

```bash
uv run pytest -q                                                    # unitários + dados
MCP_URL=https://mcp-quantum.gabsdevops.workers.dev/mcp MCP_TOKEN=$(cat .token) \
  uv run pytest tests/test_e2e.py -v                                # cliente MCP real em produção
```

Config usada pelos clientes (Claude Code em `--mcp-config`, Cursor em `.cursor/mcp.json`):

```json
{"mcpServers": {"quantum": {"type": "http",
  "url": "https://mcp-quantum.gabsdevops.workers.dev/mcp",
  "headers": {"Authorization": "Bearer <token>"}}}}
```

| Arquivo | O que prova |
|---|---|
| `01-pytest-unitario.txt` | 19 testes: 4 tools, resources, prompts, erros e agregados x planilha |
| `02-pytest-e2e-producao.txt` | 11 testes com `ClientSession` do SDK contra a URL publicada (401, 404, tools, resources, prompt) |
| `03-inspector-sem-token-401.png` | sem header de auth o Inspector não conecta |
| `04-inspector-conectado.png` | conectado em produção, MCP 2025-11-25 |
| `05` a `08` | tools 1 a 4 executadas no Inspector |
| `09-resource-catalogo-completo.png` | resource `catalogo://produtos` |
| `10-resource-template-produto.png` | resource template `produto://P015` |
| `11-prompt-recomendar-produto.png` | prompt `recomendar_produto` com argumentos |
| `12-claude-code-oneshot.md` | `claude -p` usando as 4 tools + prompt como slash command |
| `13-cursor-oneshot.md` | `cursor-agent -p` usando as tools |

## Segurança (o mínimo que dá pra defender)

- **Bearer token** em `wrangler secret` (nunca no código), comparado com
  `hmac.compare_digest` antes de chegar no MCP. Sem token: `401` com `WWW-Authenticate`.
- **Só `/mcp` existe**; qualquer outra rota responde `404`.
- **Proteção contra DNS rebinding** do SDK ligada, com allowlist de `Host`/`Origin`.
- **Somente leitura**: nenhuma tool altera estado; o catálogo é embutido no bundle.
- Fora do escopo: OAuth por usuário, rate limiting e rotação automática do token.

## Por que essa combinação de versões

Testei com deploy real antes de fechar (plano free: 3 MB de bundle, CPU limitada):

| Tentativa | Resultado |
|---|---|
| `fastmcp` standalone | 9,5 MB gzip (puxa `cryptography`, `beartype`, `authlib`) — não cabe |
| `mcp` 2.x | importa `cryptography` no topo do módulo — não cabe |
| `mcp` 1.x + override `pyjwt` sem `[crypto]` | **2,8 MB gzip** — cabe |
| import dentro do `fetch` | 2010 ms de CPU no cold start → erro `1102` |
| import no topo (snapshot de memória do deploy) | 68–750 ms de CPU, `outcome: ok` |

O consumo de CPU passa dos 10 ms nominais do free e a Cloudflare tem tolerado; sob
carga pode aparecer `1102`. Para uso real, o plano pago (US$ 5/mês) resolve.
