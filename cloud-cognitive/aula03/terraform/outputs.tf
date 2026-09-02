output "resource_group_name" {
  description = "Nome do Resource Group da Aula 3"
  value       = azurerm_resource_group.rg.name
}

output "catalogo_storage_account_name" {
  description = "Storage Account do catálogo (criado nesta aula, já com produtos.csv)"
  value       = azurerm_storage_account.catalogo.name
}

# Function
output "function_app_name" {
  description = "Nome da Function App (usar no 'func azure functionapp publish')"
  value       = azurerm_function_app_flex_consumption.fn.name
}

output "function_app_default_hostname" {
  description = "URL HTTPS da Function App"
  value       = "https://${azurerm_function_app_flex_consumption.fn.default_hostname}"
}

# Application Insights
output "application_insights_name" {
  description = "Nome do Application Insights (Exercício 2.2)"
  value       = azurerm_application_insights.ai.name
}

output "application_insights_app_id" {
  description = "App ID do Application Insights (usar em consultas/portal)"
  value       = azurerm_application_insights.ai.app_id
}

# Container Registry
output "acr_login_server" {
  description = "Endereço do ACR (destino do 'az acr import' da imagem do GHCR)"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  description = "Nome curto do ACR (usar com 'az acr ...')"
  value       = azurerm_container_registry.acr.name
}

# ACI — variante A (lab/padrão)
output "aci_fqdn" {
  description = "FQDN do ACI padrão quando habilitado; do contrário, mensagem"
  value       = var.aci_enabled ? azurerm_container_group.aci[0].fqdn : "ACI padrão ainda não habilitado — apply com -var aci_enabled=true"
}

output "aci_name" {
  description = "Nome do container group padrão (para 'az container logs/show')"
  value       = var.aci_enabled ? azurerm_container_group.aci[0].name : ""
}

output "aci_identity_client_id" {
  description = "Client ID da Managed Identity user-assigned do ACI"
  value       = azurerm_user_assigned_identity.aci_id.client_id
}

# ACI — variante B (2.3-b, right-sizing)
output "aci_sized_fqdn" {
  description = "FQDN da variante 1vCPU/2GB (Exercício 2.3-b)"
  value       = var.aci_sized_enabled ? azurerm_container_group.aci_sized[0].fqdn : "Variante sized não habilitada — apply com -var aci_sized_enabled=true"
}

output "aci_sized_name" {
  description = "Nome do container group da variante sized"
  value       = var.aci_sized_enabled ? azurerm_container_group.aci_sized[0].name : ""
}

# ACI — variante C (2.3-a, job batch)
output "aci_job_name" {
  description = "Nome do container group do job batch (Exercício 2.3-a)"
  value       = var.aci_job_enabled ? azurerm_container_group.aci_job[0].name : ""
}
