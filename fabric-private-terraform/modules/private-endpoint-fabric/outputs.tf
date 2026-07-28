output "private_link_service_id" {
  value = azapi_resource.fabric_pls.id
}

output "private_endpoint_id" {
  value = module.pe.resource_id
}

output "private_endpoint_ip" {
  description = "Private IP assigned by the PE NIC."
  value       = try(module.pe.resource.private_service_connection[0].private_ip_address, null)
}
