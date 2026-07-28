################################################################################
# Top-level orchestration
#
# All resource names are now driven by `local.caf` from naming.tf
# (CAF v3 spec: <abbr>-<workload>-<env>-<region>-<instance>).
#
# Bumping `var.instance` (01 -> 02) changes every generated name, which is
# the supported way to recreate the stack after the Fabric capacity 24h name
# reservation. See scripts/recreate.ps1.
################################################################################

module "rg" {
  source  = "Azure/avm-res-resources-resourcegroup/azurerm"
  version = "~> 0.4"

  name             = local.caf.rg
  location         = var.location
  tags             = var.tags
  enable_telemetry = false
}

module "network" {
  source = "./modules/network"

  name_prefix                 = local.caf.short_prefix
  location                    = var.location
  resource_group_name         = module.rg.name
  resource_group_id           = module.rg.resource_id
  vnet_address_space          = var.vnet_address_space
  subnet_firewall_prefix      = var.subnet_firewall_prefix
  subnet_dnsr_inbound_prefix  = var.subnet_dnsr_inbound_prefix
  subnet_dnsr_outbound_prefix = var.subnet_dnsr_outbound_prefix
  subnet_pe_prefix            = var.subnet_pe_prefix
  subnet_jumpbox_prefix       = var.subnet_jumpbox_prefix
  tags                        = var.tags
}

module "dns" {
  source = "./modules/dns"

  name_prefix         = local.caf.short_prefix
  location            = var.location
  resource_group_name = module.rg.name
  resource_group_id   = module.rg.resource_id
  vnet_id             = module.network.vnet_id
  # DNS resolver AVM looks up subnets by name inside the supplied VNet.
  dnsr_inbound_subnet_name  = "snet-dnsr-inbound"
  dnsr_outbound_subnet_name = "snet-dnsr-outbound"
  tags                      = var.tags
}

module "fabric_capacity" {
  source = "./modules/fabric-capacity"

  name_prefix         = local.caf.short_prefix
  location            = var.location
  resource_group_name = module.rg.name
  sku_name            = var.capacity_sku
  admin_members       = var.capacity_admin_members
  tags                = var.tags
}

module "private_endpoint_fabric" {
  source = "./modules/private-endpoint-fabric"

  name_prefix         = local.caf.short_prefix
  location            = var.location
  resource_group_name = module.rg.name
  tenant_id           = var.fabric_tenant_id
  subnet_id           = module.network.subnet_pe_id

  private_dns_zone_ids = [
    module.dns.zone_analysis_id,
    module.dns.zone_pbidedicated_id,
    module.dns.zone_powerquery_id,
  ]

  tags = var.tags
}

module "firewall" {
  count  = var.enable_firewall ? 1 : 0
  source = "./modules/firewall"

  name_prefix         = local.caf.short_prefix
  location            = var.location
  resource_group_name = module.rg.name
  sku_tier            = var.firewall_sku_tier
  firewall_subnet_id  = module.network.subnet_firewall_id
  home_region         = var.location
  paired_regions      = var.paired_regions
  tags                = var.tags
}

module "simulated_onprem" {
  count  = var.enable_simulated_onprem ? 1 : 0
  source = "./modules/simulated-onprem"

  name_prefix         = local.caf.short_prefix
  location            = var.location
  resource_group_name = module.rg.name
  resource_group_id   = module.rg.resource_id
  tags                = var.tags

  vnet_address_space    = var.onprem_vnet_address_space
  subnet_dc_prefix      = var.onprem_subnet_dc_prefix
  subnet_clients_prefix = var.onprem_subnet_clients_prefix
  dc_static_ip          = var.onprem_dc_static_ip

  ad_domain_name  = var.onprem_ad_domain_name
  ad_netbios_name = var.onprem_ad_netbios_name
  admin_username  = var.onprem_admin_username
  admin_password  = var.onprem_admin_password
  vm_size         = var.onprem_vm_size

  admin_source_ip_cidr = var.onprem_admin_source_ip_cidr
  enable_public_ip     = var.onprem_enable_public_ip

  hub_vnet_id             = module.network.vnet_id
  hub_vnet_name           = module.network.vnet_name
  dns_resolver_inbound_ip = module.dns.dnsr_inbound_ip
  fabric_tenant_id        = var.fabric_tenant_id
}
