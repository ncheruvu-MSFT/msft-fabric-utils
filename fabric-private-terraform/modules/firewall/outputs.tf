output "firewall_id" {
  value = module.fw.resource_id
}

output "firewall_private_ip" {
  value = module.fw.resource.ip_configuration[0].private_ip_address
}

output "firewall_policy_id" {
  value = module.fw_policy.resource_id
}

output "firewall_public_ip" {
  value = module.pip.public_ip_address
}
