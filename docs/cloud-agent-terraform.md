# Cloud Agent — Terraform / Azure

Config do environment em [`.cursor/`](../.cursor/): imagem com Terraform `1.11.4` + Azure CLI, `install` via `uv sync`.

## Secrets (dashboard do environment)

Criar no Cloud Agents → Environment → Secrets (nunca commitar):

| Nome | Obrigatório | Uso |
|------|-------------|-----|
| `ARM_CLIENT_ID` | sim (plan/apply) | App ID do Service Principal |
| `ARM_CLIENT_SECRET` | sim (plan/apply) | Secret do SP |
| `ARM_TENANT_ID` | sim (plan/apply) | Tenant Entra ID |
| `ARM_SUBSCRIPTION_ID` | sim (plan/apply) | Subscription do lab |
| `TF_VAR_ssh_public_key` | aula01 apply | Chave pública OpenSSH |
| `TF_VAR_meu_ip` | aula01 apply (opcional) | IPv4 liberado no NSG SSH; se omitir, o agent pode usar o IP egress da VM |

O provider `azurerm` e o `az` CLI leem `ARM_*` automaticamente (sem `az login` interativo).

SP sugerido: **Contributor** no Resource Group do lab (ou subscription Students), não Owner da conta.

## O que o agent consegue

- Sem secrets: `terraform fmt`, `validate`, `init -backend=false` (ex.: `cloud-cognitive/aula01/scripts/check-terraform.sh`)
- Com `ARM_*`: `plan` / `apply` / `destroy` + `az` (zip deploy Function, ACR, etc.)

State é **local** nos labs — apply no agent não compartilha state com a sua máquina. Preferir remote backend se apply no agent for o fluxo padrão.

## Smoke local na imagem

```bash
terraform version
az version
cd cloud-cognitive/aula01 && ./scripts/check-terraform.sh
```
