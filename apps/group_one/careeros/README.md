# CareerOS — Pitch

Pitch VC do **CareerOS**: o sistema operacional da sua carreira — um currículo vivo
de impacto para quem trabalha (ou quer trabalhar) em uma empresa de tecnologia.

Entrega do **Group One** — MBA AI Engineering & Multi-Agents (FIAP).

## O que é

Deck de 17 slides em HTML estático, na identidade visual do Group One (tokens +
tipografia Sora + mascote G-One). Usa o web component `deck-stage` (copiado de
`brand/deck-stage.js`) para navegação, escala automática 1920×1080 e export PDF.

Acesse em produção: `/<group-one>/careeros/` (montado pela homepage via Railway).

## Navegação

- **← / →**, PgUp/PgDn, Espaço — navegar
- **Home / End** — primeiro / último slide
- **R** — voltar ao início
- **Imprimir → Salvar como PDF** — gera um PDF com um slide por página

## Estrutura

```
dist/
├── index.html          # o deck (17 slides) + animações (count-up, bar chart)
├── deck-stage.js       # engine de slides (cópia self-contained do brand/)
└── assets/             # logos Group One usados pelo deck
```

> Self-contained de propósito: no Railway a homepage serve apenas o `static_dir`
> do app, então os assets de marca são copiados para dentro de `dist/assets/`
> em vez de referenciar `/brand`.

## Rodar local

```bash
# a partir da raiz do monorepo
uv run uvicorn homepage.main:app --reload
# http://localhost:8000/group-one/careeros/

# ou direto, só o deck:
python3 -m http.server 8192 --directory apps/group_one/careeros/dist
```

## Fontes dos dados

Todos os números de mercado e do problema citam a fonte no próprio slide
(rodapé `⌖`). Detalhamento completo das referências em [`SOURCES.md`](./SOURCES.md).
