output "vnet_id" { value = module.vnet.resource_id }
output "vnet_name" { value = module.vnet.name }
output "subnet_firewall_id" { value = module.vnet.subnets["firewall"].resource_id }
output "subnet_dnsr_inbound_id" { value = module.vnet.subnets["dnsr_inbound"].resource_id }
output "subnet_dnsr_outbound_id" { value = module.vnet.subnets["dnsr_outbound"].resource_id }
output "subnet_pe_id" { value = module.vnet.subnets["private_endpoints"].resource_id }
output "subnet_jumpbox_id" { value = module.vnet.subnets["jumpbox"].resource_id }
