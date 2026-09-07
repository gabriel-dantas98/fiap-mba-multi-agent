# Evidências (resumo)

Saída bruta dos comandos que sustentam os números citados no relatório
principal. Versão completa (Terraform e Bicep separados) disponível em
`evidencias/provisionamento.md` e `evidencias/bicep.md` no repositório do
GitHub.

## Terraform (Exercício 3.1)

Restrições de ambiente (Azure for Students): `eastus2` bloqueado por
policy, `eastus` sem capacidade de `Standard_B2s` → saiu `chilecentral` +
`Standard_B2als_v2`, Ubuntu 24.04 LTS, Secure Boot + vTPM.

```text
Destroy complete! Resources: 9 destroyed.
resource_group_absent=true

Plan: 9 to add, 0 to change, 0 to destroy.
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.
public_ip_address = "57.156.58.166"
```

```json
{"location": "chilecentral", "os": "ubuntu-24_04-lts",
 "powerState": "VM running", "size": "Standard_B2als_v2"}
```

`scripts/validate-nginx.sh`: `ssh=ok`, `http=200` na página Group One
(print em `evidencias/nginx-group-one.png`).

Alteração isolada de `meu_ip` no NSG (VM fora do plano):

```text
~ resource "azurerm_network_security_group" "vm"
Plan: 0 to add, 1 to change, 0 to destroy.
```

Idempotência: `No changes. Your infrastructure matches the configuration.`

Limpeza final: `Destroy complete! Resources: 9 destroyed.` →
`az group exists -n rg-cloud-cognitive-aula01` retornou `false`.

## Bicep (Exercício 3.2)

```text
az bicep build --file main.bicep → ok
provisioningState: Succeeded
public_ip_address: 57.156.67.7
```

Linhas: `main.bicep` 191, `main.json` gerado 237, Terraform equivalente
216. Subnets confirmadas: `subnet-vm` (10.0.1.0/24), `subnet-app`
(10.0.2.0/24). SSH ok, Ubuntu 24.04.

Limpeza: `az group delete -n rg-bicep-aula01 --yes` → confirmado depois
com `az group exists -n rg-bicep-aula01` retornando `false`.
