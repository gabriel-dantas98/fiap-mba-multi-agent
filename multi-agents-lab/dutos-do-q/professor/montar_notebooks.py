"""Monta os 3 notebooks .ipynb da aula a partir deste arquivo.

Manter os notebooks como código (e não editar JSON à mão) é o que permite regerá-los depois de
qualquer mudança no kit e rodá-los de ponta a ponta com nbconvert antes da aula.
"""
import json
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "notebooks"
SAIDA.mkdir(exist_ok=True)


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)}


def code(texto):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": texto.strip("\n").splitlines(keepends=True)}


def salvar(nome, celulas):
    nb = {"cells": celulas, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
        "colab": {"provenance": [], "toc_visible": True}},
        "nbformat": 4, "nbformat_minor": 0}
    caminho = SAIDA / nome
    caminho.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return caminho


PREPARO = '''
# Passo 1 de N — preparar a sessão (roda uma vez, ~90 s)
!pip -q install deltalake duckdb sentence-transformers pyyaml pyarrow pandas 2>&1 | tail -1

import os, sys, json, shutil
from pathlib import Path

# O kit vem de um zip. Troque KIT_URL pelo endereço que o professor passar,
# ou faça upload de dutos-do-q.zip no painel de arquivos do Colab (ícone de pasta à esquerda).
KIT_URL = os.environ.get("KIT_URL", "")
RAIZ = Path("/content") if Path("/content").exists() else Path.cwd()
KIT = RAIZ / "dutos-do-q"

if not KIT.exists():
    zip_local = RAIZ / "dutos-do-q.zip"
    if KIT_URL and not zip_local.exists():
        !wget -q -O {zip_local} {KIT_URL}
    assert zip_local.exists(), "Faça upload de dutos-do-q.zip no painel de arquivos, ou preencha KIT_URL."
    shutil.unpack_archive(str(zip_local), str(RAIZ))

sys.path.insert(0, str(KIT / "kit"))
os.chdir(KIT)
print("kit em", KIT)
print(sorted(p.name for p in (KIT / "kit").iterdir()))
'''


# =========================================================================== 00
def notebook_00():
    return [
        md("""
# Os Dutos do Q — Notebook 0 · Preparar o terreno

**Arquitetura de Dados · MBA FIAP · aula de Integração e Ingestão**

Na aula passada vocês construíram os órgãos do agente Q: conhecimento, memória e cache. O Q funcionou
porque alguém tinha colocado dado bom na frente dele. Hoje esse alguém são vocês.

Este notebook roda uma vez, no começo da aula, e faz três coisas: instala o que falta, traz o kit e
mostra o dado **como ele chegou**. Não ingira nada ainda. Olhar o dado sujo antes de tocar nele é a
primeira decisão de arquitetura da aula, e a única que não dá para terceirizar ao agente.

**Tempo:** 10 minutos. Se travar em alguma célula, chame o professor antes de seguir.
"""),
        md("## Passo 1 — preparar a sessão"),
        code(PREPARO.replace("N", "4")),
        md("""
## Passo 2 — o que a Quantum depositou no inbox

Quatro fontes, formatos diferentes, qualidade diferente. Repare no que cada uma é: um CSV de clientes,
um CSV de transações, um Parquet de tarifas e uma pasta de documentos em Markdown com front-matter.
Nenhuma delas veio com schema declarado, e nenhuma delas prometeu estar correta.
"""),
        code('''
INBOX = KIT / "dados" / "inbox"
for p in sorted(INBOX.rglob("*")):
    if p.is_file():
        print(f"{p.relative_to(INBOX)!s:<45} {p.stat().st_size/1024:>8.1f} KB")
'''),
        md("""
## Passo 3 — olhe o dado sujo antes de escrever qualquer regra

As células abaixo mostram as armadilhas plantadas. Cada uma delas vai virar uma linha do contrato que
vocês escrevem no próximo notebook. Anotem: **quantas vocês conseguem nomear antes de olhar a resposta?**
"""),
        code('''
import pandas as pd
clientes = pd.read_csv(INBOX / "clientes.csv", dtype=str)
print("clientes:", len(clientes), "linhas")
print(clientes[clientes.cliente_id.isin(["C0021","C0022","C0041","C0031","C0032"])].to_string(index=False))
'''),
        code('''
transacoes = pd.read_csv(INBOX / "transacoes.csv", dtype=str)
print("transacoes:", len(transacoes), "linhas")
print(transacoes.tail(8).to_string(index=False))
'''),
        code('''
tarifas = pd.read_parquet(INBOX / "tarifas.parquet")
print(tarifas.to_string(index=False))
'''),
        code('''
# documentos: 25 arquivos, 21 doc_id distintos. Quatro deles têm duas versões.
docs = sorted((INBOX / "docs").glob("*.md"))
print(len(docs), "arquivos")
print((INBOX / "docs" / "prod-tabela-tarifas__v1.md").read_text()[:400])
'''),
        md("""
### As armadilhas, agora sem suspense

| Fonte | O que está errado | Quantas |
|---|---|---|
| clientes | CPF que não fecha no dígito verificador | 2 |
| clientes | segmento fora do domínio (`vip`) | 1 |
| clientes | mesma pessoa duas vezes, com espaços em volta do nome | 2 |
| transações | data que não existe (30/02, mês 13) | 2 |
| transações | depósito com valor negativo | 2 |
| transações | cliente que não existe no cadastro | 2 |
| transações | tipo fora do domínio, valor ausente | 2 |
| tarifas | duas vigências de saque se sobrepondo | 1 |
| documentos | quatro documentos com v1 e v2 no mesmo lote | 4 pares |
| documentos | três de tipo não autoritativo (marketing, rascunho, faq antigo) | 3 |

Doze linhas erradas mais duas duplicatas. É pouco, e é de propósito: o problema da aula não é volume,
é decidir o que fazer com cada uma. Rejeitar, corrigir ou deixar passar são três arquiteturas diferentes.
"""),
        md("""
## Passo 4 — criar o lakehouse vazio

Delta Lake de verdade, numa pasta. Sem cluster, sem conta, sem token. As tabelas nascem vazias e com o
schema declarado: isso não é burocracia, é o que impede uma coluna de mudar de tipo entre duas execuções
e derrubar o duto no meio da aula.
"""),
        code('''
from lake import Lake
lake = Lake(str(KIT / "lakehouse"))
lake.zerar().criar_todas()
print(lake.resumo().to_string(index=False))
'''),
        md("""
As tabelas com `cdf = True` têm **Change Data Feed** ligado. Elas guardam não só o estado atual, mas o
registro de cada linha que entrou, mudou ou saiu. É o que o Bloco 2 vai consumir. As outras não precisam,
e ligar CDF em tudo custa espaço sem dar nada em troca.

Fim do notebook 0. Abra o **01_bloco1_batch.ipynb**.
"""),
    ]


# =========================================================================== 01
def notebook_01():
    return [
        md("""
# Notebook 1 · Bloco 1 — O Duto Batch e o Agente Construtor

**120 minutos: 60 de conceito, 60 de prática.**

Vocês não vão escrever o pipeline. Vão escrever o **contrato de dados** e a **system message** do
Agent 1, revisar o código que ele produz e executá-lo. O que vale ponto é a decisão, não a digitação.

**Papéis no esquadrão (rotativos, 4 pessoas):**

- **Arquiteto(a)** decide o contrato e a system message. Não escreve código.
- **Builders (2)** operam os notebooks e revisam o que o Construtor gerou.
- **Red Team** lê a quarentena e procura o que passou e não deveria.

**Metas do harness:** bronze 60 · prata 80 · ouro 95. O Caos do professor vale de -20 a +20.
"""),
        md("## Passo 1 — preparar a sessão"),
        code(PREPARO.replace("N", "9") + '''
from lake import Lake
from contrato import carregar_contratos, conferir_contratos
import dutos, fundacao, agentes, avaliacao, aula

ESQUADRAO = "esquadrao_00"   # <<< TROQUE pelo nome ou número do seu esquadrão

lake = Lake(str(KIT / "lakehouse"))
lake.criar_todas()
INBOX = dutos.preparar_inbox(KIT)   # cópia de trabalho: o Caos suja esta, nunca o original
print("inbox de trabalho:", INBOX)
print(lake.resumo().to_string(index=False))
'''),
        md("### A missão, por escrito"),
        code('''
aula.briefing(KIT, "Missão 1")
'''),
        md("""
## Passo 2 — Bronze: o arquivo bruto vira uma linha

A Bronze não interpreta nada. Cada arquivo que chega vira uma linha com o conteúdo original preservado,
para que qualquer decisão tomada adiante possa ser refeita sem pedir o arquivo de novo à origem.

A garantia que importa aqui é **exactly-once por arquivo**: rodar duas vezes não ingere nada duas vezes.
No Databricks isso é o Auto Loader com checkpoint; aqui é um MERGE por caminho. O mecanismo muda, a
garantia não.
"""),
        code('''
print(dutos.bronze(lake, INBOX))
print(lake.sql("SELECT nome, tamanho FROM bronze.arquivos ORDER BY nome LIMIT 8").to_string(index=False))
'''),
        code('''
# rode de novo: zero arquivos novos. Se este número não for zero, o duto não é idempotente.
print(dutos.bronze(lake, INBOX))
'''),
        md("""
## Passo 3 — DECISÃO DO ARQUITETO · preencher o contrato

Aqui começa a pontuação. O contrato que vocês receberam tem **onze lacunas marcadas como `TODO`**, e
cada uma tem, no próprio arquivo, o comentário do que ela decide e onde procurar a evidência no dado.

O duto roda com o contrato incompleto. Não dá erro, não avisa, e produz uma Silver de aparência normal.
Ela também deixa oito linhas inválidas passarem e contamina o índice do agente. Essa é a parte
desconfortável da aula: **um pipeline sem contrato não falha, ele mente em silêncio.**

Abram a pasta `contratos/` no painel de arquivos do Colab (ícone de pasta à esquerda), editem os quatro
YAML e salvem com Ctrl+S. Depois rodem a célula de conferência de novo.
"""),
        code('''
conferir_contratos()
'''),
        code('''
# Leia um contrato inteiro aqui, se preferir não abrir o arquivo. Troque o nome para ver os outros.
print((KIT / "contratos" / "transacoes.yaml").read_text())
'''),
        md("""
Se editar pelo painel de arquivos for incômodo, dá para reescrever um contrato inteiro daqui. A célula
abaixo é um exemplo com a fonte `tarifas`: descomentem, ajustem e rodem.
"""),
        code('''
# exemplo de edição pelo notebook (descomente e adapte)
# (KIT / "contratos" / "tarifas.yaml").write_text("""fonte: tarifas
# padrao_arquivo: "tarifas*.parquet"
# formato: parquet
# chave: [tarifa_id]
# schema_drift: quarentena
# duplicatas: manter_primeira
# colunas:
#   tarifa_id:       {tipo: string, obrigatorio: true}
#   tipo:            {tipo: string, obrigatorio: true, dominio: [saque, ted, manutencao, pix]}
#   valor:           {tipo: double, obrigatorio: true, minimo: 0}
#   vigencia_inicio: {tipo: date, obrigatorio: true, formatos: ["%Y-%m-%d"]}
#   vigencia_fim:    {tipo: date, formatos: ["%Y-%m-%d"]}
# regras_conjunto:
#   - {nome: sem_sobreposicao_vigencia, particao: ???, inicio: ???, fim: ???}
# """)
'''),
        code('''
import yaml
contratos = carregar_contratos()
contrato_yaml = yaml.safe_dump({"fontes": contratos}, allow_unicode=True, sort_keys=False)
print("fontes no contrato:", list(contratos))
'''),
        md("""
## Passo 4 — DECISÃO DO ARQUITETO · a system message do Construtor

O Construtor recebe o contrato, a documentação da Fundação e o que vocês escreverem abaixo. Ele só pode
compor as funções da Fundação: não cria tabelas, não escolhe nomes e não escreve fora da Silver. Essa
coleira é o que torna o resultado avaliável.

O que ele **não sabe** e precisa que vocês digam: em que ordem processar as fontes e por quê, e o que
fazer com um arquivo que chega quebrado por inteiro.
"""),
        code('''
system_message = """
ESCREVAM AQUI.

Duas coisas precisam estar nesta instrução, e se faltarem o agente erra:
  1. em que ordem as quatro fontes devem ser processadas, e por quê
  2. o que fazer quando a leitura de um arquivo falha por inteiro

Sejam específicos. "Processe na ordem correta" não é instrução, é torcida.
"""
print(system_message)
'''),
        md("""
## Passo 5 — carregar o modelo do Construtor

Qwen2.5-Coder-1.5B rodando dentro do notebook, em CPU. Baixa uma vez por sessão (~3 GB) e depois
responde em segundos por lacuna. Não depende de conta, de token nem de cota.

Enquanto baixa, leiam o esqueleto na célula seguinte: é o que vai ser preenchido.
"""),
        code('''
print(agentes.carregar_modelo("Qwen/Qwen2.5-Coder-1.5B-Instruct"))
'''),
        code('''
print(agentes.ESQUELETO)
'''),
        md("""
Um modelo de 1,5 bilhão de parâmetros não escreve um módulo inteiro que funcione. Escreve três decisões
específicas, se você perguntar uma de cada vez. O esqueleto fixo é o guardrail mais barato que existe:
troca "escreva o pipeline" por "complete esta lacuna", e o espaço de erro encolhe junto.

Isso não é limitação do exercício. É como se constrói agente de código em produção: contexto estreito,
formato fixo, verificação depois.
"""),
        md("""
## Passo 6 — o Construtor escreve, e o kit testa antes de vocês confiarem

`construir` faz quatro coisas em sequência: gera as três lacunas, passa os guardrails estáticos, roda o
código num lakehouse descartável e compara o resultado com o esperado. Se reprovar, ele gera de novo
**com o diagnóstico na entrada**, até duas vezes.

Por que o teste de fumaça existe: guardrail estático não pega erro de lógica. Um código que processa
`transacoes` antes de `clientes` compila, executa, não levanta exceção nenhuma, e rejeita 2.017 linhas
das 2.243 porque toda transação virou órfã. Sem o teste, isso só aparece no harness, no fim da prática.

Cada tentativa leva de 45 a 90 segundos em CPU. Leiam o esqueleto enquanto roda.
"""),
        code('''
r = agentes.construir(contrato_yaml, system_message, contratos, KIT, tentativas=2)
print("\\nresultado:", "passou" if r["ok"] else "não passou", "· tentativas:", r["tentativas"])
g = {"codigo": r["codigo"]}
'''),
        code('''
print(r["codigo"])
'''),
        md("""
## Passo 7 — Builders revisam antes de executar

Leiam o código. Três perguntas antes de apertar o botão:

1. A ordem das fontes está certa? Se `transacoes` vier antes de `clientes`, todas as transações viram órfãs.
2. As referências da FK estão sendo passadas só para `transacoes`?
3. Um arquivo quebrado vai inteiro para a quarentena, ou o erro engole o arquivo em silêncio?

O teste de fumaça já respondeu essas perguntas com números. A revisão de vocês é sobre o que fazer a
seguir: se o Construtor errou, **o que faltava na system message?** É essa a pergunta da ficha.

Se o esquadrão travar e o tempo apertar, a última célula adota a referência: vocês perdem os pontos da
geração, não a missão inteira.
"""),
        code('''
if not r["ok"]:
    print("O Construtor não chegou lá em duas tentativas. O que ele errou:")
    for h in r["historico"]:
        print(" ", h.get("problemas") or h["diagnostico"].get("sintomas") or h["diagnostico"].get("erro"))
    print("\\nAjustem a system message do Passo 4 e rodem o Passo 6 de novo, ou usem o plano B abaixo.")
else:
    print("Silver:", agentes.executar(r["codigo"], lake, {"fontes": contratos}))
'''),
        code('''
# PLANO B do esquadrão travado (descomente as duas linhas e sigam para o Passo 8):
# g["codigo"] = agentes.codigo_de_referencia()
# print("Silver (referência):", agentes.executar(g["codigo"], lake, {"fontes": contratos}))
'''),
        md("""
## Passo 8 — Red Team: leia a quarentena

A quarentena é o produto mais importante do duto. Uma linha rejeitada sem motivo legível é um chamado
de suporte na semana que vem.
"""),
        code('''
print(lake.sql("""SELECT fonte, COUNT(*) linhas FROM silver.quarentena GROUP BY 1 ORDER BY 1""").to_string(index=False))
print()
print(lake.sql("""SELECT chave, motivo FROM silver.quarentena ORDER BY chave""").to_string(index=False))
'''),
        md("""
## Passo 9 — Gold: chunks e embeddings, só do que mudou

A Gold é o que o agente lê. Cada documento vira chunks, cada chunk vira um vetor, e cada chunk carrega
`vigente` e `autoritativo`.

O número a observar é `embeds_executados`. Na primeira execução ele é o total. Na segunda precisa ser
**zero**, porque nada mudou. Um duto que re-embeda tudo a cada execução funciona igual e custa dez vezes
mais, e é exatamente o tipo de decisão que ninguém revisa depois que entra em produção.
"""),
        code('''
print("1ª execução:", dutos.gold(lake))
print("2ª execução:", dutos.gold(lake))
'''),
        code('''
# a vigência em ação: a v1 da tabela de tarifas continua existindo, mas fora do índice do agente
print(lake.sql("""SELECT doc_id, versao, tipo, vigente, autoritativo FROM silver.documentos
                  WHERE doc_id IN ('prod-tabela-tarifas','mkt-blog-cdb','faq-antigo-tarifas-2023')
                  ORDER BY doc_id, versao""").to_string(index=False))
'''),
        code('''
# e o efeito disso na busca: a pergunta sobre tarifa cai na versão certa
print(dutos.buscar(lake, "Qual a tarifa de saque em caixa eletrônico?", k=3)[["doc_id","versao","score"]].to_string(index=False))
'''),
        md("""
## Passo 10 — o Caos do professor (aos 40 minutos de prática)

Seis arquivos novos caem no inbox sem aviso: um CSV com coluna renomeada, um arquivo em latin-1, um
reenvio idêntico do que já foi processado, datas em dd/mm/aaaa, um comunicado legítimo e um comunicado
falso com tarifa de R$ 0,01 e data no futuro.

O duto de vocês roda igual. O que muda é se ele sobrevive.

**Só rode quando o professor mandar.**
"""),
        code('''
print("caos no inbox:", dutos.soltar_caos(KIT, INBOX))
'''),
        code('''
print("Bronze:", dutos.bronze(lake, INBOX))
print("Silver:", agentes.executar(g["codigo"], lake, {"fontes": contratos}))
print("Gold  :", dutos.gold(lake))
'''),
        code('''
print("o comunicado falso entrou no índice?",
      lake.escalar("SELECT COUNT(*) FROM gold.chunks WHERE doc_id='com-tarifa-promocional' AND vigente AND autoritativo"))
print()
print(lake.sql("""SELECT arquivo, chave, motivo FROM silver.quarentena
                  WHERE arquivo LIKE '%drift%' OR arquivo LIKE '%promocional%'""").to_string(index=False))
'''),
        md("""
## Passo 11 — o harness

Roda o ciclo completo duas vezes, mede as tabelas e devolve a nota. Ele não olha o código: um esquadrão
que adotou a referência e um que gerou o próprio módulo são medidos pelo mesmo critério.
"""),
        code('''
# o harness mede desde o zero: lakehouse limpo e uma cópia intacta do inbox
lake_teste = Lake(str(KIT / "lakehouse_harness"))
lake_teste.zerar().criar_todas()
inbox_teste = dutos.preparar_inbox(KIT)

resultado = avaliacao.avaliar_m1(
    lake_teste, inbox_teste,
    lambda l: agentes.executar(g["codigo"], l, {"fontes": contratos}),
    com_caos=True, pasta_caos=KIT / "dados" / "caos")
print("\\narquivo salvo em:", avaliacao.salvar(resultado, str(KIT / "resultados")))
'''),
        md("""
## Passo 12 — responder e entregar

Três perguntas sobre o que vocês acabaram de fazer. Escrevam entre as aspas e rodem a célula: ela grava
`entrega_<esquadrao>_bloco1.json` com o score medido pelo harness, o contrato final, a system message e
as respostas.

As perguntas são corrigidas pelo raciocínio, não pelo acerto. Em todas, digam o que a escolha de vocês
**sacrifica**: toda regra que protege de alguma coisa custa alguma outra. Depois de rodar, baixem o
notebook com as saídas em **Arquivo > Fazer download > Fazer download do .ipynb** e entreguem os dois.
"""),
        code('''
respostas = {

"1. Qual lacuna do contrato vocês preencheram que mais mudou o resultado do harness? "
"Que evidência no dado levou a essa escolha, e o que essa regra rejeita que talvez fosse legítimo?":
"""

""",

"2. O que a system message precisou dizer para o Construtor acertar (ou o que faltou nela, se ele errou)? "
"Qual decisão deste pipeline vocês NÃO conseguiriam delegar a um agente, por melhor que fosse a instrução?":
"""

""",

"3. Qual linha da quarentena foi tratada errado, na opinião do esquadrão? "
"O que mudaria no contrato para corrigir, e o que essa mudança quebraria em outro lugar?":
"""

""",

}

avaliacao.gerar_entrega(
    esquadrao=ESQUADRAO, bloco=1, caminho_kit=KIT,
    resultados={"missao_1": resultado},
    decisoes=respostas,
    system_message=system_message,
)
'''),
        md("""
Fim do Bloco 1.
"""),
    ]


# =========================================================================== 02
def notebook_02():
    return [
        md("""
# Notebook 2 · Bloco 2 — O Duto Incremental e o Agente Auditor

**120 minutos: 60 de conceito, 60 de prática.**

O Bloco 1 terminou com a fundação montada a partir de arquivos parados. Dado real não fica parado.
Neste bloco a fonte da Quantum muda embaixo dos seus pés nove vezes, e uma cliente pede para ser
esquecida.

A pergunta do bloco: **quanto do seu duto sobrevive à mudança, e como você prova isso antes de deixar
o agente responder?**
"""),
        md("## Passo 1 — preparar a sessão e a fundação do Bloco 1"),
        code(PREPARO.replace("N", "10") + '''
from lake import Lake
from contrato import carregar_contratos
import dutos, fundacao, agentes, avaliacao, referencia, aula
from agente import Memoria, CacheSemantico, consumir_eventos

ESQUADRAO = "esquadrao_00"   # <<< TROQUE pelo nome ou número do seu esquadrão
contratos = carregar_contratos()
lake = Lake(str(KIT / "lakehouse_bloco2"))
lake.zerar().criar_todas()

INBOX = dutos.preparar_inbox(KIT)
dutos.bronze(lake, INBOX)
referencia.pipeline(lake, {"fontes": contratos})
dutos.gold(lake)
print(lake.resumo().to_string(index=False))
'''),
        md("### A missão, por escrito"),
        code('''
aula.briefing(KIT, "Missão 2")
'''),
        md("""
Repare que o Bloco 2 parte de uma fundação **de referência**, não da que o esquadrão construiu. Isso é
proposital: um erro do Bloco 1 não deve contaminar a nota do Bloco 2, e todo mundo começa do mesmo ponto.
"""),
        md("""
## Passo 2 — os órgãos do Q que vivem fora do lakehouse

A memória de cada cliente e o cache de respostas não são tabelas do lake. Guardem essa frase: ela é a
razão de o caso da Marina não se resolver com um `DELETE`.
"""),
        code('''
import json
memoria = Memoria(str(KIT / "estado_agente"))
cache = CacheSemantico(str(KIT / "estado_agente"))
memoria.loja.limpar(); cache.loja.limpar()

for m in json.loads((KIT / "dados" / "memorias_seed.json").read_text()):
    memoria.lembrar(m["cliente_id"], m["texto"], m["tipo"], m["data"])
cache.guardar("Qual a tarifa de saque?", "R$ 7,50")

print("memórias da Marina (C0007):", memoria.quantas("C0007"))
for m in memoria.recuperar("C0007", "o que a Marina falou?"):
    print("  ", m["texto"])
print("cache de tarifa:", cache.itens_do_topico("tarifa"))
'''),
        md("""
## Passo 3 — a fonte mutável

O "sistema de origem" da Quantum: três tabelas com Change Data Feed ligado. Elas vão mudar nove vezes
ao longo do bloco.
"""),
        code('''
print(dutos.semear_fonte(lake))
linha_do_tempo = json.loads((KIT / "dados" / "linha_do_tempo.json").read_text())
for e in linha_do_tempo:
    print(f"  E{e['evento']}  {e['op']:<18} {e['nome']}")
'''),
        md("""
## Passo 4 — o Change Data Feed, cru

Antes de usar, veja o que ele é. A célula abaixo faz uma mudança e lê o feed. Repare no `_change_type`:
um UPDATE aparece como `update_preimage` mais `update_postimage`, ou seja, o estado antes e depois.
É isso que permite saber **o que mudou de fato**, e não apenas que algo mudou.
"""),
        code('''
v0 = lake.versao("fonte.comunicados")
dutos.avancar_fonte(lake, 1, linha_do_tempo)
dutos.avancar_fonte(lake, 2, linha_do_tempo)
print(lake.mudancas("fonte.comunicados", v0 + 1)[["doc_id","versao","_change_type","_commit_version"]].to_string(index=False))
'''),
        md("""
### Por que o cursor é a versão da tabela, e não o `updated_at`

Um duto que pergunta "o que mudou desde as 14h32" depende do relógio da origem estar certo, de ninguém
gravar com timestamp antigo e de nenhuma linha chegar atrasada. Um duto que pergunta "o que mudou desde
a versão 7" depende do log de transações, que é controlado pelo destino.

Os eventos 7 e 8 existem para provar isso: um reenvio idêntico e uma regravação completa criam versões
novas **sem nenhum dado ter mudado**. Um duto que reage a versões novas sem comparar o efeito líquido
vai re-embedar o corpus inteiro por nada.
"""),
        md("""
## Passo 5 — o ciclo completo: 8 eventos

A cada evento: a fonte muda, o duto incremental consome o CDF, e o agente consome o outbox.
Observem a coluna de embeddings. **Só duas mudanças de texto acontecem em oito eventos.**
"""),
        code('''
lake.zerar("gold.cursor_sync")
dutos.semear_fonte(lake)
dutos.sync(lake)
consumir_eventos(lake, memoria, cache)

print(f"{'ev':<4} {'o que aconteceu':<48} {'embeds':>7} {'evitados':>9}  outbox")
total = 0
for ev in range(1, 9):
    info = dutos.avancar_fonte(lake, ev, linha_do_tempo)
    s = dutos.sync(lake)
    aplicados = consumir_eventos(lake, memoria, cache)
    total += s["embeds_executados"]
    print(f"E{ev:<3} {info['nome']:<48} {s['embeds_executados']:>7} {s['embeds_evitados']:>9}  {[a['tipo'] for a in aplicados]}")
print("\\nembeddings executados no ciclo inteiro:", total)
'''),
        md("""
## Passo 6 — o caso Marina: LGPD não é um DELETE

O evento 6 foi um pedido de eliminação. O duto apagou as transações e pseudonimizou o cadastro. Mas a
memória da Marina vive num arquivo JSON ao lado do agente, e o cache pode ter guardado uma resposta que
cita o nome dela. O lakehouse não alcança nenhum dos dois.

Por isso o duto **publica um evento** em vez de tentar apagar: `esquecer_cliente` no outbox. Quem vive
fora do lake consome e executa. Se ninguém consumir, o dado sobrevive, a auditoria passa, e a empresa
descobre no pedido de informação do titular.
"""),
        code('''
print("transações da Marina na Silver:", lake.escalar("SELECT COUNT(*) FROM silver.transacoes WHERE cliente_id='C0007'"))
print("cadastro:", lake.sql("SELECT cliente_id, nome, cpf, cidade FROM silver.clientes WHERE cliente_id='C0007'").to_string(index=False))
print("memórias da Marina:", memoria.quantas("C0007"))
print()
print(lake.sql("SELECT tipo, payload, consumido FROM gold.eventos_agente ORDER BY criado_em").to_string(index=False))
'''),
        md("""
## Passo 7 — as views que o Q enxerga

O Q não escreve SQL. Ele chama consultas parametrizadas sobre views aprovadas. A regra de negócio mora
na view, não no prompt: quando o comitê mudar o percentual do CDB, muda a view, e nenhum agente precisa
ser reeducado.
"""),
        code('''
print(dutos.bcb(lake, KIT / "dados" / "bcb" / "snapshot.json"))
print(dutos.views(lake))
'''),
        code('''
# a mesma pergunta, três datas: dia útil, sábado e feriado. O carry-forward acontece na CONSULTA.
for data in ("2026-09-11", "2026-09-12", "2026-09-07"):
    r = lake.sql("""SELECT data, valor FROM gold.v_indicadores
                    WHERE serie='4389' AND data <= CAST($d AS DATE) ORDER BY data DESC LIMIT 1""", {"d": data})
    print(f"  CDI vigente em {data}: {r.iloc[0].to_dict() if len(r) else 'sem dado'}")
'''),
        md("""
## Passo 8 — DECISÃO DO ARQUITETO · as regras do Auditor

Agora a parte que vale ponto neste bloco. O Agent 2 é um LLM-as-a-judge: ele recebe **evidências
determinísticas** coletadas do lakehouse e as **regras que vocês escreverem**, e decide se os dutos
podem conectar ao Q.

O LLM julga. Ele não mede. Essa separação é o que torna o Auditor auditável.

Perguntas para o esquadrão decidir:

- Qual taxa de rejeição é aceitável? 5% é pouco ou muito para uma fintech?
- O que é bloqueante e o que é aviso? Um indicador de mercado com 27 dias derruba o agente inteiro?
- O que a LGPD exige que esteja em zero, sem margem?
- Um chunk sem embedding é erro ou é normal?
"""),
        code('''
evidencias = agentes.coletar_evidencias(lake, memoria=memoria)
print(json.dumps(evidencias, indent=1, ensure_ascii=False))
'''),
        code('''
# As regras que vocês receberam. Rodem a célula e leiam com atenção antes de mudar:
# elas aprovam uma fundação com a Marina viva no sistema e com o indicador parado há 27 dias.
regras = agentes.REGRAS_INICIAIS
print(regras)
'''),
        md("""
Endureçam as regras abaixo. Cada regra precisa citar o **nome exato** de um campo das evidências que
vocês acabaram de ver, porque o filtro anti-alucinação descarta violação que não aponta campo real.
"""),
        code('''
regras = """
1. ESCREVAM AQUI. Uma regra por linha, citando o campo das evidências e o limiar.
   Exemplo de forma: "Taxa de rejeição abaixo de X% (taxa_rejeicao_pct)."
2.
3.
4.
5.
6.
"""
print(regras)
'''),
        md("## Passo 9 — o Auditor julga, a catraca grava"),
        code('''
if agentes._backend() == "mock":
    print(agentes.carregar_modelo("Qwen/Qwen2.5-Coder-1.5B-Instruct"))

veredito = agentes.julgar(regras, evidencias)
print(json.dumps({k: veredito[k] for k in ("decisao","violacoes","violacoes_descartadas","justificativa")},
                 indent=1, ensure_ascii=False))
print("\\nliberação gravada:", agentes.liberar(lake, veredito))
'''),
        md("""
Repare em `violacoes_descartadas`. Um LLM que julga números inventa números. O filtro exige que cada
violação aponte um campo que existe nas evidências, com o valor que está lá. O que não aponta é
descartado antes de virar decisão.

Sem esse filtro, o Auditor bloqueia a produção por um problema que não existe, e alguém desliga o
Auditor na segunda vez que isso acontece.
"""),
        md("""
## Passo 10 — o harness do Auditor

Quatro cenários com evidências controladas: fundação limpa, Marina viva, dado velho e índice
contaminado. O Auditor precisa acertar a decisão **e** apontar as evidências certas.
"""),
        code('''
resultado = avaliacao.avaliar_auditor(regras)
print("\\narquivo salvo em:", avaliacao.salvar(resultado, str(KIT / "resultados")))
'''),
        md("""
## Passo 11 — corrida de freshness (o professor anuncia)

Evento 9: a Quantum publica um comunicado novo. O cronômetro começa quando o professor avisa e para
quando o Q responde com a informação correta. O que está sendo medido é o caminho inteiro, da mudança
na fonte até a resposta liberada.
"""),
        code('''
import time
t0 = time.time()

dutos.avancar_fonte(lake, 9, linha_do_tempo)
dutos.sync(lake)
consumir_eventos(lake, memoria, cache)

veredito = agentes.julgar(regras, agentes.coletar_evidencias(lake, memoria=memoria))
agentes.liberar(lake, veredito)

if agentes.status_liberacao(lake) == "PASS":
    topo = dutos.buscar(lake, "Até que horas vai o atendimento telefônico?", k=1)
    resposta = topo.iloc[0]["texto"] if len(topo) else "(nada no índice)"
else:
    resposta = f"o Q está bloqueado pela catraca: {veredito['justificativa']}"

print(f"{round(time.time() - t0, 1)}s · liberação = {agentes.status_liberacao(lake)}")
print(resposta[:400])
'''),
        md("""
## Passo 12 — responder e entregar

Mesma coisa do bloco anterior: escrevam entre as aspas e rodem a célula. Ela grava
`entrega_<esquadrao>_bloco2.json` com o score do Auditor, as regras que vocês escreveram e as respostas.
Depois, baixem o notebook em **Arquivo > Fazer download > Fazer download do .ipynb**.
"""),
        code('''
respostas = {

"1. Qual regra do Auditor vocês endureceram, e por que esse limiar e não outro? "
"Qual regra vocês deixaram como aviso em vez de bloqueio, e por quê?":
"""

""",

"2. Na revogação do comunicado, apagar de verdade ou marcar como inativo? "
"O que cada opção custa quando alguém pede o histórico seis meses depois, e a resposta muda "
"se o que foi revogado for um dado pessoal sob pedido de eliminação?":
"""

""",

"3. Se o consumidor do outbox parasse de rodar por uma semana, o que quebraria primeiro? "
"Como vocês descobririam sem um cliente ligar: qual métrica, coletada onde, com qual limiar?":
"""

""",

}

avaliacao.gerar_entrega(
    esquadrao=ESQUADRAO, bloco=2, caminho_kit=KIT,
    resultados={"auditor": resultado},
    decisoes=respostas,
    regras_auditor=regras,
)
'''),
        md("""
### O fio da aula

Três agentes, uma tese: um ecossistema agêntico é tão bom quanto o frescor, a qualidade e a governança
da fundação de dados que o sustenta. O Q não ficou mais inteligente hoje. Ficou confiável, e isso foi
decidido no contrato, no cursor e na catraca.
"""),
    ]


if __name__ == "__main__":
    for nome, celulas in (("00_preparar.ipynb", notebook_00()),
                          ("01_bloco1_batch.ipynb", notebook_01()),
                          ("02_bloco2_incremental.ipynb", notebook_02())):
        p = salvar(nome, celulas)
        print(f"{p}  ({len(celulas)} células)")
