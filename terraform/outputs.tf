output "url" {
  description = "Public HTTPS address of the cookie catalogue."
  value       = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}

output "fqdn" {
  description = "Bare hostname, handy for scripting against."
  value       = azurerm_container_app.app.ingress[0].fqdn
}

output "resource_group" {
  description = "Delete this to remove everything: az group delete --name <this> --yes"
  value       = azurerm_resource_group.rg.name
}

output "image" {
  description = "Image currently deployed."
  value       = var.image
}

output "scale" {
  description = "Replica bounds — min 0 is what keeps this free."
  value       = "min ${var.min_replicas} / max ${var.max_replicas}"
}
