# multi-agents-lab · Os Dutos do Q · Bloco 1

Exercicio do notebook Colab `01_bloco1_batch.ipynb` (pasta Drive FONTE + kit do professor).

Meta do harness. bronze 60 · prata 80 · ouro 95. Caos vale de -20 a +20.

Resultado medido neste repo (2026-09-22), com `com_caos=True` e contratos preenchidos.

```
MISSÃO 1 · DUTO BATCH — 100.0 pontos — OURO
Caos: +20 → total 120.0
```

Prova local. `LLM_BACKEND=mock python professor/validar_kit.py` dentro de `dutos-do-q/`
(ou `python run_m1_harness.py` a partir desta pasta).

## O que e a missao

Voce nao escreve o pipeline do zero. Voce preenche o **contrato de dados** (11 lacunas nos 4 YAML)
e a **system message** do Agent 1 Construtor. O harness mede tabelas Silver/Gold, quarentena,
retrieval e resistencia ao pacote Caos. Ele nao le o codigo.

## Layout

```
multi-agents-lab/
  contratos/           YAML preenchidos (fonte da verdade do esquadrao)
  system_message.txt   ordem das fontes + tratamento de arquivo quebrado
  respostas_ficha.md   tres perguntas da entrega
  run_m1_harness.py    Missao 1 + Caos, assert 100/20
  dutos-do-q.zip       kit do professor
  dutos-do-q/          kit descompactado (libs em kit/)
  _raw/                snapshot do Colab e YAML originais do Drive
```

## As 11 lacunas (preenchimento que passa)

| # | Fonte | Campo | Valor |
|---|---|---|---|
| 1 | clientes | encodings | `[utf-8, latin-1]` |
| 2 | clientes | duplicatas | `manter_primeira` |
| 3 | clientes | cpf.validador | `cpf` (nao `cpf_ok`) |
| 4 | clientes | segmento.dominio | `[varejo, black, private]` |
| 5 | transacoes | chave | `[transacao_id]` |
| 6 | transacoes | cliente_id.fk | `{tabela: clientes, coluna: cliente_id}` |
| 7 | transacoes | data.formatos | `["%Y-%m-%d", "%d/%m/%Y"]` |
| 8 | transacoes | regras | deposito_positivo + saida_negativa |
| 9 | documentos | data.maximo | `hoje` |
| 10 | documentos | tipos_nao_autoritativos | `[marketing, rascunho, faq-antigo]` |
| 11 | tarifas | regras_conjunto | `sem_sobreposicao_vigencia` em `tipo` |

Armadilhas do YAML que estava no Drive. `validador: cpf_ok` nao aciona o motor.
`chave: transacao_id` sem lista quebra o MERGE. `valor > 0` em regras mata todos os saques.
`tipos_nao_autoritativos: TODO` deixa ruido no indice. `regras_conjunto: TODO` deixa 5 tarifas.

## Rodar no Colab

1. Upload de `dutos-do-q.zip` (ja esta na pasta FONTE do Drive) ou preencha `KIT_URL`.
2. Copie os 4 YAML de `contratos/` para `dutos-do-q/contratos/` no painel de arquivos.
3. Cole `system_message.txt` na celula do Passo 4.
4. Rode o Construtor. Se falhar 2 vezes, use o plano B (`agentes.codigo_de_referencia()`).
5. Descomente o Caos (Passo 10) e rode Bronze → Silver → Gold de novo.
6. Rode o harness com `com_caos=True`.
7. Preencha `ESQUADRAO`, cole as respostas da ficha, gere a entrega JSON.

## Rodar local

```bash
cd multi-agents-lab
# deps: deltalake duckdb pyyaml pyarrow pandas sentence-transformers
python run_m1_harness.py
```

Esperado. `score=100.0 bonus_caos=20.0 total=120.0 medalha=OURO`.

## Principios usados nesta entrega

Contrato como modelo de dominio (estrutura declarativa, nao ifs espalhados). Verificacao no
avaliador real com Caos ligado, nao so "compila".
