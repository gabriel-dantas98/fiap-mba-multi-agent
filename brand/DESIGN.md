# Group One — Design System (System Prompt)

> Cole este documento como contexto/system prompt em qualquer IA (Claude, GPT, Gemini,
> v0, etc.) para que ela gere interfaces na identidade visual do **Group One**.
> É autossuficiente: descreve tokens, tipografia, componentes, o mascote e as regras.

---

## Identidade

**Group One** — grupo do MBA em AI Engineering & Multi-Agents (FIAP). A marca traduz
**inteligência, inovação e resultados**, no tom da "era da Inteligência Agêntica".
Estética: tecnológica, limpa, escura por padrão (navy), com acentos em azul/ciano.

## Tokens de cor

| Nome           | Hex       | Uso |
|----------------|-----------|-----|
| Azul Group One | `#0066FF` | Cor protagonista — ação, links, ênfase |
| Azul Claro     | `#33CCFF` | Acento ciano — destaques, brilho, detalhes |
| Azul Profundo  | `#0A0F1E` | Navy — fundo principal escuro, autoridade |
| Cinza Claro    | `#F2F4F7` | Fundo claro alternativo, neutralidade |
| Branco         | `#FFFFFF` | Texto sobre escuro, simplicidade |

Tons de apoio (texto sobre navy): `#9fb2d6` (dim), `#6c83ad` (mais fraco).
Linhas/bordas sobre escuro: `rgba(51,204,255,.16)`; mais fortes: `rgba(51,204,255,.32)`.

## Tipografia

- **Família única: [Sora](https://fonts.google.com/specimen/Sora)** (Google Fonts), pesos 400–800.
- Títulos/Destaques: **Sora 700–800**, `letter-spacing: -.02em`, line-height ~1.0–1.05.
- Subtítulos: Sora 600. Corpo: Sora 400, line-height ~1.5.
- Eyebrows/labels: 11–13px, `font-weight:600`, `letter-spacing:.28em`, `text-transform:uppercase`, cor ciano.

## Princípios visuais

1. **Dark-first.** Fundo navy (`#0A0F1E`); seções claras usam `#F2F4F7` com texto navy.
2. **Acento contido.** Ciano/azul para brilho e ênfase — nunca saturar a tela inteira.
3. **Respiro generoso.** Padding amplo, hierarquia clara, poucas colunas.
4. **Profundidade sutil.** Glows radiais suaves, grids pontilhados/lineares de baixa opacidade,
   `backdrop-filter: blur()` em barras fixas.
5. **Cantos arredondados.** Raio base `18px` (cards), `12px` (controles), `100px` (pills).
6. **Movimento orgânico.** Transições com `cubic-bezier(.22,.61,.36,1)`; revelações com
   stagger; sempre respeitar `prefers-reduced-motion`.

## Componentes-chave (padrões)

- **Card:** fundo `#0c1426`, borda `rgba(51,204,255,.16)`, raio 18px, barra de acento de 3px
  à esquerda com glow; hover sobe 4px + sombra.
- **Botão primário:** fundo `#0066FF`, texto branco, raio 10px; hover escurece.
  **Secundário:** fundo branco, texto azul, borda. **Pill/ghost** para ações leves.
- **Badge/pill:** fundo do acento a ~12% opacidade, texto na cor do acento, raio 100px.
- **Eyebrow:** label monoespaçado/Sora com tracinho ciano antes do texto.
- **Barra fixa:** `rgba(10,15,30,.72)` + `backdrop-filter: blur(14px)` + borda inferior fina.

## Mascote — G-One

Robô amigável: capacete branco arredondado, **visor escuro** (`#0A0F1E`), **olhos e sorriso
ciano** (`#33CCFF`), antenas com ponta dourada/azul, domo no topo. O visor é a "tela": troque
só os olhos para mudar a emoção (feliz, foco, surpresa, soneca…). Geometria limpa, escala de
favicon a outdoor. Use como avatar, ícone e ponto de calor da marca.

## Regras de uso do logo

- Logo G1 = monograma hexagonal (um "G/C" angular + um "1" com bandeira).
- Branco sobre fundos escuros/azuis; azul ou navy sobre fundos claros. Alto contraste sempre.
- Área de proteção ≥ altura do "1" em todos os lados. Não distorcer, girar ou recolorir.

## Instrução para a IA

Ao gerar qualquer interface, página ou componente para o Group One:
- Use **somente** a paleta e a tipografia Sora acima.
- Prefira layout dark-first; ofereça seções claras quando fizer sentido.
- Aplique os padrões de card/botão/badge/eyebrow descritos.
- Inclua micro-movimento sutil e acessível (respeitando `prefers-reduced-motion`).
- Mantenha o tom: tecnológico, confiante, limpo — "era da Inteligência Agêntica".
