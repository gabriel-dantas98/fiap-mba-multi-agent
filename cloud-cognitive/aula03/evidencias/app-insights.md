# Evidências — Exercício 2.2 (Application Insights)

Recurso: `appi-qc-aula03-ro6i2l` (workspace-based, `law-qc-aula03-ro6i2l`),
conectado à Function via `application_insights_connection_string`.

## Por que não tem print do portal

A automação de browser usada nesta sessão (extensão Chrome MCP) não tinha
permissão de site liberada para `portal.azure.com` — retornou
`Permission denied for this action on this domain` ao tentar tirar
screenshot. Não é uma limitação do Azure nem dos dados; é uma limitação da
ferramenta de automação desta sessão específica, que exige liberação manual
por domínio e não pode ser concedida programaticamente. Optamos por
documentar via `az monitor app-insights query` (KQL real, contra o recurso
provisionado de verdade) em vez de simular ou pular o exercício.

## Tráfego gerado (66 requisições, mix real de sucesso e erro)

- 44 requisições válidas a `/produtos` (categorias variadas, incluindo uma
  categoria inexistente para gerar lista vazia sem erro)
- 15 requisições válidas a `/frete`
- 5 requisições propositalmente malformadas a `/frete` (sem `peso`) → `400`
- 3 requisições a rota inexistente `/api/naoexiste` → `404` (nem chegou a
  gerar telemetria de `request`, pois o Function host responde antes de
  invocar qualquer função)
- 2 requisições a `/health`

## Query 1 — latência por endpoint

```kql
requests
| summarize total=count(), p50=percentile(duration,50),
            p95=percentile(duration,95), p99=percentile(duration,99)
  by name
```

```json
[
  ["listar_produtos", 34, 450.5514, 1545.8155, 1841.0649],
  ["frete",           30, 687.2673, 1202.9689, 1330.9403],
  ["health",           2,  12.2560,   15.5899,   15.5899]
]
```

## Query 2 — distribuição de resultCode

```kql
requests | summarize total=count() by resultCode | order by resultCode asc
```

```json
[["200", 61], ["400", 5]]
```

`success == false` deu **zero** nas 66 requisições — o campo mede exceção
não tratada, não status HTTP. Os 5 retornos `400` foram respostas
propositais e válidas do próprio código (parâmetro faltando), então nunca
contam como "falha" pra essa métrica. Taxa de erro HTTP real: 5/66 ≈ 7,6%.

## Query 3 — dependencies (Blob Storage)

```kql
dependencies | summarize total=count(), p95=percentile(duration,95) by type, target
```

```json
[]
```

Vazio. O SDK `azure-storage-blob` não gera telemetria de `dependency`
automaticamente no worker Python de Azure Functions sem instrumentação
OpenTelemetry/OpenCensus explícita — a chamada ao Blob acontece, mas não é
medida por padrão. É um achado relevante para o Exercício 2.2(d): sem
instrumentar explicitamente, você não vê onde o tempo realmente vai.
