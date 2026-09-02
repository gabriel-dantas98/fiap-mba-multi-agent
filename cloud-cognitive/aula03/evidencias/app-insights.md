# Evidências — Exercício 2.2 (Application Insights)

Recurso: `appi-qc-aula03-ro6i2l` (workspace-based, `law-qc-aula03-ro6i2l`),
conectado à Function via `application_insights_connection_string`.

## Por que não tem print do portal

Não conseguimos acessar o `portal.azure.com` a partir do ambiente usado na
atividade, então o print obrigatório do Live Metrics não foi produzido. As
consultas KQL abaixo são reais, mas não substituem esse item do enunciado.

## Tráfego preservado na consulta (66 requisições)

- 34 requisições válidas a `/produtos`
- 25 requisições válidas a `/frete`
- 5 requisições propositalmente malformadas a `/frete` (sem `peso`) → `400`
- 2 requisições a `/health`

Também fizemos três chamadas a `/api/naoexiste` que retornaram `404`, mas elas
não aparecem no resultado preservado da tabela `requests`; por isso não entram
na soma de 66.

### Comandos que geraram a maior parte desse tráfego

```
$ for i in $(seq 1 20); do
    cat=("moveis" "eletronicos" "calcados" "vestuario" "eletrodomesticos" "acessorios" "naoexiste")
    c=${cat[$((RANDOM % ${#cat[@]}))]}
    curl -s -o /dev/null -w "%{http_code} " "$HOSTNAME/api/produtos?categoria=$c"
    curl -s -o /dev/null -w "%{http_code} " "$HOSTNAME/api/frete?cep_origem=0131093$((RANDOM%10))&cep_destino=2004002$((RANDOM%10))&peso=$((RANDOM%10+1))"
  done
200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200

$ for i in $(seq 1 10); do curl -s -o /dev/null -w "%{http_code} " "$HOSTNAME/api/produtos?nome=cadeira"; done
200 200 200 200 200 200 200 200 200 200

$ for i in $(seq 1 5); do curl -s -o /dev/null -w "%{http_code} " "$HOSTNAME/api/frete?cep_origem=01310930&cep_destino=20040020"; done
400 400 400 400 400

$ for i in $(seq 1 3); do curl -s -o /dev/null -w "%{http_code} " "$HOSTNAME/api/naoexiste"; done
404 404 404
```

→ 30 requisições a `/produtos` (categoria aleatória, incluindo o valor
`"naoexiste"` como *valor de categoria inexistente* — retorna lista vazia com
`200`, não confundir com a rota inexistente abaixo) + 20 a `/frete` válidas +
5 a `/frete` malformadas (`400`) + 3 à rota `/api/naoexiste` (`404`, sem
telemetria de `request`). O restante — 4 requisições a `/produtos`, 5 a
`/frete` e 2 a `/health` — veio de chamadas avulsas de outros exercícios
(Exercício 1.3, ver `evidencias/cold-start.md`, e testes manuais do 2.1/2.3
em `evidencias/provisionamento.md`) que caíram na mesma janela de telemetria.
A Query 1 abaixo — direto contra o recurso real via `az monitor
app-insights query` — é a fonte de verdade para os totais usados no
relatório, não a soma manual dos comandos de geração de tráfego.

## Query 1 — latência por endpoint

Forma reproduzível da consulta preservada:

```bash
RG="rg-qc-aula03-grupo01-ro6i2l"
APP_INSIGHTS="appi-qc-aula03-ro6i2l"

az monitor app-insights query \
  --resource-group "$RG" \
  --app "$APP_INSIGHTS" \
  --analytics-query "requests | summarize total=count(), p50=percentile(duration,50), p95=percentile(duration,95), p99=percentile(duration,99) by name" \
  --offset 1h
```

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
