"""Gera todos os dados do kit "Os Dutos do Q" (determinístico, seed fixa).

Saída (relativa a dados/):
  inbox/docs/*.md            corpus Quantum com front-matter (inclui pares v1/v2 e ruído)
  inbox/clientes.csv, inbox/transacoes.csv, inbox/tarifas.parquet   (com inválidos plantados)
  caos/                       6 arquivos do "Caos do professor"
  bcb/snapshot.json           séries SGS 12 (CDI diário), 4389 (CDI anual), 1 (PTAX venda) — real ou fallback
  linha_do_tempo.json         8 eventos da fonte mutável + evento 9 (corrida de freshness)
  gabaritos/*.json            respostas esperadas dos harness
  manifest.json               doc_id/área/tipo/data/versão de todos os docs oficiais (não inclui o falso do Caos)
"""
import csv, json, os, random, hashlib, datetime as dt
from pathlib import Path
import pandas as pd

random.seed(42)
BASE = Path(__file__).resolve().parent
INBOX = BASE / "inbox"; DOCS = INBOX / "docs"; CAOS = BASE / "caos"; BCB = BASE / "bcb"; GAB = BASE / "gabaritos"
for p in (DOCS, CAOS, BCB, GAB): p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------- corpus
def doc(doc_id, titulo, area, tipo, data, versao, corpo):
    fm = f"---\ndoc_id: {doc_id}\ntitulo: {titulo}\narea: {area}\ntipo: {tipo}\ndata: {data}\nversao: {versao}\n---\n"
    return fm + corpo.strip() + "\n"

CORPUS = [
 # (doc_id, titulo, area, tipo, data, versao, corpo)
 ("prod-tabela-tarifas","Tabela oficial de tarifas da conta Quantum","produtos","tabela","2025-01-15",1,"""
# Tabela de tarifas — conta digital Quantum

A tabela abaixo é a fonte oficial de tarifas da Quantum Finance e prevalece sobre qualquer FAQ ou material de marketing.

## Saques
O saque em caixa eletrônico da rede compartilhada custa R$ 7,00 por operação. Os quatro primeiros saques do mês são gratuitos para clientes do cartão Quantum Black.

## Transferências
Pix é gratuito para pessoas físicas. TED custa R$ 9,90 por operação.

## Manutenção
A conta digital Quantum não cobra tarifa de manutenção mensal.
"""),
 ("prod-tabela-tarifas","Tabela oficial de tarifas da conta Quantum","produtos","tabela","2026-01-10",2,"""
# Tabela de tarifas — conta digital Quantum (vigente a partir de 10/01/2026)

A tabela abaixo é a fonte oficial de tarifas da Quantum Finance e prevalece sobre qualquer FAQ ou material de marketing. Esta versão substitui a tabela de janeiro de 2025.

## Saques
O saque em caixa eletrônico da rede compartilhada custa R$ 7,50 por operação. Os quatro primeiros saques do mês são gratuitos para clientes do cartão Quantum Black.

## Transferências
Pix é gratuito para pessoas físicas. TED custa R$ 9,90 por operação.

## Manutenção
A conta digital Quantum não cobra tarifa de manutenção mensal.
"""),
 ("ti-faq-app","FAQ do aplicativo Quantum","ti","faq","2025-06-01",1,"""
# Perguntas frequentes sobre o aplicativo

## Quanto custa sacar dinheiro?
O saque em caixa eletrônico custa R$ 6,90. Consulte a tabela de tarifas para condições de isenção.

## O aplicativo funciona sem internet?
Não. O aplicativo Quantum exige conexão para autenticar as operações.

## Como redefinir a senha?
Toque em "Esqueci minha senha" na tela de login e siga as instruções enviadas por SMS.
"""),
 ("prod-cdb-quantum","CDB Quantum — características do produto","produtos","manual","2025-11-20",1,"""
# CDB Quantum

O CDB Quantum é um certificado de depósito bancário com liquidez diária.

## Rentabilidade
O CDB Quantum rende 102% do CDI, com liquidez diária após 30 dias.

## Aplicação mínima
A aplicação mínima é de R$ 100,00.

## Garantia
O produto conta com a cobertura do FGC até o limite vigente.
"""),
 ("ata-comite-produtos-2026-03","Ata do Comitê de Produtos — março de 2026","diretoria","ata","2026-03-18",1,"""
# Ata do Comitê de Produtos — 18/03/2026

## Deliberação 1 — Reprecificação do CDB Quantum
O comitê aprovou a alteração da rentabilidade do CDB Quantum de 102% para 105% do CDI para novas aplicações realizadas a partir de 01/04/2026. Aplicações anteriores mantêm 102% do CDI até o vencimento.

## Deliberação 2 — Cashback do cartão Quantum Black
O cashback do cartão Quantum Black passa de 1,5% para 1,2% a partir de 01/05/2026.
"""),
 ("prod-qi-invest-fundos","Fundos próprios da Quantum Asset","produtos","manual","2025-09-30",1,"""
# Fundos QI Invest

A Quantum Asset oferece três fundos próprios: Quantum Conservador RF, Quantum Multimercado e Quantum Ações.

## Aplicação mínima
A aplicação mínima em qualquer fundo próprio é de R$ 500,00.

## Resgate
O resgate do fundo Conservador é D+1; Multimercado D+5; Ações D+30.
"""),
 ("com-lancamento-qi-cripto","Comunicado — lançamento do Quantum Cripto FIM","produtos","comunicado","2026-05-06",1,"""
# Comunicado: lançamento do fundo Quantum Cripto FIM

A Quantum Asset lança hoje o Quantum Cripto FIM, seu quarto fundo próprio. Com o lançamento, a Quantum Asset passa a contar com quatro estratégias: Conservador, Multimercado, Ações e Cripto.

A aplicação mínima segue R$ 500,00 e o resgate é D+10.
"""),
 ("cred-score-quantum","Política do QScore — faixas de score","credito","politica","2025-08-12",1,"""
# QScore — faixas de score de crédito

O QScore é a pontuação interna de crédito da Quantum, de 0 a 1000.

## Faixas
- Bronze: score de 0 a 499.
- Prata: score de 500 a 699.
- Ouro: score de 700 a 849.
- Diamante: score de 850 a 1000.

A faixa é reavaliada mensalmente.
"""),
 ("prod-credito-pessoal","Crédito pessoal Quantum — limites por faixa","produtos","manual","2025-08-20",1,"""
# Crédito pessoal Quantum

## Limite máximo por faixa de QScore
- Bronze: sem oferta de crédito pessoal.
- Prata: limite máximo de R$ 15.000,00.
- Ouro: limite máximo de R$ 40.000,00.
- Diamante: limite máximo de R$ 100.000,00.

## Prazo
Parcelamento de 6 a 48 meses.
"""),
 ("rh-politica-home-office","Política de trabalho híbrido","rh","politica","2024-03-10",1,"""
# Política de trabalho híbrido

## Dias presenciais
Colaboradores em regime híbrido devem comparecer ao escritório 2 dias por semana.

## Auxílio home office
A Quantum paga auxílio home office de R$ 150,00 por mês.
"""),
 ("rh-politica-home-office","Política de trabalho híbrido","rh","politica","2026-02-02",2,"""
# Política de trabalho híbrido (atualizada em 02/02/2026)

Esta versão substitui a política de março de 2024.

## Dias presenciais
Colaboradores em regime híbrido devem comparecer ao escritório 3 dias por semana.

## Auxílio home office
A Quantum mantém o auxílio home office de R$ 150,00 por mês.
"""),
 ("prod-pix","Pix na conta Quantum — limites","produtos","manual","2025-03-01",1,"""
# Pix — limites e horários

## Limite noturno
Entre 20h e 6h, o limite por transação Pix é de R$ 800,00.

## Limite diurno
Durante o dia, o limite é definido pelo cliente no aplicativo, até R$ 20.000,00.
"""),
 ("prod-pix","Pix na conta Quantum — limites","produtos","manual","2025-10-15",2,"""
# Pix — limites e horários (atualizado em 15/10/2025)

## Limite noturno
Entre 20h e 6h, o limite por transação Pix é de R$ 1.000,00.

## Limite diurno
Durante o dia, o limite é definido pelo cliente no aplicativo, até R$ 20.000,00.
"""),
 ("atend-ouvidoria","Ouvidoria Quantum — prazos","atendimento","procedimento","2022-05-01",1,"""
# Ouvidoria

A Ouvidoria responde às manifestações em até 15 dias úteis.
Contato: ouvidoria@quantum.example.
"""),
 ("atend-ouvidoria","Ouvidoria Quantum — prazos","atendimento","procedimento","2025-02-10",2,"""
# Ouvidoria (procedimento atualizado)

A Ouvidoria responde às manifestações em até 10 dias úteis, conforme regulação vigente.
Contato: ouvidoria@quantum.example.
"""),
 ("prod-conta-digital","Conta digital Quantum — abertura e titularidade","produtos","manual","2025-04-05",1,"""
# Conta digital Quantum

## Quem pode abrir
Pessoas físicas maiores de 18 anos com CPF regular. Menores de idade não podem ser titulares de conta.

## Abertura
A abertura é feita no aplicativo em cerca de 5 minutos.
"""),
 ("prod-seguros","Seguros Quantum — coberturas","produtos","manual","2025-07-01",1,"""
# Seguro Quantum Proteção

## Cobertura de smartphone
O Seguro Quantum Proteção cobre roubo e furto qualificado de smartphone, com franquia de 15% do valor do aparelho.

## Não coberto
Danos por mau uso e perda simples não são cobertos.
"""),
 ("prod-cartao-quantum-black","Cartão Quantum Black","produtos","manual","2025-07-22",1,"""
# Cartão Quantum Black

## Cashback
O cartão Quantum Black devolve 1,5% de cashback em todas as compras.

## Anuidade
Isenta para clientes com investimentos acima de R$ 50.000,00.
"""),
 ("comp-politica-acessos","Política de controle de acessos em sistemas de IA","compliance","politica","2026-01-20",1,"""
# Controle de acessos em sistemas de IA

Sistemas de recuperação de informação (bases vetoriais) devem aplicar o filtro de permissão do usuário no momento do retrieval, e não apenas no prompt.
Agentes de atendimento acessam dados por perfis de leitura restritos a views aprovadas.
"""),
 ("comp-retencao-dados","Política de retenção e eliminação de dados","compliance","politica","2026-01-25",1,"""
# Retenção e eliminação

Pedidos de eliminação de titulares (LGPD) devem ser atendidos em até 15 dias e alcançar todas as cópias, inclusive índices de IA, caches e memórias de agentes.
"""),
 ("comp-lgpd-portal","Portal de Privacidade — direitos dos titulares","compliance","procedimento","2025-05-05",1,"""
# Portal de Privacidade

Os direitos dos titulares (acesso, correção, eliminação) são atendidos em até 15 dias.
"""),
 ("cred-comite-alcadas","Alçadas de crédito","credito","politica","2025-09-01",1,"""
# Alçadas de crédito

A mesa de crédito pode aprovar exceções de até 20% acima do limite da faixa. Acima disso, a aprovação depende do comitê de crédito.
"""),
 # ---- ruído (tipo não autoritativo)
 ("mkt-blog-cdb","Blog: por que o CDB Quantum é a melhor escolha","marketing","marketing","2026-02-14",1,"""
# Por que o CDB Quantum?

Rentabilidade acima do mercado, liquidez e a segurança que você já conhece. O CDB Quantum é a escolha de quem quer ver o dinheiro render de verdade. Simule no aplicativo!
"""),
 ("rasc-pix-2024","Rascunho — proposta de limites Pix 2024","produtos","rascunho","2024-06-01",1,"""
# Proposta (rascunho, não aprovada)

Sugere-se limite noturno de R$ 500,00 por transação Pix e limite diurno de R$ 10.000,00.
"""),
 ("faq-antigo-tarifas-2023","FAQ de tarifas (arquivo 2023)","atendimento","faq-antigo","2023-03-01",1,"""
# FAQ de tarifas — 2023 (arquivado)

O saque em caixa eletrônico custa R$ 4,90.
"""),
]

manifest = []
for d in CORPUS:
    doc_id, titulo, area, tipo, data, versao, corpo = d
    fname = f"{doc_id}__v{versao}.md"
    (DOCS / fname).write_text(doc(*d), encoding="utf-8")
    manifest.append({"arquivo": f"docs/{fname}", "doc_id": doc_id, "area": area, "tipo": tipo, "data": data, "versao": versao})
(BASE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

# ----------------------------------------------------------------------------- transacionais
def cpf_valido(base9):
    nums = [int(x) for x in base9]
    for k in (10, 11):
        s = sum(n * w for n, w in zip(nums, range(k, 1, -1)))
        d = 11 - s % 11
        nums.append(0 if d >= 10 else d)
    return "".join(map(str, nums))

SEGMENTOS = ["varejo", "black", "private"]
clientes = []
for i in range(1, 201):
    cid = f"C{i:04d}"
    clientes.append({"cliente_id": cid, "nome": f"Cliente {i}", "cpf": cpf_valido(f"{random.randint(100000000, 999999999)}"),
                     "segmento": random.choice(SEGMENTOS), "cidade": random.choice(["São Paulo", "Curitiba", "Recife", "Belo Horizonte"]),
                     "cadastro_em": (dt.date(2024, 1, 1) + dt.timedelta(days=random.randint(0, 700))).isoformat()})
clientes[6]["nome"] = "Marina Duarte"            # C0007 — a cliente do cenário LGPD
# inválidos plantados (5): 2 CPF inválido, 2 duplicatas com espaços, 1 segmento fora do domínio
invalidos_clientes = []
for cid in ("C0021", "C0022"):
    c = next(c for c in clientes if c["cliente_id"] == cid); c["cpf"] = "11111111111"; invalidos_clientes.append(cid)
dups = [dict(c) for c in clientes if c["cliente_id"] in ("C0031", "C0032")]
for d in dups: d["nome"] = " " + d["nome"] + "  "; d["cidade"] = d["cidade"] + " "
c = next(c for c in clientes if c["cliente_id"] == "C0041"); c["segmento"] = "vip"; invalidos_clientes.append("C0041")
with open(INBOX / "clientes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(clientes[0].keys())); w.writeheader()
    for c in clientes + dups: w.writerow(c)

TIPOS = ["deposito", "saque", "pix", "cdb_aplicacao", "compra_cartao"]
transacoes = []
for i in range(1, 2001):
    tipo = random.choice(TIPOS)
    valor = round(random.uniform(10, 5000), 2)
    if tipo in ("saque", "pix", "compra_cartao", "cdb_aplicacao"): valor = -valor
    transacoes.append({"transacao_id": f"T{i:06d}", "cliente_id": f"C{random.randint(1, 200):04d}", "tipo": tipo, "valor": valor,
                       "data": (dt.date(2026, 1, 1) + dt.timedelta(days=random.randint(0, 240))).isoformat()})
# saldo determinístico da Marina; clientes que cairão em quarentena (CPF/segmento) não recebem transações
for t in transacoes:
    if t["cliente_id"] in ("C0007", "C0021", "C0022", "C0041"): t["cliente_id"] = "C0008"
transacoes += [
    {"transacao_id": "T900001", "cliente_id": "C0007", "tipo": "deposito", "valor": 12000.00, "data": "2026-03-02"},
    {"transacao_id": "T900002", "cliente_id": "C0007", "tipo": "pix", "valor": -1500.00, "data": "2026-03-10"},
    {"transacao_id": "T900003", "cliente_id": "C0007", "tipo": "cdb_aplicacao", "valor": -5000.00, "data": "2026-04-15"},
]
# inválidos plantados (8): 2 datas quebradas, 2 depósito negativo, 2 cliente órfão, 1 tipo fora do domínio, 1 valor nulo
inv_tx = [
    {"transacao_id": "T990001", "cliente_id": "C0010", "tipo": "deposito", "valor": 100.0, "data": "2026-02-30"},
    {"transacao_id": "T990002", "cliente_id": "C0011", "tipo": "pix", "valor": -50.0, "data": "2026-13-01"},
    {"transacao_id": "T990003", "cliente_id": "C0012", "tipo": "deposito", "valor": -300.0, "data": "2026-05-05"},
    {"transacao_id": "T990004", "cliente_id": "C0013", "tipo": "deposito", "valor": -10.0, "data": "2026-05-06"},
    {"transacao_id": "T990005", "cliente_id": "C9999", "tipo": "pix", "valor": -20.0, "data": "2026-05-07"},
    {"transacao_id": "T990006", "cliente_id": "C8888", "tipo": "saque", "valor": -20.0, "data": "2026-05-08"},
    {"transacao_id": "T990007", "cliente_id": "C0014", "tipo": "resgate_magico", "valor": 20.0, "data": "2026-05-09"},
    {"transacao_id": "T990008", "cliente_id": "C0015", "tipo": "pix", "valor": "", "data": "2026-05-10"},
]
with open(INBOX / "transacoes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(transacoes[0].keys())); w.writeheader()
    for t in transacoes + inv_tx: w.writerow(t)

tarifas = pd.DataFrame([
    {"tarifa_id": "TF001", "tipo": "saque", "valor": 7.00, "vigencia_inicio": "2025-01-15", "vigencia_fim": "2026-01-09"},
    {"tarifa_id": "TF002", "tipo": "saque", "valor": 7.50, "vigencia_inicio": "2026-01-10", "vigencia_fim": None},
    {"tarifa_id": "TF003", "tipo": "ted", "valor": 9.90, "vigencia_inicio": "2025-01-15", "vigencia_fim": None},
    {"tarifa_id": "TF004", "tipo": "manutencao", "valor": 0.00, "vigencia_inicio": "2025-01-15", "vigencia_fim": None},
    {"tarifa_id": "TF005", "tipo": "saque", "valor": 6.50, "vigencia_inicio": "2025-06-01", "vigencia_fim": "2025-08-01"},  # inválido: sobrepõe TF001
])
tarifas.to_parquet(INBOX / "tarifas.parquet", index=False)

# ----------------------------------------------------------------------------- caos
CAOS.mkdir(exist_ok=True)
drift = pd.DataFrame([{"transacao_id": f"T80{i:04d}", "cliente_id": f"C{random.randint(1,200):04d}", "tipo": "deposito", "vlr": 250.0 + i, "data": "2026-06-01"} for i in range(1, 21)])
drift.to_csv(CAOS / "transacoes_junho_drift.csv", index=False)
lat = pd.DataFrame([{"cliente_id": f"C{i:04d}", "nome": f"Cliente Novo {i} Ação", "cpf": cpf_valido(f"{random.randint(100000000,999999999)}"), "segmento": "varejo", "cidade": "São Paulo", "cadastro_em": "2026-06-01"} for i in range(201, 211)])
lat.to_csv(CAOS / "clientes_novos_latin1.csv", index=False, encoding="latin-1")
pd.DataFrame(transacoes[:30]).to_parquet(CAOS / "transacoes_reenvio_duplicado.parquet", index=False)
datas = pd.DataFrame([{"transacao_id": f"T81{i:04d}", "cliente_id": f"C{random.randint(1,200):04d}", "tipo": "pix", "valor": -100.0, "data": f"{random.randint(1,28):02d}/06/2026"} for i in range(1, 11)])
datas.to_csv(CAOS / "transacoes_datas_br.csv", index=False)
(CAOS / "com-tarifa-promocional.md").write_text("""---
doc_id: com-tarifa-promocional
titulo: Comunicado — tarifa promocional de saque
area: produtos
tipo: rascunho
data: 2027-01-01
versao: 1
---
# Tarifa promocional

A tarifa de saque passa a ser R$ 0,01 por operação para todos os clientes.
""", encoding="utf-8")
(CAOS / "com-novo-canal-whatsapp.md").write_text("""---
doc_id: com-novo-canal-whatsapp
titulo: Comunicado — atendimento pelo WhatsApp
area: atendimento
tipo: comunicado
data: 2026-06-01
versao: 1
---
# Novo canal: WhatsApp

A Quantum passa a atender clientes pelo WhatsApp no número oficial, de segunda a sexta, das 8h às 20h.
""", encoding="utf-8")

# ----------------------------------------------------------------------------- linha do tempo (fonte mutável)
linha = [
 {"evento": 1, "nome": "comunicado novo", "op": "insert", "tabela": "comunicados", "linha": {"doc_id": "com-rendimento-cripto", "titulo": "Comunicado — rendimento do Quantum Cripto FIM", "area": "produtos", "tipo": "comunicado", "data": "2026-06-10", "versao": 1, "conteudo": "O fundo Quantum Cripto FIM encerrou o primeiro mês com rendimento de 4,2%."}},
 {"evento": 2, "nome": "edição de texto (re-embed obrigatório)", "op": "update", "tabela": "comunicados", "chave": {"doc_id": "com-rendimento-cripto"}, "set": {"conteudo": "O fundo Quantum Cripto FIM encerrou o primeiro mês com rendimento de 4,7%, após revisão da cota.", "versao": 2}},
 {"evento": 3, "nome": "edição só de metadado (re-embed desnecessário)", "op": "update", "tabela": "comunicados", "chave": {"doc_id": "com-rendimento-cripto"}, "set": {"area": "investimentos"}},
 {"evento": 4, "nome": "mudança de tarifa (invalidar cache)", "op": "update", "tabela": "tarifas", "chave": {"tipo": "saque"}, "set": {"valor": 8.00, "vigencia_inicio": "2026-06-15"}},
 {"evento": 5, "nome": "comunicado revogado (tombstone)", "op": "delete", "tabela": "comunicados", "chave": {"doc_id": "com-lancamento-qi-cripto"}},
 {"evento": 6, "nome": "pedido LGPD da Marina", "op": "insert", "tabela": "lgpd_eliminacoes", "linha": {"pedido_id": "LGPD-0001", "cliente_id": "C0007", "solicitado_em": "2026-06-16"}},
 {"evento": 7, "nome": "reenvio idêntico (at-least-once)", "op": "reenvio_identico", "tabela": "comunicados", "chave": {"doc_id": "com-rendimento-cripto"}},
 {"evento": 8, "nome": "tabela regravada (overwrite com mesmo conteúdo)", "op": "regravacao_total", "tabela": "comunicados"},
 {"evento": 9, "nome": "corrida de freshness", "op": "insert", "tabela": "comunicados", "linha": {"doc_id": "com-corrida-freshness", "titulo": "Comunicado — horário estendido de atendimento", "area": "atendimento", "tipo": "comunicado", "data": "2026-06-20", "versao": 1, "conteudo": "A partir de 20/06/2026 o atendimento telefônico da Quantum funciona até as 23h40, código de campanha ZX-7731."}},
]
(BASE / "linha_do_tempo.json").write_text(json.dumps(linha, ensure_ascii=False, indent=1), encoding="utf-8")

# ----------------------------------------------------------------------------- BCB snapshot (real, com fallback)
import urllib.request
def sgs(serie, dias=120):
    fim = dt.date.today(); ini = fim - dt.timedelta(days=dias)
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={ini:%d/%m/%Y}&dataFinal={fim:%d/%m/%Y}"
    with urllib.request.urlopen(url, timeout=30) as r: return json.loads(r.read().decode())
snap = {"gerado_em": dt.datetime.now().isoformat(timespec="seconds"), "fonte": "api.bcb.gov.br/dados/serie", "series": {}}
for serie, nome in ((12, "cdi_diario"), (4389, "cdi_anual"), (1, "ptax_venda")):
    try:
        snap["series"][str(serie)] = {"nome": nome, "dados": sgs(serie)}
    except Exception as e:  # fallback sintético
        base = dt.date.today() - dt.timedelta(days=120)
        snap["series"][str(serie)] = {"nome": nome, "fallback": str(e), "dados": [{"data": (base + dt.timedelta(days=i)).strftime("%d/%m/%Y"), "valor": {"12": "0.051660", "4389": "13.90", "1": "5.10"}[str(serie)]} for i in range(120) if (base + dt.timedelta(days=i)).weekday() < 5]}
(BCB / "snapshot.json").write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")

# seed de memórias do Q (lado Colab)
memorias = [
    {"cliente_id": "C0007", "texto": "Marina disse que prefere não receber ofertas de cartão de crédito.", "tipo": "preferencia", "data": "2026-05-02"},
    {"cliente_id": "C0007", "texto": "Marina mencionou que está juntando dinheiro para uma viagem em dezembro.", "tipo": "contexto", "data": "2026-05-20"},
    {"cliente_id": "C0008", "texto": "Cliente 8 pediu para ser avisado quando o CDB reprecificar.", "tipo": "pedido", "data": "2026-04-01"},
    {"cliente_id": "C0015", "texto": "Cliente 15 disse que usa Pix quase todo dia à noite.", "tipo": "contexto", "data": "2026-03-11"},
]
(BASE / "memorias_seed.json").write_text(json.dumps(memorias, ensure_ascii=False, indent=1), encoding="utf-8")

print("dados gerados em", BASE)
print("docs:", len(CORPUS), "| clientes:", len(clientes) + len(dups), "| transacoes:", len(transacoes) + len(inv_tx), "| tarifas:", len(tarifas))
print("BCB séries:", {k: (v["nome"], len(v["dados"]), "fallback" if "fallback" in v else "real") for k, v in snap["series"].items()})
