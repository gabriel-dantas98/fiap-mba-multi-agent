# Evidências (resumo)

Saída bruta dos comandos que sustentam os números citados no relatório
principal. Versão completa, com todos os comandos e o passo a passo,
disponível em `evidencias/*.md` no repositório do GitHub.

## Provisionamento (Terraform)

```
$ terraform apply main.tfplan
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

resource_group_name           = "rg-qc-aula03-grupo01-ro6i2l"
function_app_name             = "func-qc-ro6i2l"
function_app_default_hostname = "https://func-qc-ro6i2l.azurewebsites.net"
acr_name                       = "acrqcro6i2l"
```

```
$ curl -s "https://func-qc-ro6i2l.azurewebsites.net/api/produtos?categoria=moveis"
{"total": 4, "produtos": [{"id": 1, "nome": "Cadeira Ergonômica DXRacer", ...}]}
```

20 produtos vindos do `produtos.csv` no Blob via Managed Identity, sem
nenhuma credencial no código.

## Cold start (Exercício 1.3)

```
Chamada 1 (fria, ~12 min sem tráfego): time_total=2.822712s
Chamada 2 (+5 s):                      time_total=2.745923s
Chamada 3 (fria, ~20 min sem tráfego): time_total=3.006176s
```

Isolando TLS de TTFB em `/health` (não toca o Blob): `tls=0.397s
ttfb=2.382s`. TLS estável, TTFB dominante mesmo sem I/O de dados.

## Application Insights (Exercício 2.2)

```kql
requests | summarize total=count(), p50=percentile(duration,50),
  p95=percentile(duration,95), p99=percentile(duration,99) by name
```

| Endpoint | Total | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|---|
| listar_produtos | 34 | 450.6 | 1545.8 | 1841.1 |
| frete | 30 | 687.3 | 1203.0 | 1330.9 |
| health | 2 | 12.3 | 15.6 | 15.6 |

```kql
requests | summarize total=count() by resultCode | order by resultCode asc
```

`200` → 61, `400` → 5. `success == false` deu 0 nas 66 requisições: o campo
mede exceção não tratada, não status HTTP.

`dependencies | summarize ... by type, target` voltou vazio: o SDK do Blob
Storage não gera telemetria de dependência sem instrumentação explícita.

## ACI hardening (Exercício 2.3)

```
$ az container show ... aci-qc-job-ro6i2l --query "containers[0].instanceView"
{"detailStatus": "Completed", "exitCode": 0, "state": "Terminated"}
```

Job `restart_policy=OnFailure` rodou, terminou com exit 0, não reiniciou.

```
$ az container show ... --query "containers[0].environmentVariables"
[
  {"name": "STORAGE_ACCOUNT_CATALOGO", "value": "stcatqcro6i2l", "secureValue": null},
  {"name": "APPINSIGHTS_CONNECTION_STRING", "value": null, "secureValue": null}
]
```

Variável em `secure_environment_variables` não retorna valor pela API
(`value: null`, sem máscara); as demais aparecem em texto plano.

Preço real (Azure Retail Prices API, `eastus`, 27/08/2026): vCPU
US$ 0,0405/h, memória US$ 0,00445/GB-h → 0.5vCPU/1GB ≈ US$ 18,03/mês 24/7,
1vCPU/2GB ≈ US$ 36,06/mês.

## Benchmark de carga (Exercício 3.2)

```
$ hey -n 1000 -c 50 <ACI>
Requests/sec: 157.63   p50: 0.243s   p95: 0.651s   p99: 0.775s

$ hey -n 1000 -c 50 <Function>
Requests/sec: 129.16   p50: 0.144s   p95: 2.949s   p99: 3.875s
```

946/1000 respostas da Function abaixo de 0,61s; cauda de ~48 entre 3s e
4,9s, sob rajada de 50 conexões concorrentes.

## Destroy final (custo zero)

```
$ az resource delete -g rg-qc-aula03-grupo01-ro6i2l \
    -n "Application Insights Smart Detection" --resource-type "microsoft.insights/actiongroups"
$ az group delete -n rg-qc-aula03-grupo01-ro6i2l --yes --no-wait

$ az group list --query "[?starts_with(name, 'rg-qc-aula03')]" -o table
Name    Location
------  --------
(vazio de recursos desta entrega)
```

`terraform state list` vazio após o destroy. Nenhum recurso gerenciado por
este Terraform continuou provisionado.
