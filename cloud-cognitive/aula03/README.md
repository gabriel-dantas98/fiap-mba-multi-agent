# Entrega da Aula 3 — Serverless & Containers

Estrutura das pastas alinhadas ao template e ao roteiro do lab.

```text
aula03/
├── entrega-grupo-aula03.md
├── README.md
├── diagramas/
│   └── arquitetura-qc-aula03.mmd
├── terraform/
│   ├── main.tf           # RG, Service Plan (FC1)
│   ├── storage.tf         # Storage da Function + Storage do catálogo (produtos.csv)
│   ├── function.tf        # Function App Flex Consumption + Managed Identity
│   ├── insights.tf        # Application Insights (Exercício 2.2)
│   ├── containers.tf      # ACR + 3 variantes de ACI (Exercício 2.3)
│   ├── variables.tf
│   └── outputs.tf
├── function/
│   ├── v1-mock/           # Versão L₁ do lab (5 produtos hardcoded)
│   ├── v2-full/           # Versão L₂ do lab (Blob via MI) + Exercício 2.1 (frete)
│   ├── tests/             # pytest (Exercício 3.3)
│   └── data/produtos.csv
├── docker/                 # Código de referência do container (a imagem em si
│                            # vem pronta do GHCR do professor, via az acr import)
└── evidencias/
```

## Pré-requisitos

- Terraform `>= 1.5`
- Azure CLI autenticado
- `hey` (benchmark do Exercício 3.2) — `brew install hey` ou já vem no Cloud Shell

```bash
az account show --output table
```

### Nota de ambiente

O roteiro da disciplina pressupõe Azure Cloud Shell ("no install"). Executamos
a partir de máquina local com Azure CLI + Terraform — mesmos comandos, mesmo
resultado. A única divergência real: `func` core tools (deploy da Function)
não estava disponível localmente, então usamos
`az functionapp deployment source config-zip` (mesmo mecanismo de zip deploy
por baixo do capô) em vez de `func azure functionapp publish`.

### Região

A política de regiões da nossa Azure for Students libera só `eastus`,
`chilecentral`, `brazilsouth`, `canadacentral` e `centralus` — `eastus2`
(default do lab) está bloqueado:

```bash
SUBSCRIPTION_ID="$(az account show --query id --output tsv)"
az policy assignment list \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --disable-scope-strict-match \
  --query "[?name=='sys.regionrestriction'].parameters.listOfAllowedLocations.value[]" \
  --output tsv
```

`eastus` também suporta Flex Consumption (FC1) — confirmado com
`az functionapp list-flexconsumption-locations` — por isso ficou o default
em `terraform/variables.tf`.

## Terraform — Phase 1 (Function + Storage + App Insights + ACR, sem ACI)

```bash
cd cloud-cognitive/aula03/terraform
terraform init
terraform plan -out main.tfplan
terraform apply main.tfplan
```

## Deploy do código da Function

```bash
RG=$(terraform output -raw resource_group_name)
FUNC_NAME=$(terraform output -raw function_app_name)

cd ../function/v2-full   # ou v1-mock/ para a versão mock
zip -r /tmp/func.zip . -x "*.pyc"
az functionapp deployment source config-zip -g "$RG" -n "$FUNC_NAME" --src /tmp/func.zip
```

Testar:

```bash
HOSTNAME=$(cd ../../terraform && terraform output -raw function_app_default_hostname)
curl -s "$HOSTNAME/api/health"
curl -s "$HOSTNAME/api/produtos?categoria=moveis"
curl -s "$HOSTNAME/api/frete?cep_origem=01310930&cep_destino=20040020&peso=2.5"
```

## Container — import do GHCR + Phase 2 (ACI)

```bash
cd ../../terraform
ACR_NAME=$(terraform output -raw acr_name)

az acr import --name "$ACR_NAME" \
  --source ghcr.io/isaiasbritto/produtos-api:v1 \
  --image produtos-api:v1 --force

# Habilita as 3 variantes do Exercício 2.3 de uma vez
terraform apply -auto-approve \
  -var="aci_enabled=true" -var="aci_sized_enabled=true" -var="aci_job_enabled=true"
```

Testar:

```bash
ACI_FQDN=$(terraform output -raw aci_fqdn)
sleep 60   # propagação da Managed Identity
curl "http://$ACI_FQDN:8080/health"
curl "http://$ACI_FQDN:8080/produtos?categoria=moveis"
```

## Testes e lint (Exercício 3.3)

```bash
cd ../function
pip install ruff pytest -r v2-full/requirements.txt
ruff check .
pytest tests/ -v
```

## Benchmark (Exercício 3.2)

```bash
hey -n 1000 -c 50 "$HOSTNAME/api/produtos?categoria=moveis"
hey -n 1000 -c 50 "http://$ACI_FQDN:8080/produtos?categoria=moveis"
```

## Diagrama

```bash
npx --yes @mermaid-js/mermaid-cli \
  -i cloud-cognitive/aula03/diagramas/arquitetura-qc-aula03.mmd \
  -o cloud-cognitive/aula03/diagramas/arquitetura-qc-aula03.png \
  -w 2400 -b transparent
```

## Limpeza — regra de ouro (custo zero)

```bash
cd terraform
terraform destroy -auto-approve \
  -var="aci_enabled=true" -var="aci_sized_enabled=true" -var="aci_job_enabled=true"
```

## Gerar o ZIP para envio ao Portal FIAP

```bash
git archive \
  --format=zip \
  --prefix=qc-grupo-01-aula03/ \
  --output=entrega-grupo-01-aula03.zip \
  HEAD:cloud-cognitive/aula03

# adicionar o workflow de CI/CD, que fica fora desta pasta:
mkdir -p /tmp/entrega-extra/.github/workflows
cp ../../.github/workflows/deploy-function.yml /tmp/entrega-extra/.github/workflows/
```

Não incluir `.terraform/`, `*.tfstate*`, `*.tfplan`.
