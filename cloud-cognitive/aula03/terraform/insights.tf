# Exercício 2.2 — Application Insights e observabilidade.
# A Function do lab veio SEM App Insights (desativado para custo). Aqui religamos:
# workspace-based (padrão atual do Azure Monitor), conectado via connection
# string na Function.
resource "azurerm_log_analytics_workspace" "law" {
  name                = "law-qc-aula03-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 1
  tags                = local.tags
}

resource "azurerm_application_insights" "ai" {
  name                = "appi-qc-aula03-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
  tags                = local.tags
}
