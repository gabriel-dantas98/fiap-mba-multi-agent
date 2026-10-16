# Ficha de decisao · Bloco 1

## D1. A lacuna mais cara

A lacuna 8, as regras de sinal em `transacoes.yaml`.

```yaml
regras:
  - {nome: deposito_positivo, expr: "tipo != 'deposito' or valor > 0"}
  - {nome: saida_negativa,    expr: "tipo not in ['saque','pix','cdb_aplicacao','compra_cartao'] or valor < 0"}
```

No CSV, deposito quase sempre vem positivo e saida (`saque`, `pix`, `cdb_aplicacao`, `compra_cartao`) negativo. As unicas quebadas plantadas sao T990003 e T990004 (deposito negativo). Sem a regra o harness de contagem ainda passa, mas o saldo da Marina fecha errado e ninguem percebe.

O que a gente perde: estorno lancado como `deposito` negativo cairia na quarentena. No lote de 2026 isso nao existe; em producao provavelmente viraria outro tipo no dominio.

Obs: a lacuna 9 (`maximo: hoje`) e a que segura o veneno do Caos (`com-tarifa-promocional.md`, data 2027-01-01). Sem ela o bonus vira -20 mesmo com o resto ok.

---

## D2. O que faltava na instrucao

A system message tinha que ser bem direta, quase um PE por lacuna (o Construtor 1.5B completa tres buracos, nao o modulo inteiro):

1. `___ORDEM_DAS_FONTES___` → `sorted(...)` com clientes=0 antes de transacoes.
2. `___REFERENCIAS_PARA_FK___` → dict `{"clientes": ...}` so se `fonte == "transacoes"`, senao `{}`.
3. `___O_QUE_FAZER_COM_O_ARQUIVO_INVALIDO___` → quatro linhas no except, sem `ok`/`q`/`df`, `marcar_processado(..., 0, 1)`.

Sem isso o teste de fumaca acusa orfaos ou NameError.

O que a gente nao passa pro agente: o contrato de negocio (dominios, sinal, `tipos_nao_autoritativos`, `maximo: hoje`). O modelo completa codigo; nao decide o que a Quantum considera verdade.

---

## D3. A linha da quarentena que discordamos

TF005 em tarifas, motivo `sem_sobreposicao_vigencia: sobrepoe TF001`.

TF001: saque R$7,00, 2025-01-15 a 2026-01-09. TF005: saque R$6,50, 2025-06-01 a 2025-08-01 — periodo inteiro dentro de TF001. O contrato rejeita TF005.

Pode ser promocao legitima e a gente esta rejeitando a linha certa. O arquivo nao diz qual das duas e a verdade.

Se mudasse pra auto-fechar a vigencia antiga na data da nova, a promocao passaria, mas um typo curto tambem. Preferimos deixar na quarentena e revisar: tarifa errada quietinha no indice do Q e pior que dado faltando.
