################################################################################
# DNS module — AVM-wrapped
#
# Uses:
#   - Azure/avm-res-network-privatednszone/azurerm (latest minor) for each
#     of the three Fabric private DNS zones + their VNet links
#   - Azure/avm-res-network-dnsresolver/azurerm (~> 0.8) for the DNS Private
#     Resolver with inbound + outbound endpoints
#
# The DNS resolver AVM module takes `subnet_name` (looked up inside the
# supplied VNet by name) rather than subnet resource IDs. We pass through
# the existing snet-dnsr-inbound / snet-dnsr-outbound names from
# modules/network.
################################################################################

locals {
  fabric_private_dns_zones = [
    "privatelink.analysis.windows.net",
    "privatelink.pbidedicated.windows.net",
    "privatelink.prod.powerquery.microsoft.com",
  ]
}

module "pdz" {
  source  = "Azure/avm-res-network-privatednszone/azurerm"
  version = "~> 0.3"

  for_each = toset(local.fabric_private_dns_zones)

  domain_name = each.value
  parent_id   = var.resource_group_id
  tags        = var.tags

  enable_telemetry = false

  virtual_network_links = {
    hub = {
      vnetlinkname     = "vnetlink-${replace(each.key, ".", "-")}"
      vnetid           = var.vnet_id
      autoregistration = false
    }
  }
}

module "dnsr" {
  source  = "Azure/avm-res-network-dnsresolver/azurerm"
  version = "~> 0.8"

  name                        = "dnsr-${var.name_prefix}"
  location                    = var.location
  resource_group_name         = var.resource_group_name
  virtual_network_resource_id = var.vnet_id
  tags                        = var.tags

  enable_telemetry = false

  inbound_endpoints = {
    in = {
      name                         = "dnsr-${var.name_prefix}-in"
      subnet_name                  = var.dnsr_inbound_subnet_name
      private_ip_allocation_method = "Dynamic"
    }
  }

  outbound_endpoints = {
    out = {
      name        = "dnsr-${var.name_prefix}-out"
      subnet_name = var.dnsr_outbound_subnet_name
    }
  }
}
