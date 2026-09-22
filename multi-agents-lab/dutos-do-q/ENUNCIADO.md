# Os Dutos do Q

**Integração e Ingestão de Dados para Agentes · Arquitetura de Dados · MBA FIAP**
4 horas · esquadrões de 4 pessoas · dois blocos de 120 minutos

---

## O caso

Vocês conhecem a Quantum Finance da aula passada. É a fintech onde o agente Q atende clientes, e vocês
construíram os órgãos dele: o conhecimento que ele consulta, a memória do que cada cliente já disse, o
cache que evita repetir trabalho. O Q funcionou bem no laboratório.

Três meses depois, o Q está em produção e a Quantum tem um problema.

Na semana passada um cliente ligou perguntando quanto custa sacar dinheiro no caixa eletrônico. O Q
respondeu R$ 4,90. A tarifa é R$ 7,50 desde janeiro. A resposta veio de um FAQ de 2023 que alguém tinha
arquivado numa pasta e que entrou no índice junto com todo o resto.

Não foi o único caso. Um comunicado interno anunciando um fundo novo continuou sendo citado pelo Q duas
semanas depois de o lançamento ser cancelado. Uma cliente pediu para ser esquecida, o time apagou o
cadastro dela do banco, e o Q continuou lembrando o nome dela numa conversa dois dias depois.

A diretoria chamou a área de dados e fez uma pergunta que não tem resposta técnica fácil: **o agente
está errado, ou o agente está certo sobre dados errados?**

Vocês são a equipe que vai responder isso construindo a fundação de dados do Q. Não o agente. A fundação.

---

## O que vocês vão construir

Três agentes trabalhando em conjunto, e vocês são os engenheiros que os coordenam.

### Agent 1 · O Construtor

Um modelo de linguagem que **escreve o código do pipeline de dados**. Ele roda dentro do notebook de
vocês, sem API paga e sem depender de nuvem.

Vocês não escrevem o pipeline. Vocês escrevem duas coisas:

- **O contrato de dados**, em YAML. É a declaração formal do que é um dado válido nesta empresa: quais
  colunas são obrigatórias, qual o domínio de cada uma, o que é chave, o que fazer com duplicata, qual
  formato de data aceitar, o que impede uma linha de entrar.
- **A system message**, em português. É o que o agente precisa saber e que o contrato não diz: em que
  ordem processar as fontes e por quê, o que fazer quando um arquivo inteiro chega quebrado.

Com essas duas coisas, o Construtor escreve o módulo Python que constrói a camada Silver.

**Como ele funciona por dentro, e por que isso importa.** O modelo que roda no notebook tem 1,5 bilhão
de parâmetros. É pequeno. Se vocês pedirem "escreva o pipeline", ele devolve código que parece certo e
não é. Então o kit usa uma técnica chamada **geração por lacunas**: em vez de pedir o módulo inteiro,
o agente recebe um esqueleto fixo com três buracos marcados e responde uma pergunta estreita por buraco.

Isso não é um truque de sala de aula. É como se constrói agente de código em produção: contexto estreito,
formato de resposta fixo, e verificação depois. Um agente com liberdade total é um gerador de plausível.

Depois de gerar, o código passa por três filtros:

1. **Guardrails estáticos.** O kit lê o código sem executar e reprova import fora da lista permitida,
   comando destrutivo, função ausente, lacuna não preenchida.
2. **Teste de fumaça.** O código roda num lakehouse descartável e o resultado é comparado com o esperado.
3. **O harness**, no fim, que mede as tabelas.

Guardem o motivo do filtro 2, porque ele é a lição da missão: **guardrail estático não pega erro de
lógica**. Numa das versões deste kit, o Construtor gerou um código que compila, passa em todos os
guardrails, executa sem levantar uma única exceção, e rejeita 2.017 das 2.243 linhas. Ele tinha
processado as transações antes dos clientes, e cada transação virou órfã na validação da chave
estrangeira. Nada no código estava sintaticamente errado. Tudo estava semanticamente errado.

### Agent 2 · O Auditor

Um segundo modelo de linguagem que decide se os dutos podem conectar ao Q. Ele é um **LLM-as-a-judge**:
recebe evidências e regras, e devolve um veredito.

A parte que vocês precisam entender é a divisão de trabalho:

- **O kit coleta as evidências**, e essa coleta é determinística. São consultas SQL: quantas linhas
  foram rejeitadas, quantos documentos não autoritativos estão vigentes no índice, quantos pedidos de
  eliminação foram executados, há quantos dias o indicador de mercado não é atualizado. Números, não
  opiniões.
- **Vocês escrevem as regras**, em português. Qual taxa de rejeição é aceitável numa fintech. O que é
  bloqueante e o que é só um aviso. O que a LGPD exige que esteja em zero, sem margem.
- **O LLM julga**, aplicando as regras às evidências.

O LLM não mede nada. Essa separação é o que torna o Auditor auditável: as mesmas evidências e as mesmas
regras produzem a mesma decisão, e qualquer pessoa pode conferir a conta.

Mesmo assim ele inventa. Um modelo que julga números cita números que não existem. Por isso o kit aplica
um **filtro anti-alucinação**: cada violação apontada precisa referenciar um campo que existe nas
evidências, com o valor que está lá. O que não referencia é descartado antes de virar decisão.

Pensem no que acontece sem esse filtro. O Auditor bloqueia a produção por um problema inventado, alguém
investiga, não encontra nada, e na segunda vez que isso acontece o Auditor é desligado. Um agente de
governança que dá alarme falso perde a autoridade que justificava existir.

O veredito do Auditor vai para uma tabela chamada `gold.liberacao`. É uma **catraca**: o Q só responde
quando o último status é PASS.

### Agent 3 · O Q

O agente da aula passada. Chassi lacrado, ninguém mexe. Ele consome o índice e as views que vocês
construírem, e obedece à catraca.

---

## A tese da aula

Um ecossistema de agentes é tão bom quanto o frescor, a qualidade e a governança da fundação de dados
que o sustenta.

O Q não vai ficar mais inteligente hoje. Vai ficar confiável, e isso se decide no contrato, no cursor
e na catraca.

---

## Papéis no esquadrão

Quatro pessoas, papéis rotativos entre os blocos. Todos discutem, mas a caneta é de quem tem o papel.

| Papel | O que faz | O que não faz |
|---|---|---|
| **Arquiteto(a)** | Decide o contrato, a system message e as regras do Auditor. Assina a ficha. | Não escreve código nem opera o notebook. |
| **Builders (2)** | Operam o notebook, leem o código gerado, rodam o harness. | Não decidem sozinhos o que vai no contrato. |
| **Red Team** | Lê a quarentena, procura o que passou e não deveria, e o que foi rejeitado e não deveria. | Não conserta. Reporta ao Arquiteto. |

O Red Team é o papel mais subestimado da aula. Quem lê a quarentena descobre os problemas antes do
harness, e o harness só roda no fim.

---

## Missão 1 · O Duto Batch

**Bloco 1, 60 minutos de prática. Notebook `01_bloco1_batch.ipynb`.**

O lakehouse está vazio. A Quantum depositou no inbox quatro fontes com formatos e qualidades diferentes:
um CSV de clientes, um CSV de transações, um Parquet de tarifas e 25 documentos em Markdown.

O contrato de dados que vocês receberam **está incompleto**. Onze regras estão marcadas como `TODO`, e
cada uma tem um comentário dizendo o que ela deveria decidir e onde procurar a evidência no dado.

Rodar o pipeline com o contrato incompleto funciona. Ele não quebra, não dá erro, e produz uma camada
Silver com aparência normal. Ele também deixa passar oito linhas inválidas, perde a metade do pacote do
Caos e contamina o índice do agente. O placar do harness com o contrato como vocês receberam fica em
torno de **27 pontos de 100**.

### O que fazer

1. **Olhem o dado sujo antes de escrever qualquer regra.** O notebook tem células para isso. Cada
   armadilha plantada corresponde a uma lacuna do contrato.
2. **Preencham as onze lacunas** nos arquivos de `contratos/`. Cada uma é uma decisão com custo:
   aceitar latin-1 é registrar uma correção, recusar é perder dez clientes legítimos. Nenhuma das onze
   tem resposta única obviamente certa, e todas têm respostas obviamente erradas.
3. **Escrevam a system message do Construtor.** Ela vem vazia. Duas coisas precisam estar lá, e se
   faltarem o agente erra: a ordem das fontes com o motivo, e o que fazer com um arquivo quebrado por
   inteiro.
4. **Revisem o código que o agente escreveu** antes de rodar. O kit testa sozinho, mas a pergunta da
   ficha é sobre vocês: se ele errou, o que faltava na instrução?
5. **Aos 40 minutos o professor solta o Caos.** Seis arquivos novos caem no inbox sem aviso: um CSV com
   coluna renomeada, um arquivo em latin-1, um reenvio idêntico do que já foi processado, datas em
   dd/mm/aaaa, um comunicado legítimo e um comunicado falso dizendo que a tarifa de saque passou a ser
   R$ 0,01. O duto de vocês roda igual. O que muda é se ele sobrevive.

### Como o harness pontua a Missão 1

| Critério | Pontos | O que mede |
|---|---|---|
| Idempotência | 25 | rodar duas vezes não duplica dado nem refaz embedding |
| Integridade | 20 | as contagens batem com o que é dado válido |
| Qualidade | 25 | os inválidos estão na quarentena com motivo legível, e nenhum vazou |
| Retrieval | 10 | dez perguntas caem no documento certo, na versão vigente |
| Índice limpo | 10 | nada de marketing, rascunho ou FAQ arquivado como fonte de verdade |
| SQL | 10 | quatro consultas de negócio devolvem o valor correto |
| **Caos** | **-20 a +20** | o comunicado falso no índice custa 20 pontos |

Metas: **bronze 60 · prata 80 · ouro 95**.

---

## Missão 2 · O Duto Incremental e o Auditor

**Bloco 2, 60 minutos de prática. Notebook `02_bloco2_incremental.ipynb`.**

A Missão 1 terminou com a fundação montada a partir de arquivos parados. Dado real não fica parado.

Neste bloco a fonte da Quantum muda nove vezes embaixo dos seus pés, e a cliente Marina Duarte pede
eliminação dos dados dela. O duto incremental já vem pronto: ele lê o Change Data Feed das tabelas de
origem e leva só o delta até o índice. O que vocês decidem é outra coisa.

### O que fazer

1. **Entendam o Change Data Feed antes de usar.** O notebook mostra o feed cru: cada linha que entrou,
   mudou ou saiu, com o estado antes e depois. Reparem por que o cursor do duto é a **versão da tabela**
   e não o `updated_at` da origem. Os eventos 7 e 8 existem só para provar esse ponto.
2. **Acompanhem o custo.** Oito eventos acontecem e apenas duas mudanças de texto exigem um embedding
   novo. Se o número que aparecer for muito maior, o duto está pagando por trabalho que não precisava
   fazer.
3. **Analisem o caso Marina.** O pedido de eliminação alcança quatro lugares diferentes: as transações
   na Silver, o cadastro do cliente, o índice do agente e a memória, que vive num arquivo fora do
   lakehouse. Um `DELETE` resolve dois. Descubram como o duto alcança os outros dois e o que acontece
   se ninguém estiver ouvindo.
4. **Escrevam as regras do Auditor.** É aqui que está a pontuação deste bloco. As regras que vocês
   recebem são **frouxas de propósito**: elas aprovam uma fundação com a Marina viva no sistema e com o
   indicador de mercado parado há 27 dias. O harness do Auditor roda quatro cenários controlados e
   reprova regras complacentes.
5. **Corrida de freshness.** No fim do bloco o professor anuncia o evento 9: a Quantum publica um
   comunicado novo. O cronômetro começa no anúncio e para quando o Q responde com a informação correta,
   liberada pela catraca. O que está sendo medido é o caminho inteiro, da mudança na fonte até a
   resposta.

### Como o harness pontua a Missão 2

| Critério | Pontos | O que mede |
|---|---|---|
| Estado após cada evento | 40 | o duto fez a coisa certa nos oito eventos |
| Deleção propagada | 20 | a revogação e o pedido LGPD alcançaram todos os órgãos |
| Custo | 20 | quantos embeddings foram executados no ciclo |
| Freshness | 20 | o cache foi invalidado dentro do ciclo |
| **Auditor** | **100 à parte** | quatro cenários: decisão certa e evidência certa |

**Reprovação automática:** se a memória da Marina sobreviver ao pedido de eliminação, o score da Missão
2 trava em 40, por mais bem feito que esteja o resto. Não é rigor de professor. É o artigo 18 da LGPD.

---

## A entrega

Duas coisas por esquadrão, ao fim de cada bloco.

**1. O arquivo `entrega_<esquadrao>.json`**, gerado pela última célula de cada notebook. Ele carrega o
score medido pelo harness, o contrato final, a system message, as regras do Auditor e as respostas das
fichas de decisão. O score vem medido, não declarado.

**2. O notebook salvo com as saídas** (`Arquivo > Fazer download > .ipynb`), para o professor ver o
caminho que vocês percorreram, não só onde chegaram.

### As fichas de decisão

Três perguntas por bloco, respondidas na última célula do notebook. Elas valem 30% da nota, e são
corrigidas pelo raciocínio, não pelo acerto. Uma decisão errada bem justificada vale mais que uma
decisão certa sem justificativa.

As perguntas estão no arquivo `FICHA.md` e na última célula de cada notebook.

---

## Composição da nota

| Peso | O quê |
|---|---|
| 60% | harness das duas missões, mais o do Auditor |
| 30% | fichas de decisão |
| 10% | julgamento do professor: revisão do código gerado, leitura da quarentena, participação |

---

## Regras da prática

- O chassi do Q é lacrado. Não editem `kit/agente.py` nem `kit/lake.py`.
- Vocês podem editar livremente os contratos, a system message e as regras do Auditor. É o trabalho.
- Editar o harness para conseguir nota é o único jeito de zerar a atividade.
- Se o Construtor travar, existe um plano B no notebook que adota o módulo de referência. Vocês perdem
  os pontos da geração, não a missão. Usem sem culpa se o tempo apertar, e digam na ficha por que
  precisaram.
- Se a sessão do Colab morrer, reiniciem e rodem o notebook do começo. Com o lakehouse zerado o ciclo
  completo leva menos de um minuto.
