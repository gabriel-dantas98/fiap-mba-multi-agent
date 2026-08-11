# Entrega Aula 01 — Grupo 01

**Disciplina:** Cloud & Cognitive Environments — FIAP MBA AI Engineering & Multi-Agents  
**Turma:** 1AIE  
**Data de entrega:** 10/08/2026

## Grupo

| # | Nome completo | GitHub | E-mail FIAP |
|---|---------------|--------|-------------|
| 1 | Daniel Isola Massari | não informado | RM373240@fiap.com.br |
| 2 | Gabriel Dantas Gomes | gabriel-dantas98 | RM371144@fiap.com.br |
| 3 | Henrique Maireno Inácio | não informado | RM370889@fiap.com.br |
| 4 | João Victor Placidio | não informado | RM373340@fiap.com.br |

## Distribuição do trabalho

| Membro | Nível assumido | Item específico |
|--------|----------------|-----------------|
| Daniel Isola Massari | N1 | Exercícios 1.1, 1.2, 1.3 e 1.4 |
| Henrique Maireno Inácio | N2 | Exercício 2.1 — arquitetura QC + diagrama |
| João Victor Placidio | N2 | Exercícios 2.2 e 2.3 — custos e migração |
| Gabriel Dantas Gomes | N3 | Exercícios 3.1, 3.2 e 3.3 — Terraform, Bicep e multi-cloud |

## Nível 1 — Respostas

### Exercício 1.1 — Modelos de serviço

| Serviço | Modelo | Justificativa |
|---------|--------|---------------|
| Gmail | SaaS | Mesma prateleira do Outlook 365 / Google Workspace: app pronta, ninguém abre SSH. Dados, identidades e config do tenant continuam seus. |
| Azure Virtual Machines | IaaS | O EC2 / Compute Engine da Microsoft. No [Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) da AWS isso é o caso-canônico de IaaS: provedor cuida da *security of the cloud* (hardware, hipervisor, rede física, datacenter); cliente fica com a *security in the cloud* — guest OS (update + patch), apps/utilities e firewall (NSG / security group). "Herda o SO e o patch" = herda a *responsabilidade*, não o patching feito pelo provedor. |
| Azure App Service (hospedar uma API) | PaaS | Primo do Elastic Beanstalk e do Cloud Run: sobe o código, some o servidor. Provedor sobe a fatia do OS/runtime; você ainda responde por código, config e IAM. |
| AWS Lambda | FaaS | Irmão do Azure Functions / Cloud Functions: unit of billing = invocação × duração × memória, não VM ociosa. Mais abstraído que PaaS clássico — host/OS somem; você ainda responde por runtime choice, cold start, concurrency, IAM da function, segredos e o código do handler. |
| Azure SQL Database | PaaS | App Service do mundo de banco: sobe o schema/query, some o patch do motor (RDS / Cloud SQL no outro lado). Infra + plataforma no provedor; dados, criptografia e permissões no cliente. SKU muda o ticket — Oracle gerenciado (ex.: Azure Database for Oracle / RDS Oracle) costuma sair bem acima de SQL Server/PostgreSQL na mesma faixa. |
| Salesforce CRM | SaaS | Mesmo jogo do Dynamics 365 / HubSpot: serviço totalmente gerenciado. Você não opera infra; paga licença/seat, acessos e add-ons. Ainda manda em quem entra e no que faz com o dado. |
| Google Kubernetes Engine (GKE) | PaaS/IaaS híbrido | Kubernetes gerenciado (AKS/EKS no mesmo jogo): o time ganha liberdade de pods, Deployments e YAML sem operar o baixo nível — control plane, etcd, upgrades do master e patch do nó de controle ficam com o provedor. Você ainda cuida de workloads, RBAC do cluster, network policies e o que roda dentro do pod. |
| Azure Blob Storage | PaaS | Pense Google Drive / OneDrive para armazenar arquivo — só que com API de objeto, lifecycle, versioning, SAS/ACL e integração com CDN/IA. Equivalente a S3/GCS: motor gerenciado (*of the cloud*); classificação, encryption e IAM (*in the cloud*) no cliente. Ver [Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) (serviços abstraídos). |
| Azure OpenAI Service | SaaS / API-as-a-Service | Bedrock e Vertex AI sem você comprar GPU: chama modelo, não opera cluster. Patch de GPU some; prompt, PII no payload e keys/Managed Identity continuam no seu lado. |

**Responsabilidade compartilhada (lente AWS, válido nos três):** a AWS formaliza o split como *Security of the Cloud* (provedor) vs *Security in the Cloud* (cliente) no [Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/). O quanto você "herda" de tarefa sobe ou desce conforme o modelo — IaaS (VM/EC2) exige quase tudo acima do hipervisor; PaaS/FaaS/serviços abstraídos (S3, DynamoDB, Blob, SQL gerenciado) empurram OS/plataforma pro provedor; SaaS deixa só dados, identidades e config. Azure e GCP desenham a mesma escada; a AWS só batizou o meme. Em qualquer modelo, **dado e identidade não saem do cliente**.

### Exercício 1.2 — Os 6 Rs

Respostas originais do grupo (não copiamos o gabarito da disciplina). Cada R ganha uma analogia com produto/serviço de founders brasileiros.

**Cenário A — Rehost (Lift & Shift).** Rastreamento de frota em servidor físico, código 2008, um mantenedor. Empurra a VM pro IaaS (EC2 / Azure VM / GCE) e ganha elasticidade sem reescrever. Analogia BR: early-stage de logísticas tipo **Loggi** / **99** — primeiro tira o box do DC, depois moderniza. Reescrever sem doc é o caminho mais caro de falhar.

**Cenário B — Retire.** ERP de RH com <5 usuários/mês. Arquiva em S3 Glacier / Blob frio / Coldline e desliga. Analogia BR: startup matando módulo interno morto (estilo **Nubank** / **Creditas** cortando produto que não puxa métrica) — migrar o que ninguém abre só gera fatura e risco.

**Cenário C — Refactor.** API de pagamentos monolítica → microserviços + K8s + eventos. Aqui o negócio *pediu* reescrita estrutural. Analogia BR: jornada de **iFood** / **Stone** saindo de monolito para domínio (pedido, antifraude, settlement) com event-driven — caro, mas o R certo quando o monolito trava o roadmap.

**Cenário D — Repurchase.** CRM interno de 15 anos; SaaS cobre ~90% com TCO menor → Salesforce / Dynamics / HubSpot. Analogia BR: founders trocando CRM caseiro por **Pipedrive** / Salesforce (comum em **QuintoAndar**, **Loft**, SaaS B2B) — compra o produto, não o fardo de manter o fork eterno.

**Cenário E — Retain.** Mainframe on-prem por exigência BACEN. Nuvem só onde a auditoria deixar. Analogia BR: core bancário tradicional vs **Nubank** cloud-native — regulação/compliance manda; Retain não é covardia, é restrição externa.

### Exercício 1.3 — SLA

Premissa: ano comercial de **8.760 horas** (`365 × 24`). Prova determinística em [`scripts/check_calcs.py`](scripts/check_calcs.py) (`python3 scripts/check_calcs.py` — `Decimal`, sem float solto).

a) Downtime anual com SLA 99,9%:

`8.760 × (1 − 0,999) = 8,76 horas/ano` (~525,6 minutos).

b) Impacto financeiro máximo:

`8,76 × R$ 50.000 = R$ 438.000/ano`.

c) Para impacto < R$ 50.000/ano:

Downtime máximo = `50.000 / 50.000 = 1 hora/ano`.

`1 / 8.760 ≈ 0,011415525114%` de downtime → disponibilidade mínima `99,988584474886%`.

Na prática, o SLA comercial que fecha a conta é **99,99%** (`8.760 × 0,0001 = 0,876 h` ≈ 52,56 min/ano; impacto = `0,876 × 50.000 = R$ 43.800`).

**Prova (saída do script, trecho SLA):**

```text
=== prova SLA 1.3 (Decimal) ===
premissa: hours_year = 365 * 24 = 8760
ok  1.3a downtime horas: 8.760
ok  1.3a downtime minutos: 525.600
ok  1.3b impacto anual: 438000.000
ok  1.3c downtime máximo: 1
ok  1.3c % downtime: 0.01141552511415525114155251142
ok  1.3c disponibilidade: 99.98858447488584474885844749
ok  1.3 99.99% horas: 0.8760
ok  1.3 99.99% minutos: 52.5600
ok  1.3 99.99% impacto: 43800.0000
=== fim prova SLA ===
```

### Exercício 1.4 — RBAC

Referência oficial: [Azure built-in roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles) (e detalhe de storage em [built-in roles — Storage](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage)). Analogias AWS/GCP só pra leitura cruzada.

| Perfil | Role Azure (built-in) | Justificativa |
|--------|----------------------|---------------|
| Agente de IA que LÊ produtos do Storage | **Storage Blob Data Reader** (`2a2b9908-6ea1-4ae2-8e65-a410df84e7d1`) | Role de *data plane*: `…/blobs/read` — lista/lê blob, não administra a conta. Espelho mental: `s3:GetObject` / `storage.objects.get`. |
| Engenheiro de dados que CARREGA catálogos | **Storage Blob Data Contributor** (`ba92f5b4-2d11-453d-a403-e96b0029c9fe`) | Read/write/delete no plano de dados; sem Owner da subscription. Espelho: `s3:PutObject` sem Account Owner. |
| Time de FinOps que VÊ custos | **Cost Management Reader** | View-only de Cost Analysis / forecast / recommendations ([Cost Management scopes](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-work-scopes)). Espelho: Cost Explorer read-only. |
| Auditor externo que LÊ a assinatura | **Reader** (escopo *subscription*) | Control plane read-only em todos os recursos da assinatura; sem mutação. Espelho: `ViewOnlyAccess` / `roles/viewer`. |
| CI/CD que provisiona via Terraform | **Contributor** no *Resource Group* + Service Principal dedicado | Sobe/altera recursos no RG; **nunca** `Owner`/`Contributor` da subscription. Espelho: role scoped na AWS account / GCP project. |

Least privilege: escopo no RG (ou no storage account), não na subscription.

## Nível 2 — Respostas + implementação

### Exercício 2.1 — Arquitetura da Quantum Commerce

**Provedor principal: AWS.** Defesa com cases reais (não "porque a disciplina é Azure"):

1. **[iFood × Bedrock/SageMaker](https://aws.amazon.com/solutions/case-studies/ifood-bedrock/)** — marketplace BR com 80M+ pedidos/mês; personalização e antifraude em 100+ modelos; PoC do garçom virtual **Garçon** (RAG + Claude/Titan no Bedrock). Prova que o caminho agentic de e-commerce conversacional já roda em produção/PoC sério na AWS LatAm.
2. **[Amazon Rufus × Bedrock](https://aws.amazon.com/blogs/machine-learning/how-rufus-scales-conversational-shopping-experiences-to-millions-of-amazon-customers-with-amazon-bedrock/)** — assistente de compra conversacional em escala; tool calling + RAG sobre catálogo/pedido. Blueprint direto pra QC.
3. **[Natura × OpenSearch + Bedrock](https://aws.amazon.com/solutions/case-studies/natura-ia-generativa/)** — busca semântica/vetorial de catálogo em produção (BR). Camada de retrieval que o agente precisa antes de gerar.
4. **[Mercado Libre × Bedrock](https://aws.amazon.com/solutions/case-studies/mercado-libre-mutt-data/)** — gen AI no catálogo/retail media (S3 + DynamoDB + Bedrock). Escala LatAm de enriquecimento de SKU.

Pacote agentic na AWS fecha sem cola: **IAM Roles + Cognito**, **Bedrock + OpenSearch Serverless**, **ECS Fargate + Lambda + SQS/SNS**, **S3 + RDS + DynamoDB**, **CloudFront + WAF**, **CloudWatch + Secrets Manager**. Azure/GCP entram como alternativa ou DR — não no caminho crítico do agente.

**Camadas (AWS):**

1. **Edge/entrega** — CloudFront + WAF + frontend estático (S3 / Amplify).
2. **APIs e processamento** — ECS Fargate (API síncrona) + SQS/SNS + Lambda (assíncrono).
3. **IA cognitiva / RAG** — Bedrock (LLM/embeddings), OpenSearch Serverless (vetorial), Comprehend/Rekognition.
4. **Dados** — RDS (transacional), DynamoDB (sessões/conversas), S3 (catálogo/imagens).
5. **Plataforma** — IAM/Cognito, Secrets Manager, CloudWatch.

Diagrama: [`diagramas/arquitetura-qc-aula01.png`](diagramas/arquitetura-qc-aula01.png) (fonte Mermaid: [`diagramas/arquitetura-qc-aula01.mmd`](diagramas/arquitetura-qc-aula01.mmd)).

| Categoria | Escolha AWS (primário) | Alternativa Azure | Alternativa GCP |
|-----------|------------------------|-------------------|-----------------|
| Compute (backend) | Amazon ECS/Fargate (+ Lambda workers) | Azure App Service / Container Apps | Cloud Run |
| Storage (catálogo, imagens) | Amazon S3 | Azure Blob Storage | Cloud Storage |
| Banco relacional | Amazon RDS | Azure SQL Database | Cloud SQL |
| Banco NoSQL | Amazon DynamoDB | Azure Cosmos DB | Firestore / Bigtable |
| Vector Database | Amazon OpenSearch Serverless / Aurora pgvector | Azure AI Search | Vertex AI Vector Search |
| Serviços de IA cognitivos | Amazon Bedrock + Comprehend/Rekognition | Azure OpenAI + AI Services | Vertex AI + Cloud Vision/Speech |
| CDN | Amazon CloudFront | Azure Front Door / CDN | Cloud CDN |
| Mensageria/Filas | Amazon SQS/SNS | Azure Service Bus | Pub/Sub |
| Observabilidade | Amazon CloudWatch | Azure Monitor | Cloud Monitoring/Logging |

### Exercício 2.2 — Comparativo de custos

**Premissas:**

- Região equivalente: Azure East US, AWS `us-east-1`, GCP `us-central1`.
- On-demand / pay-as-you-go, Linux, 730 h/mês.
- USD puro. Sem câmbio inventado.
- Fontes em 10/08/2026: Azure Retail Prices API, Bandwidth/EC2 oficiais, docs públicos GCP/AWS.
- VMs ~2 vCPU / 8 GB: Azure `Standard_B2ms`, AWS `t3.large`, GCP `e2-standard-2`.
- Banco: Azure SQL GP Gen5 2 vCore + ~100 GB; RDS `db.t3.large` MySQL + 100 GB gp3; Cloud SQL db-custom-2-8192 + 100 GB.
- Serverless: 10M execuções, 128 MB, 200 ms; free grants padrão.

| Item | Azure | AWS | GCP | Notas |
|------|-------|-----|-----|-------|
| 2 × VM (2vCPU/8GB) | ~US$ 121,47 | ~US$ 121,47 | ~US$ 98 | B2ms e t3.large empatam (~US$ 0,0832/h); e2-standard-2 ~US$ 0,067/h |
| 500 GB storage | ~US$ 10,40 | ~US$ 11,50 | ~US$ 10,00 | Blob Hot LRS ~US$ 0,0208/GB; S3 Standard US$ 0,023/GB; GCS Standard US$ 0,020/GB |
| Banco gerenciado | ~US$ 234 | ~US$ 117 | ~US$ 110 | SQL GP 2 vCore engole o Azure; RDS/Cloud SQL saem mais baratos nessa faixa |
| 10M req serverless | ~US$ 1,80 | ~US$ 1,80 | ~US$ 2,00 | Depois do free tier de 1M, duração cai no grant |
| **Total mensal** | **~US$ 368** | **~US$ 252** | **~US$ 220** | Ordem de grandeza; calculator oficial fecha o SKU |
| **Total anual** | **~US$ 4.416** | **~US$ 3.024** | **~US$ 2.640** | 12 × on-demand |

**Análise:**

a) **GCP ganhou** neste recorte; AWS no meio. O buraco Azure↔GCP (~US$ 148/mês) é quase todo SQL GP Gen5. Troca por Azure Database for PostgreSQL Flexible (burstable) e o gap encolhe de verdade, tipo trocar RDS Multi-AZ caro por instância single-AZ.

b) **RI / Savings Plans / CUDs de 1 ano** no Azure cortam compute ~30–40%. Aproxima VM, **não apaga** o premium do SQL GP. Commit no AWS/GCP com banco Azure substituído pode inverter o ranking.

c) Em projeto agentic, preço bruto sem FinOps de dados é mentira parcial. O que decide: região do modelo (Bedrock vs Azure OpenAI vs Vertex), identidade (IAM Role vs Managed Identity vs Workload Identity), vetor (OpenSearch vs AI Search vs Vertex Vector), latência pro Brasil e egress. Com a QC em **AWS**, Savings Plans + Graviton no compute e RDS right-size fecham o meio do ranking sem pagar o premium do SQL GP Azure.

### Exercício 2.3 — Estratégia de migração

Base conceitual: [Sam Newman — Monolith Decomposition Patterns](https://samnewman.io/talks/monolith-decomposition-patterns/) ([InfoQ](https://www.infoq.com/presentations/microservices-principles-patterns/), [Strangler Fig](https://samnewman.io/patterns/refactoring/strangler-fig-application/), [Branch by Abstraction](https://samnewman.io/patterns/architectural/branch-by-abstraction/)). Evitar big-bang rewrite.

a) **Workload:** monolito on-prem de e-commerce (catálogo + pedidos + busca), pico de campanha, assistente conversacional pedindo passagem — o próprio contexto QC / founders de marketplace BR.

b) **R: Replatform** no core (monolito → containers gerenciados), com **Refactor incremental** só nos bounded contexts que doem (busca + canal de IA). Custa mais que lift-and-shift puro (EC2), menos que rewrite. Prazo: semanas/meses, não anos.

   Plano com patterns do Newman:

   | Fatia | Pattern | Como na QC |
   |-------|---------|------------|
   | Pedidos / checkout (HTTP na borda) | **Strangler Fig** + **Parallel Run** | API Gateway / ALB na frente do monolito; rotas `/orders` vão pro Order Service; dual-run compara totais antes do cutover |
   | Catálogo (páginas/widgets) | **UI Composition** + Strangler | Widget de product detail/list vem do Catalog Service; resto da storefront ainda no monolito |
   | Busca / indexação interna | **Branch by Abstraction** ou **CDC** | Abstrai `SearchIndexer`; se o código for intocável, CDC na tabela `products` alimenta OpenSearch |
   | Assistente conversacional | **UI Composition** (chat widget) + **Decorating Collaborator** | Chat novo chama Bedrock/RAG; no sucesso do checkout, decorator dispara follow-up sem reescrever o monolito |

c) **Serviços AWS:** CloudFront, ECS Fargate (ou App Runner), Lambda, SQS/SNS, RDS, S3, OpenSearch Serverless, Bedrock, Cognito/IAM, Secrets Manager, CloudWatch. Dev/homolog enxuto: **US$ 250–450**/mês — RDS e tokens Bedrock mandam no ticket. Azure/GCP equivalentes na tabela do 2.1.

d) **Obstáculo real:** PII/pagamento + medo de mexer no monolito. Resposta Newman-compatível: deployment ≠ release (feature flags / dark launch), Parallel Run no pricing/checkout, PrivateLink/VPC endpoints, tokenization, catálogo primeiro via Strangler.

## Nível 3 — Bônus

### Exercício 3.1 — Terraform

Código em [`terraform/`](terraform/).

1. SSH/22 só em `${var.meu_ip}/32` (o security group / firewall rule de sempre).
2. `subnet-app` = `10.0.2.0/24` além de `subnet-vm` = `10.0.1.0/24`.
3. Output único `public_ip_address`.
4. Mudar `meu_ip` atualiza **só** o NSG; VM fora do plano.

**Azure for Students:** policy matou `eastus2`; `eastus` sem capacidade de `Standard_B2s`. Saiu `chilecentral` + `Standard_B2als_v2` + Ubuntu 24.04. Quotas mentem; capacidade decide.

**Validação:**

- destroy → 9 recursos fora; RG sumiu.
- plan/apply limpos → 9 criados.
- SSH + Nginx (`scripts/validate-nginx.sh`) → HTTP 200 na página Group One.
- plan final → `No changes`.

Print: [`evidencias/nginx-group-one.png`](evidencias/nginx-group-one.png). Evidências: [`evidencias/provisionamento.md`](evidencias/provisionamento.md).

### Exercício 3.2 — Bicep equivalente

Código em [`bicep/main.bicep`](bicep/main.bicep).

Mesma stack do Terraform: VNet, `subnet-vm`, `subnet-app`, NSG com SSH restrito, Public IP, NIC, Ubuntu 24.04 (`Standard_B2als_v2` / `chilecentral`). Deploy em RG pré-criado (padrão Students).

| Artefato | Linhas | Observação |
|----------|--------|------------|
| ARM gerado (`bicep build` → `main.json`) | 237 | JSON verboso exportado do Bicep |
| Terraform (`main.tf`+`variables.tf`+`outputs.tf`+`versions.tf`) | 216 | HCL; mesmo papel do CloudFormation / Deployment Manager multi-cloud |
| Bicep `main.bicep` | 191 | DSL nativa Azure; o CDK/CFN "curto" da Microsoft |

**Legibilidade:** Bicep ganha se o time só vive em Azure (tipo CloudFormation puro na AWS). Terraform ganha quando o segundo provedor aparece ou o state remoto já é padrão do time.

**Quando Bicep?** Só Azure, `az` no sangue, zero vontade de provider HashiCorp. Fora disso, Terraform (ou Pulumi se o time quer TypeScript de verdade).

Docs: [`bicep/README.md`](bicep/README.md). Evidências: [`evidencias/bicep.md`](evidencias/bicep.md).

10/08/2026: deploy `Succeeded`, VM `vm-cc-aula01-bicep` running, SSH Ubuntu 24.04 ok, subnets ok, RG apagado.

### Exercício 3.3 — Multi-cloud para a Quantum Commerce

Diagrama: [`diagramas/arquitetura-qc-multicloud.png`](diagramas/arquitetura-qc-multicloud.png).

a) **AWS + Azure:**

- **AWS (primário — agente):** CloudFront, ECS/Lambda, Bedrock, OpenSearch, RDS/DynamoDB, S3, IAM/Cognito (ver cases iFood/Rufus/Natura no 2.1).
- **Azure (secundário — analytics/DR):** Blob espelho / backup, Front Door em região secundária, SQL/Blob pra failover frio.
- Por quê essa divisão: caminho do agente fica num provedor (menos hop de identidade). DR e espelho frio vão pro segundo cloud sem colocar latência no p95 do chat. GCP entraria se o ganho fosse BigQuery/Vertex, não neste recorte.

b) **Desafios:**

1. Latência cross-cloud sobe o p95 do assistente.
2. Identidade: Cognito/IAM ↔ Entra ID via OIDC (sem isso vira senha espalhada).
3. Egress de 10 TB/mês (conta abaixo).
4. Trace único: CloudWatch ↔ Azure Monitor (ou OpenTelemetry no meio).

c) **Terraform vs Pulumi:**

| | Terraform | Pulumi |
|--|-----------|--------|
| Linguagem | HCL | TypeScript/Python/Go/C# |
| Pricing | OSS + HCP pago | OSS + Pulumi Cloud pago |
| Suporte 3 grandes | Providers oficiais maduros | Providers + bridges |
| Quando escolher | Plan/state que o mercado já fala | Time que já testa em TS/Python e odeia HCL |

d) **Egress 10 TB/mês Azure Brazil South → AWS us-east-1** (Internet):

Fonte: [Azure Bandwidth](https://azure.microsoft.com/pricing/details/bandwidth/) — Premium Global Network, South America.

- Free: 100 GB
- Billable: `10.000 − 100 = 9.900 GB`
- Tarifa: **US$ 0,181 / GB**
- **≈ 9.900 × 0,181 = US$ 1.791,90 / mês**

Routing Preference (ISP): **US$ 0,12 / GB** → **≈ US$ 1.188 / mês**.

AWS DTO us-east-1 (~US$ 0,09/GB após 100 GB free): ~US$ 891. Ainda dói; dói menos que sair do Brazil South no Premium Network. GCP egress intercontinental na mesma ordem: o problema não é "Azure caro", é "dado atravessando oceano".

**Azure Arc / AWS Outposts:** Arc = governança Azure em VM/cluster fora da Azure (tipo Anthos no GCP, mas do lado Microsoft). Outposts = rack AWS no DC. Na QC (AWS-first), Outposts só se loja/DC exigir locality; Arc só se o DR Azure precisar de policy unificada.

## Reflexão coletiva

Cloud sem IaC não se reproduz. Mudar o NSG e ver o `plan` sem recriar a VM foi o momento "ok, isso serve em produção": mudança cirúrgica, auditável. No Azure for Students, policy e capacidade pesaram mais que elegância de HCL. Acontece igual com AZ esgotada na AWS ou quota de GPU no GCP.

Agente com least privilege (`Storage Blob Data Reader` no exercício Azure; na QC AWS vira IAM role só com `s3:GetObject`) + Bedrock via IAM Role só é seguro se RBAC e infra forem git. Ambiente "quase igual" vira incidente às três da manhã.

Se recomeçássemos a QC: AWS-first (Bedrock + OpenSearch) com cases iFood/Rufus/Natura no slide 1, PrivateLink + Secrets Manager no dia 1, Bastion/SSM no lugar de SSH público, Strangler Fig no checkout antes de sonhar com rewrite. Multi-cloud só com motivo (DR). Egress Brazil South → us-east-1 de 10 TB (~US$ 1,2k–1,8k) apaga economia de lock-in antes do slide de arquitetura esfriar.

## Referências (fontes usadas nesta entrega)

- AWS — [Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
- Microsoft — [Azure built-in roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- Sam Newman — [Monolith Decomposition Patterns](https://samnewman.io/talks/monolith-decomposition-patterns/) · [InfoQ](https://www.infoq.com/presentations/microservices-principles-patterns/)
- AWS Cases — [iFood](https://aws.amazon.com/solutions/case-studies/ifood-bedrock/) · [Rufus/Bedrock](https://aws.amazon.com/blogs/machine-learning/how-rufus-scales-conversational-shopping-experiences-to-millions-of-amazon-customers-with-amazon-bedrock/) · [Natura](https://aws.amazon.com/solutions/case-studies/natura-ia-generativa/) · [Mercado Libre](https://aws.amazon.com/solutions/case-studies/mercado-libre-mutt-data/)
- Azure Bandwidth — [Pricing](https://azure.microsoft.com/pricing/details/bandwidth/)

## Artefatos do ZIP

- Diagrama QC (AWS): `diagramas/arquitetura-qc-aula01.png`
- Fonte Mermaid QC: `diagramas/arquitetura-qc-aula01.mmd`
- Diagrama multi-cloud (AWS+Azure): `diagramas/arquitetura-qc-multicloud.png`
- Fonte Mermaid multi-cloud: `diagramas/arquitetura-qc-multicloud.mmd`
- Código Terraform: `terraform/`
- Código Bicep: `bicep/`
- Página Nginx (brand Group One): `nginx/index.html`
- Print Nginx: `evidencias/nginx-group-one.png`
- Validação SSH/HTTP: `scripts/validate-nginx.sh`
- Prova SLA/custos/egress: `scripts/check_calcs.py`
- Evidências Terraform: `evidencias/provisionamento.md`
- Evidências Bicep: `evidencias/bicep.md`
