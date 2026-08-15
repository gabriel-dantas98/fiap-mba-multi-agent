# Evidências Bicep — Aula 1

**Data:** 10/08/2026  
**Resource Group:** `rg-bicep-aula01`  
**Região/SKU:** `chilecentral` / `Standard_B2als_v2`

## Build

```text
az bicep build --file main.bicep
bicep_build=ok
```

## Contagem de linhas

| Arquivo | Linhas |
|---------|--------|
| `bicep/main.bicep` | 191 |
| `bicep/main.json` (gerado, não versionado) | 237 |
| Terraform consolidado (`main`+`variables`+`outputs`+`versions`) | 216 |

## Deploy

```text
provisioningState: Succeeded
public_ip_address: 57.156.67.7
```

VM:

```json
{
  "location": "chilecentral",
  "name": "vm-cc-aula01-bicep",
  "power": "VM running",
  "size": "Standard_B2als_v2"
}
```

SSH:

```text
hostname=vm-bicep01
os=Ubuntu 24.04
```

Subnets confirmadas: `subnet-vm` (`10.0.1.0/24`) e `subnet-app` (`10.0.2.0/24`).

## Limpeza

```bash
az group delete --name rg-bicep-aula01 --yes --no-wait
```

Confirmação pós-limpeza (10/08/2026):

```text
az group exists -n rg-bicep-aula01 → false
```
