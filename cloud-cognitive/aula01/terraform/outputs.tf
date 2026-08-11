output "public_ip_address" {
  description = "IP público da VM."
  value       = azurerm_public_ip.vm.ip_address
}
