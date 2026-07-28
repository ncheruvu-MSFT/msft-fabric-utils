resource "random_string" "suffix" {
  length  = 6
  upper   = false
  numeric = true
  special = false
}

# Fabric capacity name constraint: 3-63 chars, lowercase letter start, letters/digits only.
locals {
  capacity_name = substr("${var.name_prefix}cap${random_string.suffix.result}", 0, 63)
}

resource "azurerm_fabric_capacity" "this" {
  name                = local.capacity_name
  resource_group_name = var.resource_group_name
  location            = var.location

  administration_members = var.admin_members

  sku {
    name = var.sku_name
    tier = "Fabric"
  }

  tags = var.tags
}
