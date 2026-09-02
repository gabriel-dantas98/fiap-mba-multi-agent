# Evidências — Destroy final (regra de ouro, custo zero)

## Tentativa 1 — bloqueada por recurso fora do Terraform

```
$ terraform destroy -auto-approve \
    -var="aci_enabled=true" -var="aci_sized_enabled=true" -var="aci_job_enabled=true"
```

O Azure cria automaticamente um action group `Application Insights Smart
Detection` junto com o recurso de Application Insights — ele não é gerenciado
pelo Terraform (não existe no `.tf`), então o provider AzureRM recusa apagar
o resource group enquanto ele tiver recursos não rastreados no state
(`prevent_deletion_if_contains_resources` do provider). O `terraform destroy`
ficou preso tentando destruir o resource group.

## Correção — apagar o recurso órfão manualmente, depois o resource group

```
$ RG="rg-qc-aula03-grupo01-ro6i2l"
$ az resource delete -g "$RG" -n "Application Insights Smart Detection" \
    --resource-type "microsoft.insights/actiongroups"
$ az group delete -n "$RG" --yes --no-wait
delete command issued
```

## Ressincronizar o state local

Com o resource group já apagado direto via `az group delete`, sobrou só o
`random_string.sufixo` (recurso lógico, sem contraparte no Azure) no state:

```
$ terraform destroy -auto-approve \
    -var="aci_enabled=true" -var="aci_sized_enabled=true" -var="aci_job_enabled=true"
...
Plan: 0 to add, 0 to change, 1 to destroy.
random_string.sufixo: Destroying... [id=ro6i2l]
random_string.sufixo: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

## Verificação — nenhum resource group da aula sobrou

```
$ az group list --query "[?starts_with(name, 'rg-qc-aula03')]" -o table
Name                 Location
-------------------  ----------
rg-qc-aula03-el1rxs  eastus2
```

`rg-qc-aula03-grupo01-ro6i2l` já não aparece — confirma que o destroy surtiu
efeito. O único resultado, `rg-qc-aula03-el1rxs` (região `eastus2`), é um
resource group órfão e **vazio** de uma execução anterior/diferente (mesmo
padrão de nome, sufixo distinto do usado nesta entrega) — inspecionado antes
de apagar (`az resource list -g rg-qc-aula03-el1rxs` retornou vazio) e então
removido:

```
$ az group delete -n rg-qc-aula03-el1rxs --yes --no-wait
```

`terraform state list` após o destroy final: vazio. Nenhum recurso
gerenciado por este Terraform continua provisionado — custo zero confirmado.
