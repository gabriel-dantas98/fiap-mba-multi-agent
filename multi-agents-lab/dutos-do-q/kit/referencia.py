# Módulo que o Agent 1 (Construtor) precisa produzir a partir do contrato e da Fundação.
# Serve para três coisas: resposta canônica do backend mock, solução de referência da Missão 1,
# e plano B do esquadrão cujo Construtor travou (adotar custa os pontos de geração, não a missão inteira).
import fundacao

ORDEM = {"clientes": 0, "tarifas": 1, "transacoes": 2, "documentos": 3}


def pipeline(lake, contrato: dict) -> dict:
    contratos = contrato["fontes"]
    m = {"rows_in": 0, "rows_ok": 0, "rows_rejected": 0, "arquivos": 0, "corrigidos": 0, "drift": 0}
    ref = None
    for fonte in sorted(contratos, key=lambda f: ORDEM.get(f, 9)):
        c = contratos[fonte]
        for r in fundacao.arquivos_pendentes(lake, c["padrao_arquivo"]):
            m["arquivos"] += 1
            try:
                df, correcoes = fundacao.ler(r["nome"], r["conteudo"], c)
                refs = {}
                if fonte == "transacoes":
                    ref = ref if ref is not None else fundacao.referencia_clientes(lake)
                    refs = {"clientes": ref}
                ok, q, n_corr = fundacao.aplicar_contrato(df, c, refs)
                fundacao.gravar_silver(lake, fonte, ok, c["chave"], r["nome"])
                fundacao.gravar_quarentena(lake, fonte, r["nome"], q)
                fundacao.marcar_processado(lake, r["path"], fonte, "ok", len(ok), len(q))
                if fonte == "clientes" and ref is not None:
                    ref |= set(ok["cliente_id"])
                m["rows_in"] += len(df)
                m["rows_ok"] += len(ok)
                m["rows_rejected"] += len(q)
                m["corrigidos"] += n_corr + len(correcoes)
            except (ValueError, UnicodeDecodeError, KeyError) as e:
                fundacao.gravar_quarentena(lake, fonte, r["nome"], None, str(e))
                fundacao.marcar_processado(lake, r["path"], fonte, "quarentena", 0, 1)
                m["drift"] += 1
                m["rows_rejected"] += 1
    if "documentos" in contratos:
        fundacao.finalizar_documentos(lake, contratos["documentos"])
    return m
