output "zone_analysis_id" {
  value = module.pdz["privatelink.analysis.windows.net"].resource_id
}

output "zone_pbidedicated_id" {
  value = module.pdz["privatelink.pbidedicated.windows.net"].resource_id
}

output "zone_powerquery_id" {
  value = module.pdz["privatelink.prod.powerquery.microsoft.com"].resource_id
}

output "dnsr_inbound_ip" {
  description = "Private IP of the inbound resolver endpoint. Use as on-prem AD conditional forwarder target."
  value       = module.dnsr.inbound_endpoint_ips["in"]
}

output "dnsr_id" {
  value = module.dnsr.resource_id
}
