# Bicep — Aula 1

Equivalente Azure-native do lab Terraform.

## Pré-requisitos

- Azure CLI + `az bicep`
- Assinatura Azure for Students (ou equivalente)
- Chave pública SSH

## Deploy

```bash
export MEU_IP="$(curl --fail --silent --show-error https://api.ipify.org)"
export SSH_PUB="$(< ~/.ssh/id_ed25519.pub)"

az group create \
  --name rg-bicep-aula01 \
  --location chilecentral

az deployment group create \
  --resource-group rg-bicep-aula01 \
  --template-file main.bicep \
  --parameters meu_ip="$MEU_IP" adminPublicKey="$SSH_PUB"
```

## Validar

```bash
az deployment group show \
  --resource-group rg-bicep-aula01 \
  --name main \
  --query properties.outputs
```

## Remoção do ambiente

```bash
az group delete --name rg-bicep-aula01 --yes --no-wait
```

## Notas Azure for Students

Mesma restrição do Terraform: `eastus2` bloqueado pela policy regional;
capacidade/SKU levaram a `chilecentral` + `Standard_B2als_v2`.
