# ---------------------------------------------------------------------------
# ADOPTING THE RESOURCES YOU ALREADY BUILT BY HAND
#
# You already created these with the az CLI. Terraform doesn't know about them,
# so a plain `terraform apply` would try to create duplicates and fail with
# "already exists" errors.
#
# These `import` blocks (Terraform 1.5+) tell Terraform "this real resource IS
# this config block". After one `terraform apply`, Terraform manages them and
# your live URL is preserved.
#
# ⚠️ ONLY USE THIS FILE IF ADOPTING EXISTING RESOURCES.
#    Starting fresh instead? Delete this file.
#
# ⚠️ NAME MISMATCH — READ THIS
#    The CLI auto-generated the Log Analytics workspace as
#    "workspace-rgaiaicookieC0FX", but variables.tf defaults to
#    "law-aiai-cookie". If you import without fixing that, Terraform sees a
#    name change and plans to DESTROY and RECREATE the workspace — which
#    forces the environment to be replaced too, changing your public URL.
#
#    So in terraform.tfvars set:
#        log_analytics_name = "workspace-rgaiaicookieC0FX"
#
#    Always read `terraform plan` output before applying. If it says
#    "must be replaced" for the environment, stop — your URL would change.
# ---------------------------------------------------------------------------

import {
  to = azurerm_resource_group.rg
  id = "/subscriptions/60f1fa6b-f10c-486b-a720-3ee4d299959f/resourceGroups/rg-aiai-cookie"
}

import {
  to = azurerm_log_analytics_workspace.law
  id = "/subscriptions/60f1fa6b-f10c-486b-a720-3ee4d299959f/resourceGroups/rg-aiai-cookie/providers/Microsoft.OperationalInsights/workspaces/workspace-rgaiaicookieC0FX"
}

import {
  to = azurerm_container_app_environment.env
  id = "/subscriptions/60f1fa6b-f10c-486b-a720-3ee4d299959f/resourceGroups/rg-aiai-cookie/providers/Microsoft.App/managedEnvironments/aiai-env"
}

import {
  to = azurerm_container_app.app
  id = "/subscriptions/60f1fa6b-f10c-486b-a720-3ee4d299959f/resourceGroups/rg-aiai-cookie/providers/Microsoft.App/containerapps/aiai-cookie"
}
