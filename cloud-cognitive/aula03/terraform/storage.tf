# Storage Account obrigatório para a Function (estado interno + pacote de deploy)
resource "azurerm_storage_account" "func_sa" {
  name                     = "stfunc${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# Container onde o Flex Consumption guarda o pacote de deploy da Function
resource "azurerm_storage_container" "deployments" {
  name               = "deployments"
  storage_account_id = azurerm_storage_account.func_sa.id
}

# Storage do CATÁLOGO da QC — criado NESTA aula (Aula 3 é independente da Aula 2).
# A Function e o ACI leem o produtos.csv daqui via Managed Identity.
resource "azurerm_storage_account" "catalogo" {
  name                     = "stcatqc${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

resource "azurerm_storage_container" "catalogo" {
  name                  = "catalogo"
  storage_account_id    = azurerm_storage_account.catalogo.id
  container_access_type = "private"
}

# Sobe o produtos.csv automaticamente no apply — sem passo de upload manual.
resource "azurerm_storage_blob" "produtos" {
  name                 = "produtos.csv"
  storage_container_id = azurerm_storage_container.catalogo.id
  type                 = "Block"
  source               = "${path.module}/../function/data/produtos.csv"
}
