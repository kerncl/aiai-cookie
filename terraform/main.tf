# aiai 饼家 — the same infrastructure we built by hand, as code.
#
# Equivalent to these three commands:
#   az group create --name rg-aiai-cookie --location southeastasia
#   az containerapp env create --name aiai-env ...
#   az containerapp create --name aiai-cookie ... --min-replicas 0 --max-replicas 2

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # State is local by default — fine for learning, and it means no extra Azure
  # resources (so still RM 0). See README for moving it to Azure Storage.
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# ---------------------------------------------------------------------------
# ① Resource group — free, just a folder
# ---------------------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

# ---------------------------------------------------------------------------
# Log Analytics workspace
#
# The az CLI auto-created this with a random name (workspace-rgaiaicookieC0FX).
# Terraform makes it explicit — which is the point of IaC: nothing appears by
# magic with a name you didn't choose.
#
# This is the only metered resource here (~$2.99/GB ingestion). Our logs are
# well under 1 MB/month. 30-day retention is the minimum billable period.
# ---------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "law" {
  name                = var.log_analytics_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

# ---------------------------------------------------------------------------
# ② Container Apps environment — free on Consumption
#
# Provides networking, ingress, TLS and the DNS name. NOTE: recreating this
# changes the random subdomain in your URL (purplewater-3872fd76), so your
# public address changes. Treat it as semi-permanent.
# ---------------------------------------------------------------------------
resource "azurerm_container_app_environment" "env" {
  name                       = var.environment_name
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.law.id

  tags = var.tags
}

# ---------------------------------------------------------------------------
# ③ The container app itself
# ---------------------------------------------------------------------------
resource "azurerm_container_app" "app" {
  name                         = var.app_name
  resource_group_name          = azurerm_resource_group.rg.name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  template {
    # min_replicas = 0 is what makes this RM 0 — nothing runs when idle.
    # max_replicas = 2 is the hard spend ceiling: Azure physically cannot
    # start a third replica, capping worst case at roughly RM 195/month.
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = var.app_name
      image  = var.image
      cpu    = var.cpu    # number, not string
      memory = var.memory # string with unit, e.g. "0.5Gi"
    }
  }

  ingress {
    external_enabled = true          # without this there's no public URL
    target_port      = var.target_port # must match EXPOSE in the Dockerfile
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = var.tags
}
