# Group One — Brand & Design System

Recursos de marca **globais e agnósticos** do monorepo. Qualquer app em `apps/` (ou a
homepage) pode reutilizar logos, tokens, componentes e o mascote a partir daqui — esta é
a fonte única da verdade da identidade visual do Group One.

> Grupo do **MBA em AI Engineering & Multi-Agents** — FIAP.

## Conteúdo

```
brand/
├── index.html          # Brandbook — guia de identidade visual (logo, cores, tipografia, mascote)
├── slides.html         # Style guide de slides (web component deck-stage)
├── components.html     # UI kit / Storybook (botões, inputs, cards, alerts, tabs…)
├── styles.css          # Tokens + estilos do brandbook
├── components.css      # Tokens + estilos do UI kit
├── app.js              # Interações do brandbook
├── components.js       # Interações do UI kit
├── deck-stage.js       # Web component do deck de slides
├── logo/               # Logos PNG (lockup + ícone × azul/navy/branco)
├── mascot/             # Mascote G-One em SVG (color / line / avatar)
└── uploads/            # Imagens de referência usadas durante a criação
```

## Tokens da marca

| Token        | Hex       | Uso |
|--------------|-----------|-----|
| Azul         | `#0066FF` | Cor protagonista — tecnologia, confiança, ação |
| Azul Claro   | `#33CCFF` | Acento — conexão, inteligência, destaques (ciano) |
| Azul Profundo| `#0A0F1E` | Navy — fundos escuros, autoridade |
| Cinza Claro  | `#F2F4F7` | Fundos claros, neutralidade |
| Branco       | `#FFFFFF` | Simplicidade, foco |

**Tipografia:** [Sora](https://fonts.google.com/specimen/Sora) (400–800).
**Mascote:** G-One — capacete arredondado, visor escuro, sorriso ciano. O visor é a "tela":
troque só os olhos para mudar a expressão.

## Como usar em um app

Como o GitHub Pages publica apenas a pasta do app, o deploy faz **staging** copiando
`brand/` ao lado do site (ver `scripts/build_pages.sh`). Em runtime, referencie por
caminho relativo a partir da raiz publicada:

```html
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<img src="brand/logo/group-one-full-white.png" alt="Group One">
```

Para CSS, copie os tokens da tabela acima para o `:root` do app (mantendo os mesmos
valores) ou linke `brand/styles.css`.

## Logos disponíveis

- `logo/group-one-full-{blue,navy,white}.png` — lockup completo
- `logo/group-one-mark-{blue,navy,white}.png` — só o ícone G1

Regra de contraste: branco sobre fundos escuros/azuis; azul ou navy sobre fundos claros.
Mantenha a área de proteção (respiro ≥ altura do "1") em todos os lados.
