################################################################################
# Fabric tenant private endpoint module — AVM-wrapped PE
#
# Uses:
#   - Azure/avm-res-network-privateendpoint/azurerm (~> 0.2) for the PE
#
# The Microsoft.PowerBI/privateLinkServicesForPowerBI resource is kept as
# `azapi_resource` (azurerm has no first-class resource for it). The PE then
# wires that PLS into the hub VNet and registers it with the three Fabric
# private DNS zones.
################################################################################

locals {
  pl_service_name = "pls-${var.name_prefix}-fabric"
  pe_name         = "pe-${var.name_prefix}-fabric"
}

data "azurerm_client_config" "current" {}

resource "azapi_resource" "fabric_pls" {
  type      = "Microsoft.PowerBI/privateLinkServicesForPowerBI@2020-06-01"
  name      = local.pl_service_name
  location  = "global"
  parent_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_name}"

  body = {
    properties = {
      tenantId = var.tenant_id
    }
  }

  response_export_values = ["id"]
  tags                   = var.tags

  # Power BI PLS create can take 10+ minutes; bump Terraform-side context deadline well above default.
  timeouts {
    create = "45m"
    update = "45m"
    delete = "30m"
    read   = "10m"
  }

  # Retry only on transient async failures during polling — NOT on tenant config errors.
  retry = {
    error_message_regex = [
      "AnotherOperationInProgress",
      "RequestTimeout",
      "InternalServerError",
    ]
    interval_seconds     = 15
    max_interval_seconds = 120
    multiplier           = 1.5
    randomization_factor = 0.5
  }
}

module "pe" {
  source  = "Azure/avm-res-network-privateendpoint/azurerm"
  version = "~> 0.2"

  name                   = local.pe_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  network_interface_name = "${local.pe_name}-nic"
  tags                   = var.tags

  subnet_resource_id              = var.subnet_id
  private_connection_resource_id  = azapi_resource.fabric_pls.id
  subresource_names               = ["tenant"]
  private_service_connection_name = "${local.pe_name}-conn"

  private_dns_zone_group_name   = "fabric-private-dns-zones"
  private_dns_zone_resource_ids = var.private_dns_zone_ids

  enable_telemetry = false
}
