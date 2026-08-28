# Azure Container Registry — guarda a imagem do container FastAPI
resource "azurerm_container_registry" "acr" {
  name                = "acrqc${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true # didático; em produção, usar Managed Identity para auth
  tags                = local.tags
}

# Managed Identity user-assigned para o ACI (separada da Function)
resource "azurerm_user_assigned_identity" "aci_id" {
  name                = "id-aci-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  tags                = local.tags
}

# Permissão para a UAI do ACI ler blobs do Storage do catálogo
# (já podemos conceder antes do ACI existir — a role pertence à identidade, não ao ACI)
resource "azurerm_role_assignment" "aci_blob_reader" {
  scope                = azurerm_storage_account.catalogo.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.aci_id.principal_id
}

locals {
  # Valor "secreto" só para demonstrar secure_environment_variables no 2.3(c).
  # A connection string do App Insights não é uma senha, mas ilustra bem o
  # ponto: qualquer coisa aqui dentro some do `az container show` e do portal.
  aci_secret_demo = azurerm_application_insights.ai.connection_string
}

# ---------------------------------------------------------------------------
# Variante A (lab / padrão) — 0.5 vCPU / 1GB, restart_policy = Always.
# Serviço sempre-on, como o catálogo da QC em produção normal.
# Habilitada via var.aci_enabled (a imagem precisa existir no ACR antes).
# ---------------------------------------------------------------------------
resource "azurerm_container_group" "aci" {
  count = var.aci_enabled ? 1 : 0

  name                = "aci-qc-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  ip_address_type     = "Public"
  dns_name_label      = "qc-api-${random_string.sufixo.result}"
  os_type             = "Linux"
  restart_policy      = "Always"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aci_id.id]
  }

  image_registry_credential {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }

  container {
    name   = "produtos-api"
    image  = "${azurerm_container_registry.acr.login_server}/produtos-api:v1"
    cpu    = "0.5"
    memory = "1.0"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      STORAGE_ACCOUNT_CATALOGO = azurerm_storage_account.catalogo.name
      AZURE_CLIENT_ID          = azurerm_user_assigned_identity.aci_id.client_id
    }

    # Exercício 2.3(c) — não aparece em texto plano no portal/CLI.
    secure_environment_variables = {
      APPINSIGHTS_CONNECTION_STRING = local.aci_secret_demo
    }
  }

  tags = local.tags
}

# ---------------------------------------------------------------------------
# Variante B (2.3-b, right-sizing) — 1 vCPU / 2GB, mesmo serviço sempre-on.
# Sobe lado a lado da variante A só para comparar custo/hora (az container show
# + Pricing Calculator). Habilitada via var.aci_sized_enabled.
# ---------------------------------------------------------------------------
resource "azurerm_container_group" "aci_sized" {
  count = var.aci_sized_enabled ? 1 : 0

  name                = "aci-qc-sized-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  ip_address_type     = "Public"
  dns_name_label      = "qc-api-sized-${random_string.sufixo.result}"
  os_type             = "Linux"
  restart_policy      = "Always"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aci_id.id]
  }

  image_registry_credential {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }

  container {
    name   = "produtos-api"
    image  = "${azurerm_container_registry.acr.login_server}/produtos-api:v1"
    cpu    = "1"
    memory = "2.0"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      STORAGE_ACCOUNT_CATALOGO = azurerm_storage_account.catalogo.name
      AZURE_CLIENT_ID          = azurerm_user_assigned_identity.aci_id.client_id
    }

    secure_environment_variables = {
      APPINSIGHTS_CONNECTION_STRING = local.aci_secret_demo
    }
  }

  tags = local.tags
}

# ---------------------------------------------------------------------------
# Variante C (2.3-a, job batch) — restart_policy = OnFailure, mesma imagem
# rodando `python -c "..."` simulando um recálculo noturno de recomendações
# que roda e termina sozinho (sem servir HTTP, sem porta exposta).
# Habilitada via var.aci_job_enabled.
# ---------------------------------------------------------------------------
resource "azurerm_container_group" "aci_job" {
  count = var.aci_job_enabled ? 1 : 0

  name                = "aci-qc-job-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  ip_address_type     = "None"
  os_type             = "Linux"
  restart_policy      = "OnFailure"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aci_id.id]
  }

  image_registry_credential {
    server   = azurerm_container_registry.acr.login_server
    username = azurerm_container_registry.acr.admin_username
    password = azurerm_container_registry.acr.admin_password
  }

  container {
    name     = "recalculo-recomendacoes"
    image    = "${azurerm_container_registry.acr.login_server}/produtos-api:v1"
    cpu      = "0.5"
    memory   = "1.0"
    commands = ["python", "-c", "print('recalculo de recomendacoes QC: ok'); import sys; sys.exit(0)"]

    environment_variables = {
      STORAGE_ACCOUNT_CATALOGO = azurerm_storage_account.catalogo.name
      AZURE_CLIENT_ID          = azurerm_user_assigned_identity.aci_id.client_id
    }
  }

  tags = local.tags
}
