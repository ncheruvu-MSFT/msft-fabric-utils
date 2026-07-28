output "dc_private_ip" {
  value = var.dc_static_ip
}

output "dc_public_ip" {
  value = var.enable_public_ip ? module.pip[0].public_ip_address : null
}

output "dc_fqdn_local" {
  description = "AD-internal FQDN of the lab DC (resolved by AD DNS)."
  value       = "${local.computer_name}.${var.ad_domain_name}"
}

output "ad_domain_name" {
  value = var.ad_domain_name
}

output "rdp_login_user" {
  value = "${var.ad_netbios_name}\\${var.admin_username}"
}

output "onprem_vnet_id" {
  value = module.vnet.resource_id
}

output "onprem_clients_subnet_id" {
  value = module.vnet.subnets["clients"].resource_id
}
