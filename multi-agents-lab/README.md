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
  contratos/                 YAML preenchidos (fonte da verdade do esquadrao)
  system_message.txt         PE por lacuna do Construtor
  respostas_ficha.md         tres perguntas da entrega
  run_m1_harness.py          Missao 1 + Caos, assert 100/20
  run_notebook_e2e.py        papermill do notebook local (mock|hf)
  01_bloco1_batch_LOCAL.ipynb  notebook adaptado p/ path local (sem Drive)
  01_bloco1_batch_SOLUCAO.ipynb referencia de celulas (sem outputs)
  entregas/                  notebooks EXECUTADO_* com outputs versionados
  dutos-do-q.zip             kit do professor
  dutos-do-q/                kit descompactado (libs em kit/)
  _raw/                      snapshot do Colab e YAML originais do Drive
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

1. Abra `01_bloco1_batch_SOLUCAO.ipynb` (FONTE) ou o notebook do professor.
2. Upload de `dutos-do-q.zip` (ja esta na FONTE) ou preencha `KIT_URL`.
3. **Passo 1b** — `gdown` dos 4 YAML da FONTE (`anyoneWithLink`; sem auth). Fallback:
   GitHub raw (`CONTRATOS_GIT_REF`) ou `CONTRATOS_SOURCE=local`.
4. Cole `system_message.txt` na celula do Passo 4 (arquivo tambem esta na FONTE).
5. Rode o Construtor. Se falhar 2 vezes, use o plano B (`agentes.codigo_de_referencia()`).
6. Descomente o Caos (Passo 10) e rode Bronze → Silver → Gold de novo.
7. Rode o harness com `com_caos=True`.
8. Preencha `ESQUADRAO`, cole as respostas da ficha, gere a entrega JSON.

Forcar fonte dos contratos: `CONTRATOS_SOURCE=drive|github|local`.

## Rodar local

Harness sozinho (contratos + plano B do Construtor):

```bash
cd multi-agents-lab
# deps: deltalake duckdb pyyaml pyarrow pandas sentence-transformers
python run_m1_harness.py
```

Esperado. `score=100.0 bonus_caos=20.0 total=120.0 medalha=OURO`.

Notebook E2E com outputs no `.ipynb` (papermill + kernel `fiap-mba`):

```bash
# mock: Construtor devolve codigo de referencia (sem baixar LLM)
LLM_BACKEND=mock python run_notebook_e2e.py

# hf: Qwen2.5-Coder-1.5B local (~3GB cache HF; precisa de disco)
LLM_BACKEND=hf python run_notebook_e2e.py
```

Saida. `entregas/01_bloco1_batch_EXECUTADO_<backend>.ipynb` — celula do harness com
`MISSÃO 1 · DUTO BATCH — 100.0 pontos — OURO` e `Caos: +20 → total 120.0`.

## Principios usados nesta entrega

Contrato como modelo de dominio (estrutura declarativa, nao ifs espalhados). Verificacao no
avaliador real com Caos ligado, nao so "compila".
