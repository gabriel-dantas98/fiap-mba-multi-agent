# Ficha de decisao · Bloco 1

## D1. A lacuna mais cara

**Lacuna 8  -  regras de sinal em `transacoes.yaml`.**

Preenchimento:

```yaml
regras:
  - {nome: deposito_positivo, expr: "tipo != 'deposito' or valor > 0"}
  - {nome: saida_negativa,    expr: "tipo not in ['saque','pix','cdb_aplicacao','compra_cartao'] or valor < 0"}
```

**Evidência:** no `transacoes.csv` inicial (2.011 linhas), depósitos legítimos são sempre positivos e saídas (`saque`, `pix`, `cdb_aplicacao`, `compra_cartao`) sempre negativas. As únicas violações plantadas são T990003 (`deposito`, -300,00) e T990004 (`deposito`, -10,00). Sem a regra, o harness de integridade ainda passa por contagem  -  mas o saldo da Marina (e de qualquer cliente afetado) fecha errado sem alerta.

**Falso positivo:** estorno operacional lançado como `tipo=deposito` com valor negativo. No corpus de 2026 não existe; em produção exigiria `estorno_deposito` no domínio.

**Menção:** Lacuna 9 (`maximo: hoje`) é a que barra o veneno do Caos (`com-tarifa-promocional.md`, data 2027-01-01). Sem ela, o bônus Caos vira -20 mesmo com o resto perfeito.

---

## D2. O que faltava na instrução

A system message precisou de duas receitas com número, não slogan:

1. **Ordem:** `clientes → tarifas → transacoes → documentos`, com o motivo da FK (`transacoes.cliente_id` → `clientes`). Sem isso, o Construtor de 1,5B devolve ordem alfabética e o teste de fumaça acusa milhares de órfãos.
2. **Arquivo inteiro inválido:** no `except`, gravar quarentena com `str(e)`, marcar processado com status `quarentena` e contagens zero, depois `drift += 1` e `rows_rejected += 1`  -  sem usar `len(ok)`/`len(q)` que não existem no bloco de exceção.

No Colab o Construtor frequentemente erra `refs` como dict `{"clientes": conjunto}` só em `transacoes`; o plano B (`codigo_de_referencia`) preserva a missão.

**Não delegamos ao agente:** o contrato de negócio (domínios, sinal, `tipos_nao_autoritativos`, `maximo: hoje`). O modelo completa lacunas de código; não decide o que a Quantum considera verdade.

---

## D3. A linha da quarentena que discordamos

**TF005** (fonte `tarifas`), motivo `sem_sobreposicao_vigencia: sobrepõe TF001`.

TF001: saque R$7,00, 2025-01-15 a 2026-01-09. TF005: saque R$6,50, 2025-06-01 a 2025-08-01  -  período inteiro dentro de TF001. O contrato rejeita TF005.

**Discordância:** o dado não diz qual linha está errada. TF005 pode ser promoção legítima; nesse caso TF001 deveria ter sido partida em duas vigências. A quarentena expõe o conflito mas não resolve qual tarifa vale em julho/2025.

**Mudança possível:** auto-fechar vigência da tarifa mais antiga na data de início da nova. **Custo:** typos curtos viram verdade sem revisão humana. Preferimos rejeitar e revisar: tarifa errada silenciosa no índice do Q é pior que dado ausente na quarentena.
