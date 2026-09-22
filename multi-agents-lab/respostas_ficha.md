# Ficha de decisao · Bloco 1

## 1. Lacuna que mais mudou o harness

Lacuna 8 em `transacoes.yaml` (regras de sinal).

Preenchemos:
- `deposito_positivo`: `tipo != 'deposito' or valor > 0`
- `saida_negativa`: `tipo not in ['saque','pix','cdb_aplicacao','compra_cartao'] or valor < 0`

Evidencia no lote. T990003 e T990004 sao deposito com valor negativo. No resto do arquivo, deposito
e sempre positivo e saidas de caixa sao sempre negativas. Sem a regra, essas linhas entram na Silver
e o saldo do cliente fecha errado em silencio.

O que a regra rejeita que talvez fosse legitimo. Um estorno de deposito lancado com o mesmo `tipo`
e valor negativo. No corpus de 2026 isso nao existe. Em producao precisaria de um tipo proprio
(`estorno_deposito`), senao cai na quarentena.

Menção honrosa. Lacuna 9 (`maximo: hoje`) e o que barra o veneno do Caos
(`com-tarifa-promocional.md` com data 2027-01-01). Sem ela o harness toma -20 no Caos mesmo com o
resto perfeito.

## 2. System message e o que nao se delega

A system message precisou dizer duas coisas com numero, nao slogan.
1. Ordem clientes → tarifas → transacoes → documentos, com o motivo da FK.
2. Arquivo que quebra na leitura vai inteiro pra quarentena com `str(e)`, status quarentena, zeros
   nas contagens, +1 drift e +1 rows_rejected.

Sem a frase da FK, o Construtor de 1,5B devolve ordem alfabetica ou qualquer ordem "plausivel" e o
teste de fumaca acusa milhares de orfaos. Sem a receita do except, ele tenta `len(ok)` dentro do
except e o guardrail estatico reprova.

O que nao delegamos ao agente. O contrato de negocio (dominio, sinal, tipos nao autoritativos,
`maximo: hoje`). O modelo completa lacunas de codigo. Ele nao decide o que a Quantum considera
verdade. Isso e trabalho de arquiteto com evidência no dado.

## 3. Linha de quarentena controversa

`TF005` em tarifas, motivo `sem_sobreposicao_vigencia: sobrepoe TF001`.

TF001 (saque R$7,00, 2025-01-15 a 2026-01-09) e TF005 (saque R$6,50, 2025-06-01 a 2025-08-01)
sobrepoem. O contrato rejeita TF005. O dado nao diz qual linha e a verdade. Pode ser promocao
legitima sem fechar a vigencia anterior.

Se mudassemos o contrato para "ultima vigencia vence" e fechar TF001 automaticamente, a promocao
passaria, mas um typo curto em TF005 tambem viraria verdade sem revisao. Preferimos rejeitar e deixar
visivel na quarentena. Dado ausente revisado e melhor que resposta errada silenciosa do Q.
