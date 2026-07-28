output "resource_group_name" {
  value = module.rg.name
}

output "vnet_id" {
  value = module.network.vnet_id
}

output "fabric_capacity_id" {
  value = module.fabric_capacity.capacity_id
}

output "fabric_capacity_name" {
  value = module.fabric_capacity.capacity_name
}

output "private_link_service_id" {
  description = "Microsoft.PowerBI/privateLinkServicesForPowerBI resource id (paste into Fabric admin when needed)."
  value       = module.private_endpoint_fabric.private_link_service_id
}

output "private_endpoint_ip" {
  description = "Private IP assigned to the Fabric tenant private endpoint."
  value       = module.private_endpoint_fabric.private_endpoint_ip
}

output "dns_resolver_inbound_ip" {
  description = "IP that on-prem AD DNS conditional forwarders must point to."
  value       = module.dns.dnsr_inbound_ip
}

output "fabric_fqdns" {
  description = "Common Fabric FQDNs to verify with nslookup."
  value = {
    api       = "${replace(var.fabric_tenant_id, "-", "")}-api.privatelink.analysis.windows.net"
    onelake   = "${replace(var.fabric_tenant_id, "-", "")}-onelake.privatelink.analysis.windows.net"
    warehouse = "${replace(var.fabric_tenant_id, "-", "")}-warehouse.privatelink.analysis.windows.net"
  }
}

output "onprem_dns_forwarders" {
  description = "Zones to register as conditional forwarders on on-prem DNS, pointing to dns_resolver_inbound_ip."
  value = [
    "privatelink.analysis.windows.net",
    "privatelink.pbidedicated.windows.net",
    "privatelink.prod.powerquery.microsoft.com",
    "analysis.windows.net",
    "pbidedicated.windows.net",
    "powerquery.microsoft.com",
    "fabric.microsoft.com",
    "powerbi.com",
  ]
}

output "firewall_private_ip" {
  description = "Azure Firewall private IP (use as next-hop in UDRs and on-prem default route, when applicable)."
  value       = var.enable_firewall ? module.firewall[0].firewall_private_ip : null
}

output "onprem_dc_public_ip" {
  description = "Public IP of the simulated on-prem AD DS server (RDP target)."
  value       = var.enable_simulated_onprem ? module.simulated_onprem[0].dc_public_ip : null
}

output "onprem_dc_private_ip" {
  description = "Private IP of the simulated on-prem AD DS server (also the lab VNet DNS server)."
  value       = var.enable_simulated_onprem ? module.simulated_onprem[0].dc_private_ip : null
}

output "onprem_rdp_login_user" {
  description = "Login string to use over RDP — DOMAIN\\admin format works after AD promotion completes."
  value       = var.enable_simulated_onprem ? module.simulated_onprem[0].rdp_login_user : null
}

output "onprem_ad_domain_name" {
  value = var.enable_simulated_onprem ? module.simulated_onprem[0].ad_domain_name : null
}

output "onprem_clients_subnet_id" {
  description = "Use this subnet ID when extending the demo with client VMs joined to the lab AD."
  value       = var.enable_simulated_onprem ? module.simulated_onprem[0].onprem_clients_subnet_id : null
}
