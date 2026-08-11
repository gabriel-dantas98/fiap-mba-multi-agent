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
| AWS Lambda | FaaS | Irmão do Azure Functions / Cloud Functions: paga invocação, não VM ociosa. Ainda mais abstraído que PaaS clássico — patch do host some, mas permissão da function, segredos e o que roda no handler são seus. |
| Azure SQL Database | PaaS | RDS e Cloud SQL com sotaque Microsoft: motor gerenciado, schema é seu. Tipo S3/DynamoDB no discurso AWS: infra + plataforma do provedor; dados, criptografia e permissões do cliente. |
| Salesforce CRM | SaaS | Mesmo jogo do Dynamics 365 / HubSpot: CRM alugado, zero rack. Stack quase toda no provedor; você ainda manda em quem entra e no que faz com o dado. |
| Google Kubernetes Engine (GKE) | PaaS/IaaS híbrido | Como AKS e EKS: control plane do provedor, pods e YAML do time. Fronteira típica "of/in the cloud" no meio do stack. |
| Azure Blob Storage | PaaS | S3 / GCS com outro nome: objeto gerenciado, ACL e lifecycle no cliente. AWS chama isso de serviço abstraído — *of the cloud* no storage engine; *in the cloud* em classificação, encryption e IAM. |
| Azure OpenAI Service | SaaS / API-as-a-Service | Bedrock e Vertex AI sem você comprar GPU: chama modelo, não opera cluster. Patch de GPU some; prompt, PII no payload e keys/Managed Identity continuam no seu lado. |

**Responsabilidade compartilhada (lente AWS, válido nos três):** a AWS formaliza o split como *Security of the Cloud* (provedor) vs *Security in the Cloud* (cliente). O quanto você "herda" de tarefa sobe ou desce conforme o modelo — IaaS (VM/EC2) exige quase tudo acima do hipervisor; PaaS/FaaS/serviços abstraídos (S3, DynamoDB, Blob, SQL gerenciado) empurram OS/plataforma pro provedor; SaaS deixa só dados, identidades e config. Azure e GCP desenham a mesma escada; a AWS só batizou o meme. Em qualquer modelo, **dado e identidade não saem do cliente**.

### Exercício 1.2 — Os 6 Rs

**Cenário A:** **Rehost (Lift & Shift)**. Legado de 2008, um mantenedor, zero doc. Empurra a VM pro IaaS (Azure VM / EC2 / GCE) e ganha elasticidade sem reescrever.

**Cenário B:** **Retire**. Menos de 5 usuários/mês. Arquiva em Blob frio / S3 Glacier / Coldline e mata o ERP.

**Cenário C:** **Refactor**. Quebrar monolito em microserviços + K8s + eventos é reescrita estrutural, não maquiagem.

**Cenário D:** **Repurchase**. SaaS cobre ~90% do CRM com TCO menor: troca o interno por Salesforce / Dynamics / HubSpot.

**Cenário E:** **Retain**. BACEN segura o mainframe on-prem; nuvem só onde a auditoria deixar.

### Exercício 1.3 — SLA

Premissa: ano comercial de 8.760 horas.

a) Downtime anual com SLA 99,9%:

`8.760 × (1 − 0,999) = 8,76 horas/ano` (~525,6 minutos).

b) Impacto financeiro máximo:

`8,76 × R$ 50.000 = R$ 438.000/ano`.

c) Para impacto < R$ 50.000/ano:

Downtime máximo = `50.000 / 50.000 = 1 hora/ano`.

`1 / 8.760 ≈ 0,0114%` de downtime → disponibilidade mínima `99,9886%`.

Na prática, o SLA comercial que fecha a conta é **99,99%** (~52,56 min/ano; impacto ≈ R$ 43.800).

### Exercício 1.4 — RBAC

| Perfil | Role Azure | Justificativa |
|--------|------------|---------------|
| Agente de IA que LÊ produtos do Storage | Storage Blob Data Reader | Equivalente a `s3:GetObject` / `storage.objects.get`: lê o plano de dados, não mexe na conta. |
| Engenheiro de dados que CARREGA catálogos | Storage Blob Data Contributor | Como `s3:PutObject` sem Account Owner: sobe blob, não herda billing da subscription. |
| Time de FinOps que VÊ custos | Cost Management Reader | Espelho do Cost Explorer read-only / Billing Viewer: enxerga fatura, não altera SKU. |
| Auditor externo que LÊ a assinatura | Reader (escopo subscription) | `ViewOnlyAccess` / `roles/viewer` no escopo da conta: olha config, não muta. |
| CI/CD que provisiona via Terraform | Contributor no Resource Group + Service Principal dedicado | Igual pipeline com role scoped no AWS account/project GCP: sobe infra no RG, nunca `Owner` da subscription. |

Least privilege: escopo no RG, não na subscription.

## Nível 2 — Respostas + implementação

### Exercício 2.1 — Arquitetura da Quantum Commerce

**Provedor principal:** Azure. Não porque "é o da disciplina", e sim porque o pacote agentic fecha num lugar só: Entra ID + Managed Identity (o que no AWS vira Cognito/IAM Roles e no GCP vira Workload Identity), Azure OpenAI + AI Search (Bedrock+OpenSearch / Vertex+Vector Search), App Service/Functions no lugar de ECS+Lambda ou Cloud Run+Functions. Menos cola entre provedores no caminho crítico do agente.

**Camadas:**

1. **Edge/entrega** — Front Door/CDN + WAF e frontend estático (CloudFront / Cloud CDN do outro lado).
2. **APIs e processamento** — App Service (API síncrona) + Service Bus + Functions (assíncrono).
3. **IA cognitiva / RAG** — Azure OpenAI, AI Search (vetorial) e AI Services (visão/fala/linguagem).
4. **Dados** — SQL (transacional), Cosmos DB (sessões/conversas), Blob (catálogo/imagens).
5. **Plataforma** — Entra ID, Key Vault e Azure Monitor.

Diagrama: [`diagramas/arquitetura-qc-aula01.png`](diagramas/arquitetura-qc-aula01.png) (fonte Mermaid: [`diagramas/arquitetura-qc-aula01.mmd`](diagramas/arquitetura-qc-aula01.mmd)).

| Categoria | Serviço Azure | Alternativa AWS | Alternativa GCP |
|-----------|---------------|-----------------|-----------------|
| Compute (backend) | Azure App Service | Amazon ECS/Fargate ou Elastic Beanstalk | Cloud Run |
| Storage (catálogo, imagens) | Azure Blob Storage | Amazon S3 | Cloud Storage |
| Banco relacional | Azure SQL Database | Amazon RDS | Cloud SQL |
| Banco NoSQL | Azure Cosmos DB | Amazon DynamoDB | Firestore / Bigtable |
| Vector Database | Azure AI Search | Amazon OpenSearch Serverless / Aurora pgvector | Vertex AI Vector Search |
| Serviços de IA cognitivos | Azure OpenAI + AI Services | Amazon Bedrock + Amazon Comprehend/Rekognition | Vertex AI + Cloud Vision/Speech |
| CDN | Azure Front Door / CDN | Amazon CloudFront | Cloud CDN |
| Mensageria/Filas | Azure Service Bus | Amazon SQS/SNS | Pub/Sub |
| Observabilidade | Azure Monitor | Amazon CloudWatch | Cloud Monitoring/Logging |

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

c) Em projeto agentic, preço bruto sem FinOps de dados é mentira parcial. O que decide: região do modelo (Azure OpenAI vs Bedrock vs Vertex), identidade (Managed Identity vs IAM Role vs Workload Identity), vetor (AI Search vs OpenSearch vs Vertex Vector), latência pro Brasil e egress.

### Exercício 2.3 — Estratégia de migração

a) **Workload:** monolito on-prem de e-commerce (catálogo + pedidos + busca), pico de campanha, assistente conversacional pedindo passagem.

b) **R: Replatform** (Refactor só no canal de IA).  
   Custa mais que lift-and-shift puro (EC2/Azure VM/GCE), menos que rewrite. App vai pra App Service/Container Apps (ou ECS/Cloud Run no outro mundo); dados pra Azure SQL/Blob. Em semanas/meses, não anos.

c) **Serviços:** App Service ou Container Apps, Azure SQL, Blob, AI Search, Azure OpenAI, Front Door, Monitor. Dev/homolog enxuto: **US$ 250–450**/mês, SQL e tokens mandam no ticket.

d) **Obstáculo real:** PII/pagamento + medo de mexer no monolito. Resposta: tokenization, Private Endpoints (o VPC endpoint / Private Service Connect do Azure), catálogo primeiro com feature flags.

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

a) **Azure + AWS:**

- **Azure (agente):** frontend, APIs, OpenAI, AI Search, Cosmos/SQL, Entra ID.
- **AWS (mídia/DR):** S3 + CloudFront no catálogo de imagem (onde a AWS ainda é o "CDN barato clássico"); RDS replica ou backup cross-cloud pro failover.
- Por quê essa divisão: o caminho do agente fica num provedor (menos hop de identidade). Mídia e DR vão pra quem já tem músculo de egress/CDN. GCP entraria no jogo se o ganho fosse BigQuery/Vertex, não neste recorte.

b) **Desafios:**

1. Latência cross-cloud sobe o p95 do assistente.
2. Identidade: Entra ID ↔ IAM via OIDC (sem isso vira senha espalhada).
3. Egress de 10 TB/mês (conta abaixo).
4. Trace único: Azure Monitor ↔ CloudWatch (ou OpenTelemetry no meio).

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

**Azure Arc / AWS Outposts:** Arc = governança Azure em VM/cluster fora da Azure (tipo Anthos no GCP, mas do lado Microsoft). Outposts = rack AWS no DC. Na QC, Arc unifica policy de agente híbrido; Outposts só se loja/DC exigir locality de verdade.

## Reflexão coletiva

Cloud sem IaC não se reproduz. Mudar o NSG e ver o `plan` sem recriar a VM foi o momento "ok, isso serve em produção": mudança cirúrgica, auditável. No Azure for Students, policy e capacidade pesaram mais que elegância de HCL. Acontece igual com AZ esgotada na AWS ou quota de GPU no GCP.

Agente com `Storage Blob Data Reader` + OpenAI via Managed Identity só é seguro se RBAC e infra forem git. Ambiente "quase igual" vira incidente às três da manhã.

Se recomeçássemos a QC: Private Endpoints + Key Vault no dia 1, Bastion no lugar de SSH público, banco escolhido com FinOps (SQL GP comeu o comparativo). Multi-cloud só com motivo (DR, mídia). Egress Brazil South → us-east-1 de 10 TB (~US$ 1,2k–1,8k) apaga economia de lock-in antes do slide de arquitetura esfriar.

## Artefatos do ZIP

- Diagrama QC: `diagramas/arquitetura-qc-aula01.png`
- Fonte Mermaid QC: `diagramas/arquitetura-qc-aula01.mmd`
- Diagrama multi-cloud: `diagramas/arquitetura-qc-multicloud.png`
- Fonte Mermaid multi-cloud: `diagramas/arquitetura-qc-multicloud.mmd`
- Código Terraform: `terraform/`
- Código Bicep: `bicep/`
- Página Nginx (brand Group One): `nginx/index.html`
- Print Nginx: `evidencias/nginx-group-one.png`
- Validação SSH/HTTP: `scripts/validate-nginx.sh`
- Evidências Terraform: `evidencias/provisionamento.md`
- Evidências Bicep: `evidencias/bicep.md`
