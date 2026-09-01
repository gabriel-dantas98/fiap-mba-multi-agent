terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      # 4.x é necessário para azurerm_function_app_flex_consumption (Flex Consumption,
      # sucessor do Linux Consumption/Y1 que será aposentado em set/2028).
      version = ">= 4.4, < 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  tags = {
    aula         = "3"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    grupo        = "01"
    provisionado = "terraform"
  }
}

# Resource Group da Aula 3
resource "azurerm_resource_group" "rg" {
  name     = "rg-qc-aula03-grupo01-${random_string.sufixo.result}"
  location = var.location
  tags     = local.tags
}

# Flex Consumption Plan (FC1) — sucessor do Linux Consumption/Y1 (que será
# aposentado em set/2028). Pay-per-execution, cold start menor, escala melhor.
resource "azurerm_service_plan" "plan" {
  name                = "asp-qc-aula03-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}

# Storage Accounts (Function + catálogo) estão em storage.tf
# Application Insights está em insights.tf
