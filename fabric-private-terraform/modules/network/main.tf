################################################################################
# Network module — AVM-wrapped
#
# Uses:
#   - Azure/avm-res-network-virtualnetwork/azurerm  (~> 0.17) for VNet + subnets
#   - Azure/avm-res-network-networksecuritygroup/azurerm (~> 0.5) for NSGs
#
# Interface is unchanged — same variables.tf inputs, same outputs.tf shape —
# except that `resource_group_id` is now required (the AVM VNet module needs
# `parent_id`, which is the resource group's resource ID).
################################################################################

locals {
  vnet_name        = "vnet-${var.name_prefix}-${var.location}"
  nsg_pe_name      = "nsg-${var.name_prefix}-pe"
  nsg_jumpbox_name = "nsg-${var.name_prefix}-jumpbox"
}

module "nsg_pe" {
  source  = "Azure/avm-res-network-networksecuritygroup/azurerm"
  version = "~> 0.5"

  name                = local.nsg_pe_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  enable_telemetry    = false
}

module "nsg_jumpbox" {
  source  = "Azure/avm-res-network-networksecuritygroup/azurerm"
  version = "~> 0.5"

  name                = local.nsg_jumpbox_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  enable_telemetry    = false

  security_rules = {
    deny_inbound_internet = {
      name                       = "deny-inbound-internet"
      access                     = "Deny"
      direction                  = "Inbound"
      priority                   = 4096
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }
  }
}

module "vnet" {
  source  = "Azure/avm-res-network-virtualnetwork/azurerm"
  version = "~> 0.17"

  name             = local.vnet_name
  location         = var.location
  parent_id        = var.resource_group_id
  address_space    = toset(var.vnet_address_space)
  tags             = var.tags
  enable_telemetry = false

  subnets = {
    firewall = {
      name             = "AzureFirewallSubnet"
      address_prefixes = [var.subnet_firewall_prefix]
    }
    dnsr_inbound = {
      name             = "snet-dnsr-inbound"
      address_prefixes = [var.subnet_dnsr_inbound_prefix]
      delegations = [{
        name = "dns-resolver-delegation"
        service_delegation = {
          name = "Microsoft.Network/dnsResolvers"
        }
      }]
    }
    dnsr_outbound = {
      name             = "snet-dnsr-outbound"
      address_prefixes = [var.subnet_dnsr_outbound_prefix]
      delegations = [{
        name = "dns-resolver-delegation"
        service_delegation = {
          name = "Microsoft.Network/dnsResolvers"
        }
      }]
    }
    private_endpoints = {
      name             = "snet-private-endpoints"
      address_prefixes = [var.subnet_pe_prefix]
      network_security_group = {
        id = module.nsg_pe.resource_id
      }
    }
    jumpbox = {
      name             = "snet-jumpbox"
      address_prefixes = [var.subnet_jumpbox_prefix]
      network_security_group = {
        id = module.nsg_jumpbox.resource_id
      }
    }
  }
}
