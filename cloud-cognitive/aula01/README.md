# Entrega da Aula 1

Estrutura das pastas e arquivos alinhados ao template e à anotações oficiais.

```text
aula01/
├── entrega-grupo-aula01.md
├── README.md
├── diagramas/
│   ├── arquitetura-qc-aula01.mmd|.png
│   └── arquitetura-qc-multicloud.mmd|.png
├── terraform/
├── bicep/
├── nginx/index.html
├── scripts/
│   ├── validate-nginx.sh
│   ├── check_calcs.py
│   └── check-terraform.sh
└── evidencias/
```

## Pré-requisitos

- Terraform `>= 1.5`
- Azure CLI autenticado
- `az bicep` (ou `az bicep install`)
- Chave pública SSH

```bash
az account show --output table
```

### Azure for Students

Policy regional e capacidade/SKU forçaram defaults `chilecentral` + `Standard_B2als_v2`. 
Unico tipo que funcionou para o nosso caso de Azure for Students.

```bash
SUBSCRIPTION_ID="$(az account show --query id --output tsv)"
az policy assignment list \
  --scope "/subscriptions/$SUBSCRIPTION_ID" \
  --disable-scope-strict-match \
  --query "[?name=='sys.regionrestriction'].parameters.listOfAllowedLocations.value[]" \
  --output tsv
```

## Checks (cálculos + Terraform)

```bash
python3 cloud-cognitive/aula01/scripts/check_calcs.py
cloud-cognitive/aula01/scripts/check-terraform.sh
```

`check-terraform.sh` é o `tsc --noEmit` do lab: `terraform fmt -check` + `terraform validate`, sem apply.

## Terraform

```bash
cd cloud-cognitive/aula01/terraform
export TF_VAR_subscription_id="$(az account show --query id --output tsv)"
export TF_VAR_meu_ip="$(curl --fail --silent --show-error https://api.ipify.org)"
export TF_VAR_ssh_public_key="$(< ~/.ssh/id_ed25519.pub)"

terraform fmt -check
terraform init
terraform validate
terraform plan -out main.tfplan
terraform apply main.tfplan
terraform output -raw public_ip_address
```

Validar SSH + HTTP:

Usamos NGINX para validar o SSH e HTTP.

```bash
cloud-cognitive/aula01/scripts/validate-nginx.sh
```

Alterar só `TF_VAR_meu_ip` deve atualizar apenas a regra SSH do NSG (sem recriar a VM).

Limpeza:

```bash
terraform destroy
unset TF_VAR_subscription_id TF_VAR_meu_ip TF_VAR_ssh_public_key
```

## Bicep

Ver [`bicep/README.md`](bicep/README.md). Resumo:

```bash
export MEU_IP="$(curl --fail --silent --show-error https://api.ipify.org)"
export SSH_PUB="$(< ~/.ssh/id_ed25519.pub)"
az group create --name rg-bicep-aula01 --location chilecentral
az deployment group create \
  --resource-group rg-bicep-aula01 \
  --template-file cloud-cognitive/aula01/bicep/main.bicep \
  --parameters meu_ip="$MEU_IP" adminPublicKey="$SSH_PUB"
az group delete --name rg-bicep-aula01 --yes --no-wait
```

## Diagramas usando CLI Mermaid para gerar imagens da arquitetura

```bash
npx --yes @mermaid-js/mermaid-cli \
  -i cloud-cognitive/aula01/diagramas/arquitetura-qc-aula01.mmd \
  -o cloud-cognitive/aula01/diagramas/arquitetura-qc-aula01.png \
  -w 2400 -b transparent

npx --yes @mermaid-js/mermaid-cli \
  -i cloud-cognitive/aula01/diagramas/arquitetura-qc-multicloud.mmd \
  -o cloud-cognitive/aula01/diagramas/arquitetura-qc-multicloud.png \
  -w 2200 -b transparent
```

## Gerar o ZIP para envio ao Portal FIAP

```bash
git archive \
  --format=zip \
  --prefix=qc-grupo-01-aula01/ \
  --output=entrega-grupo-01-aula01.zip \
  HEAD:cloud-cognitive/aula01
```

Não incluir `terraform.tfstate*`, `.env`, `*.pem`, `main.json` gerado do Bicep.
