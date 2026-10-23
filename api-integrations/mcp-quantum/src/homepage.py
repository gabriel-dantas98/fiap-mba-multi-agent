"""Homepage do MCP Quantum (rota /): botões para instalar o servidor em cada cliente.

O token nunca sai do servidor: a pessoa cola o próprio token no campo e os
links e comandos são montados no navegador. A lista de capacidades é lida dos
módulos tools/resources/prompts, então a página acompanha o que está registrado.
"""

import html

import prompts
import resources
import tools


def _primeira_linha(funcao) -> str:
    return (funcao.__doc__ or "").strip().splitlines()[0] if funcao.__doc__ else ""


def _itens(tipo: str, pares: list[tuple[str, str]]) -> str:
    return "".join(
        f'<li><span class="tag {tipo}">{tipo}</span><code>{html.escape(nome)}</code>'
        f"<span>{html.escape(desc)}</span></li>"
        for nome, desc in pares
    )


CAPACIDADES = (
    _itens(
        "tool",
        [
            (f.__name__, _primeira_linha(f))
            for f in (
                tools.listar_produtos_por_categoria,
                tools.obter_produto,
                tools.buscar_produto_por_nome,
                tools.obter_avaliacao_produto,
            )
        ],
    )
    + _itens("resource", list(resources.DESCRICOES.items()))
    + _itens(
        "prompt",
        [
            (f.__name__, _primeira_linha(f))
            for f in (prompts.recomendar_produto, prompts.analisar_produto)
        ],
    )
)

PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCP Quantum</title>
<style>
  :root {
    --bg: #f6f5f1; --card: #ffffff; --ink: #1c1d21; --muted: #5f6470; --line: #e2e1dc;
    --accent: #f38020; --accent-ink: #ffffff; --ok: #2e7d32; --warn: #b26a00; --no: #c62828;
    --code-bg: #15171c; --code-ink: #e8e8e8;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #121316; --card: #1b1d22; --ink: #ececec; --muted: #a2a7b3; --line: #2c2f36;
      --code-bg: #0c0d10; --code-ink: #e8e8e8;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
         font: 16px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  main { max-width: 920px; margin: 0 auto; padding: 40px 16px 64px; }
  h1 { font-size: 34px; letter-spacing: -0.5px; margin: 0 0 6px; }
  h2 { font-size: 20px; margin: 36px 0 12px; }
  p.lead { color: var(--muted); margin: 0 0 20px; }
  code, pre { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 13px; }
  .url { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; background: var(--card);
         border: 1px solid var(--line); border-radius: 10px; padding: 10px 14px; }
  .url code { word-break: break-all; }
  .token { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
  .token label { font-weight: 600; display: block; margin-bottom: 6px; }
  .token input { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--line);
                 background: var(--bg); color: var(--ink); font: inherit; }
  .token small { color: var(--muted); display: block; margin-top: 6px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
  .cliente { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px;
             display: flex; flex-direction: column; gap: 10px; }
  .cliente h3 { margin: 0; font-size: 17px; display: flex; justify-content: space-between;
                align-items: flex-start; gap: 8px; }
  .selo { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px;
          padding: 2px 8px; border-radius: 999px; white-space: nowrap; flex-shrink: 0; margin-top: 3px; }
  .selo.ok { background: color-mix(in srgb, var(--ok) 15%, transparent); color: var(--ok); }
  .selo.copiar { background: color-mix(in srgb, var(--warn) 15%, transparent); color: var(--warn); }
  .selo.nao { background: color-mix(in srgb, var(--no) 15%, transparent); color: var(--no); }
  .cliente p { margin: 0; color: var(--muted); font-size: 14px; }
  .cliente pre { background: var(--code-bg); color: var(--code-ink); border-radius: 8px; padding: 10px;
                 margin: 0; white-space: pre-wrap; word-break: break-all; max-height: 160px; overflow: auto; }
  button, a.botao { appearance: none; border: 0; border-radius: 8px; padding: 10px 14px; font: inherit;
                    font-weight: 600; cursor: pointer; text-align: center; text-decoration: none;
                    background: var(--accent); color: var(--accent-ink); }
  button.secundario { background: transparent; color: var(--ink); border: 1px solid var(--line); }
  [aria-disabled="true"] { opacity: .45; pointer-events: none; }
  ol { margin: 0; padding-left: 18px; color: var(--muted); font-size: 14px; }
  ul.caps { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
  ul.caps li { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px;
               display: grid; grid-template-columns: 82px minmax(0, 1fr); gap: 2px 10px; align-items: baseline; }
  ul.caps li span:last-child { grid-column: 2; color: var(--muted); font-size: 14px; }
  .tag { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
  .tag.tool { color: #7b1fa2; } .tag.resource { color: #1a73e8; } .tag.prompt { color: #2e7d32; }
  footer { margin-top: 40px; color: var(--muted); font-size: 13px; }
  .aviso { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); background: var(--ink);
           color: var(--bg); padding: 8px 14px; border-radius: 8px; font-size: 14px; opacity: 0;
           transition: opacity .2s; pointer-events: none; }
  .aviso.on { opacity: 1; }
</style>
</head>
<body>
<main>
  <h1>MCP Quantum</h1>
  <p class="lead">Catálogo do marketplace Quantum Commerce como servidor MCP (Streamable HTTP, Bearer token).
    Escolha o seu cliente abaixo.</p>

  <div class="url"><strong>Endpoint</strong><code id="endpoint">__MCP_URL__</code>
    <button class="secundario" data-copiar="endpoint">Copiar</button></div>

  <h2>1. Cole o seu token</h2>
  <div class="token">
    <label for="token">Bearer token</label>
    <input id="token" type="password" autocomplete="off" spellcheck="false" placeholder="peça o token a quem mantém o servidor">
    <small>O token fica só neste navegador: os links e comandos são montados aqui e nada é enviado ao servidor.</small>
  </div>

  <h2>2. Instale no seu cliente</h2>
  <div class="grid">
    <section class="cliente">
      <h3>Cursor <span class="selo ok">1 clique</span></h3>
      <p>Abre o Cursor e pede confirmação para adicionar o servidor.</p>
      <a class="botao" id="link-cursor" href="#" aria-disabled="true">Instalar no Cursor</a>
    </section>

    <section class="cliente">
      <h3>VS Code <span class="selo ok">1 clique</span></h3>
      <p>Abre o VS Code (Copilot Chat em modo agente) e adiciona o servidor.</p>
      <a class="botao" id="link-vscode" href="#" aria-disabled="true">Instalar no VS Code</a>
    </section>

    <section class="cliente">
      <h3>Claude Code <span class="selo copiar">copiar comando</span></h3>
      <p>Rode no terminal:</p>
      <pre id="cmd-claude"></pre>
      <button class="secundario" data-copiar="cmd-claude" aria-disabled="true">Copiar comando</button>
    </section>

    <section class="cliente">
      <h3>Codex <span class="selo copiar">copiar comando</span></h3>
      <p>O Codex lê o token de uma variável de ambiente:</p>
      <pre id="cmd-codex"></pre>
      <button class="secundario" data-copiar="cmd-codex" aria-disabled="true">Copiar comandos</button>
    </section>

    <section class="cliente">
      <h3>Antigravity <span class="selo copiar">copiar config</span></h3>
      <p>Cole em <code>~/.gemini/config/mcp_config.json</code> (ou <code>.agents/mcp_config.json</code> no projeto):</p>
      <pre id="cfg-antigravity"></pre>
      <button class="secundario" data-copiar="cfg-antigravity" aria-disabled="true">Copiar config</button>
    </section>

    <section class="cliente">
      <h3>Claude (app e claude.ai) <span class="selo copiar">manual</span></h3>
      <ol>
        <li>Customize → Connectors → <em>Add custom connector</em>.</li>
        <li>URL: o endpoint acima. Autenticação: <em>No sign-in</em>.</li>
        <li>Em <em>Request headers</em>: <code>Authorization</code> = <code>Bearer &lt;token&gt;</code>.</li>
      </ol>
      <p>O passo de headers ainda é beta e não aparece em todas as contas. Sem ele, o conector não autentica.</p>
    </section>

    <section class="cliente">
      <h3>ChatGPT <span class="selo nao">não suportado</span></h3>
      <p>Conectores MCP do ChatGPT aceitam só OAuth ou nenhuma autenticação. Este servidor usa Bearer
        token fixo, então não dá para conectar sem implementar OAuth.</p>
    </section>
  </div>

  <h2>O que o servidor expõe</h2>
  <ul class="caps">__CAPACIDADES__</ul>

  <footer>FIAP MBA · Integration Architecture &amp; Connectors · desafio Quantum</footer>
</main>
<div class="aviso" id="aviso">Copiado</div>
<script>
(() => {
  const URL_MCP = document.getElementById("endpoint").textContent.trim();
  const NOME = "quantum";
  const campo = document.getElementById("token");
  const $ = (id) => document.getElementById(id);

  const ativar = (el, ok) => el.setAttribute("aria-disabled", ok ? "false" : "true");

  function atualizar() {
    const token = campo.value.trim();
    const auth = "Bearer " + (token || "<token>");
    const remoto = { url: URL_MCP, headers: { Authorization: auth } };

    $("link-cursor").href = "cursor://anysphere.cursor-deeplink/mcp/install?name=" + NOME +
      "&config=" + btoa(JSON.stringify(remoto));
    $("link-vscode").href = "vscode:mcp/install?" +
      encodeURIComponent(JSON.stringify({ name: NOME, type: "http", ...remoto }));

    $("cmd-claude").textContent =
      "claude mcp add --transport http " + NOME + " " + URL_MCP + " \\\\\\n  --header \\"Authorization: " + auth + "\\"";
    $("cmd-codex").textContent =
      "export QUANTUM_MCP_TOKEN=\\"" + (token || "<token>") + "\\"\\n" +
      "codex mcp add " + NOME + " --url " + URL_MCP + " --bearer-token-env-var QUANTUM_MCP_TOKEN";
    $("cfg-antigravity").textContent = JSON.stringify(
      { mcpServers: { [NOME]: { serverUrl: URL_MCP, headers: { Authorization: auth } } } }, null, 2);

    document.querySelectorAll("#link-cursor, #link-vscode, [data-copiar]:not([data-copiar=endpoint])")
      .forEach((el) => ativar(el, Boolean(token)));
  }

  function avisar(texto) {
    const a = $("aviso");
    a.textContent = texto;
    a.classList.add("on");
    setTimeout(() => a.classList.remove("on"), 1400);
  }

  document.querySelectorAll("[data-copiar]").forEach((botao) => {
    botao.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText($(botao.dataset.copiar).textContent);
        avisar("Copiado");
      } catch {
        avisar("Não deu para copiar; selecione o texto manualmente");
      }
    });
  });

  campo.addEventListener("input", atualizar);
  atualizar();
})();
</script>
</body>
</html>
"""


def renderizar(url_mcp: str) -> str:
    return PAGINA.replace("__MCP_URL__", html.escape(url_mcp)).replace(
        "__CAPACIDADES__", CAPACIDADES
    )
