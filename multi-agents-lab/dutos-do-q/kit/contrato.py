"""Motor de contrato de dados (Silver).

Entrada: bytes de um arquivo + contrato YAML. Saída: (linhas_ok: DataFrame, quarentena: DataFrame[chave, motivo, registro]).
Roda em pandas no driver — os lotes da aula são pequenos. Em produção a mesma lógica vira expectations
(Lakeflow) ou DataFrame API; o CONTRATO (yaml) é o artefato que não muda.
"""
import io, os, re, json, fnmatch, datetime as dt
from pathlib import Path
import pandas as pd
import yaml

CONTRATOS_DIR = Path(os.environ.get("CONTRATOS_DIR") or (Path(__file__).resolve().parent.parent / "contratos"))

SENTINELA = "TODO"


def _limpar(valor):
    """TODO no YAML vira None: o motor trata como regra ausente e segue, em vez de quebrar.
    É assim que um contrato incompleto produz um resultado ruim e mensurável, não um traceback."""
    if isinstance(valor, str) and valor.strip() == SENTINELA:
        return None
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_limpar(v) for v in valor]
    return valor


def carregar_contratos():
    return {p.stem: _limpar(yaml.safe_load(p.read_text(encoding="utf-8"))) for p in CONTRATOS_DIR.glob("*.yaml")}


def pendencias(contratos: dict | None = None) -> list[dict]:
    """Lista as lacunas que ainda estão como TODO, com a fonte e o caminho da chave."""
    contratos = contratos if contratos is not None else {
        p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in CONTRATOS_DIR.glob("*.yaml")}
    achados = []

    def varrer(no, caminho, fonte):
        if isinstance(no, str) and no.strip() == SENTINELA:
            achados.append({"fonte": fonte, "campo": " > ".join(caminho)})
        elif isinstance(no, dict):
            for k, v in no.items():
                varrer(v, caminho + [str(k)], fonte)
        elif isinstance(no, list):
            for i, v in enumerate(no):
                varrer(v, caminho + [f"[{i}]"], fonte)

    for fonte, c in contratos.items():
        varrer(c, [], fonte)
    return achados


def conferir_contratos():
    """Imprime o que falta preencher. É a primeira coisa a rodar depois de editar os YAML."""
    faltando = pendencias()
    if not faltando:
        print("Contrato completo: nenhuma lacuna aberta.")
        return []
    print(f"{len(faltando)} lacuna(s) ainda em TODO:\n")
    for f in faltando:
        print(f"  {f['fonte']:<12} {f['campo']}")
    print("\nO duto roda assim mesmo. Cada lacuna aberta é uma regra que não existe,")
    print("e o harness vai encontrar exatamente o que ela deixou passar.")
    return faltando

def contrato_para(nome_relativo: str, contratos: dict):
    for c in contratos.values():
        if fnmatch.fnmatch(nome_relativo, c["padrao_arquivo"]):
            return c
    return None

# ----------------------------------------------------------------- leitura
def _decodificar(b: bytes, encodings):
    for enc in encodings or ["utf-8"]:
        try:
            return b.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("contrato", b, 0, 1, f"nenhum encoding aceito: {encodings}")

def parse_frontmatter(texto: str):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not m:
        return None
    meta = {}
    for linha in m.group(1).splitlines():          # "chave: valor" simples — títulos podem conter ':'
        if ":" in linha:
            k, v = linha.split(":", 1); meta[k.strip()] = v.strip().strip('"')
    meta["conteudo"] = m.group(2).strip()
    return meta

def ler_arquivo(nome: str, conteudo: bytes, contrato: dict):
    """Devolve (DataFrame, correcoes_aplicadas: list[str]). Lança ValueError com motivo em drift/encoding."""
    fmt = contrato.get("formato", "auto")
    correcoes = []
    if fmt == "auto":
        fmt = "parquet" if nome.endswith(".parquet") else "csv"
    if fmt == "parquet":
        df = pd.read_parquet(io.BytesIO(conteudo))
    elif fmt == "csv":
        texto, enc = _decodificar(conteudo, contrato.get("encodings"))
        if enc != "utf-8":
            correcoes.append(f"encoding:{enc}")
        df = pd.read_csv(io.StringIO(texto), dtype=str, keep_default_na=False)
    elif fmt == "markdown_frontmatter":
        texto, enc = _decodificar(conteudo, contrato.get("encodings", ["utf-8"]))
        meta = parse_frontmatter(texto)
        if meta is None:
            raise ValueError("front-matter ausente")
        df = pd.DataFrame([{k: str(v) for k, v in meta.items()}])
    else:
        raise ValueError(f"formato desconhecido: {fmt}")
    return df, correcoes

# ----------------------------------------------------------------- validadores
def cpf_ok(cpf: str) -> bool:
    d = re.sub(r"\D", "", str(cpf))
    if len(d) != 11 or d == d[0] * 11:
        return False
    n = [int(x) for x in d]
    for k in (10, 11):
        s = sum(a * w for a, w in zip(n[: k - 1], range(k, 1, -1)))
        r = 11 - s % 11
        if (0 if r >= 10 else r) != n[k - 1]:
            return False
    return True

def _parse_data(v, formatos):
    if v is None or str(v).strip() == "" or str(v) == "None":
        return None, False
    for f in formatos or ["%Y-%m-%d"]:
        try:
            return dt.datetime.strptime(str(v).strip(), f).date(), f != (formatos or ["%Y-%m-%d"])[0]
        except ValueError:
            continue
    raise ValueError(f"data inválida: {v}")

def validar(df: pd.DataFrame, contrato: dict, referencias: dict | None = None):
    """Aplica correções, regras de coluna, regras de linha, FK, duplicatas e regras de conjunto.
    referencias: {'clientes': set(cliente_id), ...} para FKs.
    Retorna (ok, quarentena, correcoes_por_linha:int)."""
    cols = contrato["colunas"]
    obrig = [c for c, r in cols.items() if r.get("obrigatorio")]
    faltando = [c for c in obrig if c not in df.columns]
    if faltando:  # schema drift → arquivo inteiro
        raise ValueError(f"schema drift: colunas obrigatórias ausentes {faltando}; colunas recebidas {list(df.columns)}")
    df = df.copy()
    n_corr = 0
    if "strip_strings" in (contrato.get("correcoes") or []):
        for c in df.columns:
            if df[c].dtype == object:
                antes = df[c].astype(str)
                df[c] = antes.str.strip()
                n_corr += int((antes != df[c]).sum())
    motivos = {i: [] for i in df.index}
    tipado = {}
    hoje = dt.date.today()
    for c, r in cols.items():
        if c not in df.columns:
            tipado[c] = [None] * len(df)
            continue
        vals = []
        for i, v in df[c].items():
            sv = None if v is None or (isinstance(v, float) and pd.isna(v)) else v
            if sv is not None and str(sv).strip() in ("", "None", "nan"):
                sv = None
            if sv is None:
                if r.get("obrigatorio"):
                    motivos[i].append(f"{c}: obrigatório ausente")
                vals.append(None); continue
            try:
                t = r.get("tipo", "string")
                if t == "date":
                    sv, corrigido = _parse_data(sv, r.get("formatos"))
                    n_corr += int(corrigido)
                    if r.get("maximo") == "hoje" and sv > hoje:
                        motivos[i].append(f"{c}: data futura {sv}")
                elif t == "double":
                    sv = float(sv)
                    if "minimo" in r and sv < r["minimo"]:
                        motivos[i].append(f"{c}: abaixo do mínimo {r['minimo']}")
                elif t == "int":
                    sv = int(float(sv))
                    if "minimo" in r and sv < r["minimo"]:
                        motivos[i].append(f"{c}: abaixo do mínimo {r['minimo']}")
                else:
                    sv = str(sv)
                    if "regex" in r and not re.match(r["regex"], sv):
                        motivos[i].append(f"{c}: não casa com {r['regex']}")
                    if r.get("dominio") and sv not in r["dominio"]:
                        motivos[i].append(f"{c}: '{sv}' fora do domínio {r['dominio']}")
                    if r.get("validador") == "cpf" and not cpf_ok(sv):
                        motivos[i].append(f"{c}: CPF inválido")
                if r.get("fk") and referencias is not None:
                    ref = referencias.get(r["fk"]["tabela"], set())
                    if sv not in ref:
                        motivos[i].append(f"{c}: FK '{sv}' inexistente em {r['fk']['tabela']}")
            except Exception as e:
                motivos[i].append(f"{c}: {e}")
                sv = None
            vals.append(sv)
        tipado[c] = vals
    t = pd.DataFrame(tipado, index=df.index)
    for regra in contrato.get("regras") or []:
        try:
            mask = t.eval(regra["expr"], engine="python")
            for i in t.index[~mask.fillna(True).astype(bool)]:
                if not any(m.startswith(regra["nome"]) for m in motivos[i]):
                    motivos[i].append(f"{regra['nome']}: violada")
        except Exception as e:  # regra não avaliável nas linhas já quebradas
            pass
    # duplicatas por chave (após correção). Sem chave ou sem política declarada, nada é duplicata:
    # as cópias entram na Silver, que é o resultado de não ter decidido.
    chave = contrato.get("chave")
    politica = contrato.get("duplicatas")
    if chave and politica == "manter_primeira":
        dup = t.duplicated(subset=chave, keep="first")
        n_corr += int(dup.sum())
        for i in t.index[dup]:
            motivos[i].append("duplicata: descartada (mantida a primeira)")
    elif chave and politica == "quarentena":
        dup = t.duplicated(subset=chave, keep=False)
        for i in t.index[dup]:
            motivos[i].append("duplicata: chave repetida")
    # regras de conjunto (sobreposição de vigência)
    for rc in contrato.get("regras_conjunto") or []:
        if rc["nome"] == "sem_sobreposicao_vigencia":
            validos = t[[len(motivos[i]) == 0 for i in t.index]]
            for _, grupo in validos.groupby(rc["particao"]):
                g = grupo.sort_values(rc["inicio"])
                fim_ant, idx_ant = None, None
                for i, row in g.iterrows():
                    ini, fim = row[rc["inicio"]], row[rc["fim"]]
                    if fim_ant is not None and ini <= fim_ant:
                        motivos[i].append(f"{rc['nome']}: sobrepõe {t.loc[idx_ant, chave[0]]}")
                        continue
                    fim_ant = fim if fim is not None else dt.date(9999, 12, 31); idx_ant = i
    ok_idx = [i for i in t.index if not motivos[i]]
    q_idx = [i for i in t.index if motivos[i]]
    ok = t.loc[ok_idx].reset_index(drop=True)
    rotulo = (lambda i: "|".join(str(t.loc[i, k]) for k in chave)) if chave else (lambda i: f"linha {i}")
    quarentena = pd.DataFrame([{"chave": rotulo(i), "motivo": "; ".join(motivos[i]),
                                "registro": json.dumps({k: (str(v) if v is not None else None) for k, v in df.loc[i].to_dict().items()}, ensure_ascii=False)}
                               for i in q_idx])
    return ok, quarentena, n_corr
