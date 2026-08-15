# Bicep — Aula 1

Seguindo a mesma ideia do lab Terraform, só que nativo do Azure.

## Pré-requisitos

- Azure CLI + `az bicep`
- Assinatura Azure for Students (ou parecida)
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

Tivemos a mesma restrição do Terraform: `eastus2` bloqueado pela policy da region;
capacidade/SKU levaram a `chilecentral` + `Standard_B2als_v2`.
