# Claude Code (one-shot) -> MCP Quantum em produção

## mcp-quantum.json
{"mcpServers":{"quantum":{"type":"http","url":"https://mcp-quantum.gabsdevops.workers.dev/mcp","headers":{"Authorization":"Bearer ***"}}}}

## Comando
claude -p 'Usando somente o servidor MCP "quantum": (1) liste os produtos da categoria livro; (2) traga os dados do produto P013; (3) busque produtos com "batom" no nome; (4) qual a nota de avaliação do headset? ...' \
  --mcp-config mcp-quantum.json --strict-mcp-config --allowedTools "mcp__quantum__listar_produtos_por_categoria,mcp__quantum__obter_produto,mcp__quantum__buscar_produto_por_nome,mcp__quantum__obter_avaliacao_produto" --output-format stream-json --verbose

## Status do servidor no init
[{'name': 'quantum', 'status': 'connected', 'source': 'dynamic'}]

## Chamadas MCP feitas pelo agente
tool_use  mcp__quantum__listar_produtos_por_categoria  {"categoria": "livro"}
tool_use  mcp__quantum__obter_produto  {"produto_id": "P013"}
tool_use  mcp__quantum__buscar_produto_por_nome  {"nome": "batom"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "headset"}

## Resposta final
1. **Livros** (`listar_produtos_por_categoria`): são 6 produtos.
   - P015, Box trilogia O Reino Partido: R$ 172,84
   - P016, Romance A Casa dos Ventos: R$ 50,62
   - P017, Guia prático de horta urbana: R$ 66,51
   - P018, HQ Guardiões da Aurora volume 3: R$ 40,24
   - P019, Livro infantil O Sapo Azul: R$ 38,63
   - P020, Manual de fotografia digital: R$ 96,61
2. **P013** (`obter_produto`): Cadeira gamer ErgoMax, da categoria game. É uma cadeira reclinável com apoio lombar que aguenta até 120 kg.
   - **Preço:** média de R$ 900,39 entre 6 vendedores, variando de R$ 720,90 a R$ 1.095,03.
   - **Nota:** 3,81, com 11 avaliações.
   - **Reclamações:** a mais comum é produto falsificado (4).
3. **"batom"** (`buscar_produto_por_nome`): só um resultado, o P023, Batom matte vermelho cereja (maquiagem), por R$ 37,70.
4. **Nota do headset** (`obter_avaliacao_produto`): o Headset gamer HX-70 (P010) tem nota média **3,54 de 5**, com 13 avaliações. As notas vão de 2,5 a 4,9. As reclamações mais comuns são devolução/ressarcimento (3) e artigo proibido (3).


# Claude Code (one-shot) usando o PROMPT MCP como slash command

## Comando
claude -p "/mcp__quantum__analisar_produto P027" --mcp-config mcp-quantum.json --strict-mcp-config --allowedTools "..."

## Chamadas MCP feitas pelo agente
tool_use  mcp__quantum__obter_produto  {"produto_id": "P027"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P027"}
tool_use  mcp__quantum__listar_produtos_por_categoria  {"categoria": "outros"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P028"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P029"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P030"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P031"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P032"}
tool_use  mcp__quantum__obter_avaliacao_produto  {"produto": "P033"}

## Resposta final
# Análise do produto P027: Escada de alumínio 5 degraus

**Categoria:** outros · **Descrição:** escada dobrável de alumínio, aguenta até 120 kg · **7 vendedores**, um deles loja oficial (Casa & Cia Oficial)

## Pontos fortes
- **Melhor nota da categoria:** 4,29 de 5, com 11 avaliações. É também o produto com mais avaliações entre os 7, então a nota é a menos frágil do grupo.
- **Avaliação mínima de 3,0:** nenhum comprador deu nota abaixo disso. Nos outros produtos da categoria a nota mais baixa fica entre 2,5 e 2,9.
- **Muitas ofertas:** são 7 vendedores e uma loja oficial, o que dá espaço para negociar preço e escolher um vendedor mais seguro.

## Pontos de atenção
Reclamações por classe (11 no total):

| Classe | Qtd. |
|---|---|
| artigo_proibido | 3 |
| entrega | 3 |
| fraude_vendedor | 2 |
| falsificado | 1 |
| devolucao_ressarcimento | 1 |
| divergente_defeito | 1 |

- **Problemas com vendedores:** 2 casos de fraude e 1 de produto falsificado. Isso aponta para vendedores ruins entre os 7, não para defeito no produto.
- **"artigo_proibido" (3):** uma escada de alumínio não deveria ser item proibido. Pode ser erro de classificação ou anúncios irregulares de algum vendedor. Vale investigar.
- **Entrega (3):** é um item grande e dobrável, então problemas logísticos são esperados.
- **Preço varia muito entre vendedores:** de R$ 162,11 a R$ 265,90, uma diferença de cerca de 64%.
- Na categoria inteira, o número de reclamações é igual ao de avaliações em todos os produtos (11/11 no P027, 8/8 no P030 etc.). Por isso, a contagem de reclamações não diferencia o P027 dos outros. O que importa é o tipo de reclamação.

## Posição na categoria

| ID | Produto | Preço médio | Nota |
|---|---|---|---|
| **P027** | **Escada de alumínio** | **R$ 208,99** | **4,29** |
| P028 | Cafeteira elétrica | R$ 144,58 | 4,04 |
| P031 | Mochila executiva | R$ 172,71 | 3,52 |
| P029 | Panela de pressão | R$ 106,71 | 3,47 |
| P030 | Luminária articulada | R$ 95,84 | 3,58 |
| P032 | Garrafa térmica | R$ 93,88 | 2,80 |
| P033 | Suporte veicular | R$ 52,84 | 3,50 |

- **Preço:** é o mais caro da categoria (1º de 7), cerca de 67% acima da média de R$ 125,08.
- **Nota:** é a mais alta (1º de 7), cerca de 0,7 ponto acima da média de 3,60.
- **Ressalva:** "outros" junta produtos que não têm nada a ver entre si (escada, cafeteira, garrafa...). Nenhum deles substitui uma escada, então a comparação de preço mostra só a posição do produto no catálogo, não se ele está caro ou barato frente a concorrentes de verdade.

## Veredito de custo-benefício
**Bom, desde que você escolha bem o vendedor.** O produto em si é o mais bem avaliado da categoria e tem uma nota consistente. Quase todas as reclamações são sobre vendedores e entrega, não sobre a escada. O preço médio de R$ 208,99 é o mais alto da categoria, mas a diferença entre ofertas é grande.

Recomendo comprar perto do preço mínimo (~R$ 162) de um vendedor confiável, de preferência a loja oficial **Casa & Cia Oficial**, para fugir dos riscos de fraude e falsificação. Comprar pela média ou pelo teto (R$ 266) de um vendedor desconhecido piora bastante a relação custo-benefício.