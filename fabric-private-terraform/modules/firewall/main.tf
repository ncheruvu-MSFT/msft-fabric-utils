################################################################################
# Firewall module — AVM-wrapped
#
# Uses:
#   - Azure/avm-res-network-publicipaddress/azurerm (~> 0.2) for the PIP
#   - Azure/avm-res-network-firewallpolicy/azurerm (~> 0.3) for the policy
#   - Azure/avm-res-network-azurefirewall/azurerm (~> 0.4) for the firewall
#
# Rule collection groups are kept as native `azurerm_firewall_policy_rule_collection_group`
# resources — no AVM module covers them with the rich rule schema we need
# (Fabric service tags + per-region SQL/PowerBI/DataFactory/EventHub).
################################################################################

locals {
  # Service tags supported by Fabric (per the Fabric service-tags doc).
  # Regional tags expand to one destination per supplied region.
  regions = distinct(concat([var.home_region], var.paired_regions))

  sql_destinations         = [for r in local.regions : "Sql.${r}"]
  powerbi_destinations     = [for r in local.regions : "PowerBI.${r}"]
  datafactory_destinations = [for r in local.regions : "DataFactory.${r}"]
  eventhub_destinations    = [for r in local.regions : "EventHub.${r}"]
}

module "pip" {
  source  = "Azure/avm-res-network-publicipaddress/azurerm"
  version = "~> 0.2"

  name                = "pip-${var.name_prefix}-fw"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  allocation_method = "Static"
  sku               = "Standard"
  enable_telemetry  = false
}

module "fw_policy" {
  source  = "Azure/avm-res-network-firewallpolicy/azurerm"
  version = "~> 0.3"

  name                = "afwp-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  firewall_policy_sku = var.sku_tier
  firewall_policy_dns = {
    proxy_enabled = true
  }
  enable_telemetry = false
}

module "fw" {
  source  = "Azure/avm-res-network-azurefirewall/azurerm"
  version = "~> 0.4"

  name                = "afw-${var.name_prefix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  firewall_sku_name  = "AZFW_VNet"
  firewall_sku_tier  = var.sku_tier
  firewall_policy_id = module.fw_policy.resource_id

  ip_configurations = {
    ipcfg = {
      name                 = "ipcfg"
      subnet_id            = var.firewall_subnet_id
      public_ip_address_id = module.pip.resource_id
    }
  }

  firewall_zones   = ["1", "2", "3"]
  enable_telemetry = false
}

# -------------------- Network rule collection group (service tags) --------------------

resource "azurerm_firewall_policy_rule_collection_group" "network" {
  name               = "rcg-fabric-network"
  firewall_policy_id = module.fw_policy.resource_id
  priority           = 1000

  network_rule_collection {
    name     = "allow-fabric-sql"
    priority = 1100
    action   = "Allow"

    rule {
      name                  = "fabric-sql-warehouse"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = local.sql_destinations
      destination_ports     = ["1433", "11000-11999"]
    }
  }

  network_rule_collection {
    name     = "allow-powerbi"
    priority = 1200
    action   = "Allow"

    rule {
      name                  = "powerbi"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = local.powerbi_destinations
      destination_ports     = ["443"]
    }
  }

  network_rule_collection {
    name     = "allow-datafactory"
    priority = 1300
    action   = "Allow"

    rule {
      name                  = "datafactory"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = local.datafactory_destinations
      destination_ports     = ["443"]
    }

    rule {
      name                  = "datafactory-management"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = ["DataFactoryManagement"]
      destination_ports     = ["443"]
    }
  }

  network_rule_collection {
    name     = "allow-eventhub"
    priority = 1400
    action   = "Allow"

    rule {
      name                  = "eventhub"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = local.eventhub_destinations
      destination_ports     = ["443", "5671-5672"]
    }
  }

  network_rule_collection {
    name     = "allow-global-tags"
    priority = 1900
    action   = "Allow"

    rule {
      name                  = "aad"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = ["AzureActiveDirectory"]
      destination_ports     = ["443"]
    }

    rule {
      name                  = "powerquery"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = ["PowerQueryOnline"]
      destination_ports     = ["443"]
    }

    rule {
      name                  = "monitor"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = ["AzureMonitor"]
      destination_ports     = ["443"]
    }

    rule {
      name                  = "storage"
      protocols             = ["TCP"]
      source_addresses      = ["*"]
      destination_addresses = ["Storage"]
      destination_ports     = ["443"]
    }
  }
}

# -------------------- Application rule collection group (FQDNs) --------------------

resource "azurerm_firewall_policy_rule_collection_group" "application" {
  name               = "rcg-fabric-application"
  firewall_policy_id = module.fw_policy.resource_id
  priority           = 2000

  application_rule_collection {
    name     = "allow-fabric-fqdns"
    priority = 2100
    action   = "Allow"

    rule {
      name = "fabric-portal-and-apis"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "app.fabric.microsoft.com",
        "api.fabric.microsoft.com",
        "api.powerbi.com",
        "content.powerapps.com",
        "dc.services.visualstudio.com",
        "gatewayadminportal.azure.com",
      ]
    }

    rule {
      name = "fabric-wildcards"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "*.fabric.microsoft.com",
        "*.powerbi.com",
        "*.analysis.windows.net",
        "*.pbidedicated.windows.net",
        "*.datawarehouse.fabric.microsoft.com",
        "*.datamart.fabric.microsoft.com",
        "*.database.fabric.microsoft.com",
        "*.powerquery.microsoft.com",
        "*.servicebus.windows.net",
        "*.events.data.microsoft.com",
      ]
    }

    rule {
      name = "aad-login"
      protocols {
        type = "Https"
        port = 443
      }
      source_addresses = ["*"]
      destination_fqdns = [
        "login.microsoftonline.com",
        "login.windows.net",
        "aadcdn.msftauth.net",
        "aadcdn.msauth.net",
        "*.msftidentity.com",
        "*.msauth.net",
      ]
    }
  }

  application_rule_collection {
    name     = "allow-fqdn-tags"
    priority = 2200
    action   = "Allow"

    rule {
      name             = "windows-update"
      source_addresses = ["*"]
      protocols {
        type = "Https"
        port = 443
      }
      protocols {
        type = "Http"
        port = 80
      }
      destination_fqdn_tags = ["WindowsUpdate", "WindowsDiagnostics", "MicrosoftActiveProtectionService"]
    }
  }
}
