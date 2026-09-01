# Evidências — Provisionamento (Terraform)

Execução real em 27-28/08/2026, região `eastus` (política de regiões
permitidas da Azure for Students bloqueia `eastus2`, o default do lab — ver
nota em `terraform/variables.tf`).

## Phase 1 — apply inicial

```
$ terraform apply main.tfplan
...
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:
resource_group_name           = "rg-qc-aula03-grupo01-ro6i2l"
catalogo_storage_account_name = "stcatqcro6i2l"
function_app_name             = "func-qc-ro6i2l"
function_app_default_hostname = "https://func-qc-ro6i2l.azurewebsites.net"
application_insights_name     = "appi-qc-aula03-ro6i2l"
application_insights_app_id   = "9d208a8b-19d9-487e-bd37-6a289a295d16"
acr_login_server               = "acrqcro6i2l.azurecr.io"
acr_name                       = "acrqcro6i2l"
```

## Deploy do código da Function

`func` core tools não estava disponível no ambiente local usado para esta
execução (a política "no install" da disciplina pressupõe Cloud Shell, que
já vem com `func`). Substituímos por
`az functionapp deployment source config-zip` (endpoint Kudu de zip deploy),
que é o mesmo mecanismo por baixo do capô — resultado equivalente:

```
$ az functionapp deployment source config-zip -g rg-qc-aula03-grupo01-ro6i2l \
    -n func-qc-ro6i2l --src /tmp/v1-mock.zip
...
"Deployment was successful."
```

Testado (v1-mock):

```
$ curl -s https://func-qc-ro6i2l.azurewebsites.net/api/health
{"status": "ok", "service": "qc-catalogo", "source": "mock"}

$ curl -s https://func-qc-ro6i2l.azurewebsites.net/api/produtos
{"total": 5, "produtos": [...]}
```

Depois substituído pela versão v2-full (blob + frete):

```
$ curl -s "https://func-qc-ro6i2l.azurewebsites.net/api/produtos?categoria=moveis"
{"total": 4, "produtos": [{"id": 1, "nome": "Cadeira Ergonômica DXRacer", ...}, ...]}
```

20 produtos reais vindos do `produtos.csv` no Blob (confirma leitura via
Managed Identity SystemAssigned, sem nenhuma credencial no código).

## Import da imagem para o ACR

```
$ az acr import --name acrqcro6i2l \
    --source ghcr.io/isaiasbritto/produtos-api:v1 \
    --image produtos-api:v1 --force

$ az acr repository list -n acrqcro6i2l -o table
Result
------------
produtos-api
```

## Phase 2 — habilitar ACI (variante padrão)

```
$ terraform apply -auto-approve -var="aci_enabled=true"
...
aci_fqdn = "qc-api-ro6i2l.eastus.azurecontainer.io"

$ curl http://qc-api-ro6i2l.eastus.azurecontainer.io:8080/health
{"status":"ok","service":"qc-catalogo","source":"blob","runtime":"container"}

$ curl "http://qc-api-ro6i2l.eastus.azurecontainer.io:8080/produtos?categoria=moveis"
{"total": 4, "produtos": [...]}
```

Managed Identity **user-assigned** confirmada funcionando (lê o mesmo Blob
que a Function, via role separada). Estado do container:

```
$ az container show -g rg-qc-aula03-grupo01-ro6i2l -n aci-qc-ro6i2l \
    --query "containers[0].instanceView.{estado:currentState.state,reinicios:restartCount}" -o table
Estado    Reinicios
--------  -----------
Running   0
```

## Variantes de hardening (Exercício 2.3) — aplicadas juntas

```
$ terraform apply -auto-approve \
    -var="aci_enabled=true" -var="aci_sized_enabled=true" -var="aci_job_enabled=true"
...
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

aci_sized_fqdn = "qc-api-sized-ro6i2l.eastus.azurecontainer.io"
aci_job_name   = "aci-qc-job-ro6i2l"
```

Job batch terminou sozinho, sem restart (ver `evidencias/aci-hardening.md`
para o detalhamento completo do 2.3).

## Destroy final (regra de ouro — custo zero)

O `terraform destroy` foi executado ao final da atividade, mas a saída do
terminal e a consulta `az group exists` não foram preservadas neste
repositório. Portanto, este pacote não contém evidência independente para
auditar a remoção do Resource Group; contém apenas o procedimento reproduzível
em [`../README.md`](../README.md).
