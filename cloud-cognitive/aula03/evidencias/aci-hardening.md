# Evidências — Exercício 2.3 (Endurecer e dimensionar o ACI)

Três `azurerm_container_group` vivos ao mesmo tempo, todos apontando pra
mesma imagem (`produtos-api:v1`) importada no ACR, cada um demonstrando um
ponto diferente do exercício. Código em `terraform/containers.tf`.

## (a) Restart policy — job batch (`OnFailure`)

```
$ az container show -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-job-ro6i2l \
    --query "{estado:containers[0].instanceView, reinicios:containers[0].instanceView.restartCount}" -o json
{
  "estado": {
    "detailStatus": "Completed",
    "exitCode": 0,
    "finishTime": "2026-08-28T02:04:52.884000+00:00",
    "startTime": "2026-08-28T02:04:47.771000+00:00",
    "state": "Terminated"
  },
  "reinicios": 0
}

$ az container logs -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-job-ro6i2l
recalculo de recomendacoes QC: ok
```

Rodou, imprimiu, terminou com `exit 0`, **não reiniciou** — é exatamente o
comportamento de `restart_policy = OnFailure` com sucesso: só reinicia se o
processo sair com código de erro.

## (b) Right-sizing — 0.5vCPU/1GB vs 1vCPU/2GB

```
$ az container show -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-ro6i2l \
    --query "containers[0].resources.requests" -o json
{"cpu": 0.5, "memoryInGb": 1.0}

$ az container show -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-sized-ro6i2l \
    --query "containers[0].resources.requests" -o json
{"cpu": 1.0, "memoryInGb": 2.0}

$ curl http://qc-api-sized-ro6i2l.eastus.azurecontainer.io:8080/health
{"status":"ok","service":"qc-catalogo","source":"blob","runtime":"container"}
```

Preço real (Azure Retail Prices API, `eastus`, consultado 27/08/2026):

```
$ curl -sG "https://prices.azure.com/api/retail/prices" \
    --data-urlencode "\$filter=serviceName eq 'Container Instances' and armRegionName eq 'eastus' and priceType eq 'Consumption'"
...
"Standard vCPU Duration"    | "Container Instances" | 0.0405  "1 Hour"
"Standard Memory Duration"  | "Container Instances" | 0.00445 "1 GB Hour"
```

| Variante | Custo/hora | 24/7 (730h) |
|----------|-----------|-------------|
| 0.5 vCPU / 1 GB | US$ 0,0247 | US$ 18,03/mês |
| 1 vCPU / 2 GB | US$ 0,0494 | US$ 36,06/mês |

## (c) `secure_environment_variables`

```
$ az container show -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-ro6i2l \
    --query "containers[0].environmentVariables" -o json
[
  {"name": "STORAGE_ACCOUNT_CATALOGO", "secureValue": null, "value": "stcatqcro6i2l"},
  {"name": "AZURE_CLIENT_ID",          "secureValue": null, "value": "75bdaf82-..."},
  {"name": "APPINSIGHTS_CONNECTION_STRING", "secureValue": null, "value": null}
]
```

As duas primeiras (`environment_variables` no Terraform) aparecem em texto
plano. A terceira (`secure_environment_variables`) retorna `null` nos dois
campos — não é mascarada, simplesmente não é devolvida pela API. Mesmo
comportamento no portal (Container settings → Environment variables mostra
"—" pra ela).
