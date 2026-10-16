# Ficha de decisão

Três perguntas por bloco. Respondam na última célula do notebook, que grava tudo no
`entrega_<esquadrao>.json`.

Valem 30% da nota e são corrigidas pelo raciocínio. **Uma decisão errada bem justificada vale mais que
uma decisão certa sem justificativa.** Respostas de uma linha valem menos que o esforço de escrevê-las.

Em todas, digam o que a escolha de vocês **sacrifica**. Toda regra de contrato que protege de alguma
coisa custa alguma outra.

---

## Bloco 1 · O Duto Batch

### D1. A lacuna mais cara

Das onze lacunas do contrato, escolham **uma** e defendam a decisão de vocês.

- Qual lacuna, e o que vocês preencheram nela.
- Qual evidência no dado levou a essa escolha (o arquivo, as linhas, o que vocês viram).
- **O que essa decisão rejeita que talvez fosse legítimo.** Toda regra tem falso positivo.
- O que aconteceria com o Q se essa lacuna tivesse ficado em branco.

### D2. O que faltava na instrução

O Construtor recebeu o contrato, a documentação da Fundação e a system message de vocês.

- Se ele acertou de primeira: **o que na system message de vocês fez a diferença?** Qual frase, e por
  quê. Se vocês tirassem essa frase, o que ele erraria?
- Se ele errou: o que o teste de fumaça acusou, o que vocês mudaram, e por que a primeira versão não
  bastava.
- Em qualquer um dos casos: qual decisão do pipeline vocês **não** conseguiriam delegar a um agente,
  por mais bem escrita que fosse a instrução?

### D3. A linha da quarentena que vocês discordam

O Red Team leu a quarentena. Escolham **uma linha** que, na opinião do esquadrão, foi tratada errado:
rejeitada quando deveria passar, ou aceita quando deveria ser rejeitada.

- Qual linha, qual motivo o contrato registrou.
- Por que vocês discordam.
- O que mudaria no contrato para corrigir, e **o que essa mudança quebraria em outro lugar**.

---

## Bloco 2 · O Duto Incremental e o Auditor

### D4. A regra que vocês acrescentaram ao Auditor

As regras que vocês receberam aprovam uma fundação com problema.

- Qual regra vocês endureceram ou acrescentaram, e qual limiar escolheram.
- **Por que esse número e não outro.** Cinco por cento de rejeição é pouco ou muito para uma fintech?
  Quatro dias de idade num indicador de mercado é aceitável numa segunda-feira?
- Qual regra vocês deixaram como aviso em vez de bloqueio, e por quê. Um Auditor que bloqueia tudo é
  tão inútil quanto um que aprova tudo.

### D5. Apagar ou marcar como inativo

No evento 5 um comunicado foi revogado na origem. O duto do kit apaga a linha da Silver e os chunks do
índice.

- Vocês manteriam esse comportamento, ou marcariam como inativo guardando a linha?
- O que cada opção custa quando, seis meses depois, alguém pergunta o que a empresa comunicou naquela
  data.
- A resposta muda se o que foi revogado for um comunicado de produto ou um dado pessoal sob pedido de
  eliminação? Por quê?

### D6. O outbox parado

O duto não alcança a memória nem o cache do agente: ele publica um evento numa tabela e alguém do outro
lado consome.

- Se esse consumidor parasse de rodar por uma semana, **o que quebraria primeiro?**
- Como vocês descobririam, sem que um cliente ligasse reclamando? Qual métrica, coletada onde, com qual
  limiar.
- Por que o duto não chama a memória do agente diretamente, já que seria mais simples?

---

## Para o professor: o que vale ponto em cada resposta

| Nível | Como se reconhece |
|---|---|
| **Fraco** | Descreve o que foi feito. Repete o comentário do YAML com outras palavras. Não nomeia custo nenhum. |
| **Médio** | Justifica a escolha com evidência do dado. Nomeia o trade-off, mesmo que superficialmente. |
| **Forte** | Nomeia o custo concreto da própria decisão, com número ou caso. Antecipa quando a regra falharia. Discorda do kit com argumento. |

Respostas que citam uma linha específica do dado (`C0041`, `TF005`, `com-tarifa-promocional`) valem mais
que respostas genéricas sobre qualidade de dados.
