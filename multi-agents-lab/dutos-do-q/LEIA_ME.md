# Os Dutos do Q — kit da aula

Integração e Ingestão de Dados para agentes · MBA FIAP · 4 horas presenciais · esquadrões de 4.

Continuação direta da Operação Q: lá os esquadrões construíram os órgãos do agente Q da Quantum Finance.
Aqui eles constroem a fundação de dados que sustenta esse agente, e descobrem quanto dela sobrevive à
mudança.

---

## Para o aluno: como rodar

1. Abra o Google Colab e faça upload dos três notebooks da pasta `notebooks/`.
2. Rode o **00_preparar.ipynb** inteiro, uma vez. Ele instala o que falta e traz o kit.
3. Bloco 1: **01_bloco1_batch.ipynb**.
4. Bloco 2: **02_bloco2_incremental.ipynb**.

Não precisa de conta além do Google, nem de token, nem de cartão. Nada do que você roda aqui sai da
sua sessão do Colab.

Se alguma coisa travar: `Ambiente de execução > Reiniciar sessão` e rode o notebook de novo do começo.
Com o lakehouse zerado, o ciclo completo leva menos de um minuto, então reiniciar é barato.

---

## Para o professor

### O que o kit é

Um lakehouse Delta rodando dentro do Colab, sem Spark e sem cluster. `deltalake` (delta-rs) dá transação,
MERGE, time travel e Change Data Feed; o DuckDB consulta as mesmas tabelas com `delta_scan`. A semântica
é a do Databricks, que é o que a aula avalia. O que não existe aqui é o executor distribuído, e com 2.243
linhas isso não faz falta.

### Estrutura

```
dutos-do-q/
  notebooks/       00_preparar · 01_bloco1_batch · 02_bloco2_incremental
  contratos/       os 4 YAML que o esquadrão edita (é aqui que ficam as decisões)
  dados/
    inbox/         o lote inicial: clientes.csv, transacoes.csv, tarifas.parquet, docs/*.md
    caos/          os 6 arquivos que o professor solta aos 40 min de prática
    bcb/           snapshot real das séries SGS 12, 4389 e 1
    linha_do_tempo.json   os 9 eventos da fonte mutável
    memorias_seed.json    as memórias do Q usadas no caso Marina
  kit/
    lake.py        Delta + DuckDB: a plataforma
    contrato.py    o motor de contrato (correções, regras, FK, duplicatas, vigência)
    fundacao.py    a Fundação lacrada que o Agent 1 compõe
    dutos.py       Bronze, Gold, incremental (CDF), externo (BCB), views, fonte mutável
    agentes.py     Agent 1 Construtor e Agent 2 Auditor, mais o cliente de LLM
    agente.py      memória e cache do Q (os órgãos que vivem fora do lakehouse)
    avaliacao.py   o harness das duas missões e do Auditor
    referencia.py  o módulo que o Construtor deveria produzir (plano B e gabarito)
  professor/
    gerar_dados.py      regera o corpus (seed fixa; só rode se quiser mudar os dados)
    montar_notebooks.py regera os 3 notebooks a partir do código
    validar_kit.py      a checagem de D-1
```

### Antes da aula

```bash
python professor/validar_kit.py
```

Roda as duas missões nos dois modos, mais o Construtor e o Auditor, com backend mock. Leva cerca de 30
segundos e não baixa modelo de linguagem. Se qualquer número da calibração mudar, ele acusa.

Calibração medida (2 vCPU):

| Item | Referência | Ingênuo |
|---|---|---|
| Missão 1 | 100 (ouro) + 20 de bônus no Caos | duplica os dados na 2ª execução |
| Missão 1, 2ª execução | 0 embeddings | 153 re-embeddings |
| Missão 2 | 100 (ouro), 2 embeddings em 8 eventos | perde tarifas e LGPD |
| Auditor | 100, com a alucinação plantada descartada | — |
| Ciclo completo | ~13 s | — |

### O LLM

Qwen2.5-Coder-1.5B-Instruct dentro do notebook, em bfloat16, CPU. Baixa ~3 GB por sessão. Não depende
de conta, token, cota nem GPU.

Com `LLM_BACKEND=mock` o kit roda inteiro com respostas canônicas, sem baixar nada. É o modo do
`validar_kit` e a saída de emergência se o download travar no dia.

Se um esquadrão empacar na geração, a célula de plano B do notebook 1 adota `referencia.py`: perdem os
pontos da geração, não a missão.

### Nota e fichas

Harness 60% · fichas de decisão 30% · julgamento 10%. Cada notebook termina com três perguntas de ficha.
As metas do harness são bronze 60, prata 80, ouro 95.

### Os 9 eventos da fonte mutável

| Evento | O que é | O que testa |
|---|---|---|
| 1 | comunicado novo | o duto pega o que entrou |
| 2 | edição de texto | re-embedding obrigatório, e a versão antiga sai de vigente |
| 3 | edição só de metadado | re-embedding desnecessário: o vetor não depende da área |
| 4 | mudança de tarifa | fecha vigência, abre nova, avisa o agente pelo outbox |
| 5 | comunicado revogado | deleção propagada até o índice |
| 6 | pedido LGPD da Marina | eliminação multi-órgão: Silver, índice, memória e cache |
| 7 | reenvio idêntico | at-least-once: versão nova sem dado novo |
| 8 | regravação completa | o CDF mostra tudo como delete + insert, e nada mudou |
| 9 | corrida de freshness | o caminho inteiro, da fonte à resposta liberada |

### O que ficou de fora, e por quê

Databricks, Unity Catalog, Auto Loader, Vector Search, Jobs API, dois tokens PAT e o simulador. Tudo
isso existia na versão anterior do kit e custava 15 minutos de setup por aluno, uma conta por aluno e
uma cota diária por conta. O conteúdo da aula é contrato, idempotência, CDF, custo de re-embedding e
governança, e nada disso precisa de cluster para ser ensinado, medido ou defendido numa ficha.

A versão Databricks do mesmo conteúdo fica como material avançado, fora do horário da aula.
