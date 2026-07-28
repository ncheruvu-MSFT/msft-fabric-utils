################################################################################
# CAF naming reference
#
# Builds the canonical CAF v3 names for every resource in this stack:
#   <abbr>-<workload>-<env>-<region_short>-<instance>
#
# These are exposed as `local.caf` and as the `caf_naming` output so they can
# be consumed by the validation notebook (notebooks/01_smoke_test.ipynb).
#
# Adoption is non-breaking by default: the module wiring still passes
# `var.name_prefix` into each module, which preserves the names of any
# already-deployed resources. To fully adopt CAF, replace `var.name_prefix`
# with `local.caf.short_prefix` in main.tf module calls (forces destroy/recreate).
################################################################################

variable "environment" {
  description = "CAF environment short code (dev, test, demo, prod)."
  type        = string
  default     = "demo"
  validation {
    condition     = contains(["dev", "test", "demo", "stg", "prod"], var.environment)
    error_message = "environment must be one of: dev, test, demo, stg, prod."
  }
}

variable "instance" {
  description = "CAF instance index, zero-padded (e.g. 01, 02). Lets you recreate after a Fabric capacity 24h name-reservation conflict by bumping to 02."
  type        = string
  default     = "01"
  validation {
    condition     = can(regex("^[0-9]{2,3}$", var.instance))
    error_message = "instance must be a 2 or 3 digit zero-padded number (01, 02, 010)."
  }
}

locals {
  # Region short codes (CAF Microsoft official abbreviations).
  region_short_map = {
    eastus             = "eus"
    eastus2            = "eus2"
    centralus          = "cus"
    westus             = "wus"
    westus2            = "wus2"
    westus3            = "wus3"
    northcentralus     = "ncus"
    southcentralus     = "scus"
    westcentralus      = "wcus"
    canadacentral      = "cac"
    canadaeast         = "cae"
    westeurope         = "weu"
    northeurope        = "neu"
    uksouth            = "uks"
    ukwest             = "ukw"
    francecentral      = "frc"
    germanywestcentral = "gwc"
    swedencentral      = "swc"
    switzerlandnorth   = "chn"
    norwayeast         = "noe"
    eastasia           = "ea"
    southeastasia      = "sea"
    japaneast          = "jpe"
    japanwest          = "jpw"
    koreacentral       = "krc"
    australiaeast      = "aue"
    australiasoutheast = "ause"
    centralindia       = "inc"
    southindia         = "ins"
    uaenorth           = "uaen"
    southafricanorth   = "san"
    brazilsouth        = "brs"
  }
  region_short = lookup(local.region_short_map, var.location, substr(replace(var.location, "/[^a-z0-9]/", ""), 0, 4))

  caf_suffix = "${var.name_prefix}-${var.environment}-${local.region_short}-${var.instance}"

  caf = {
    # Composable building blocks
    short_prefix = "${var.name_prefix}${var.environment}${var.instance}" # for storage / kv (alnum, <=24)
    suffix       = local.caf_suffix
    region_short = local.region_short

    # Resource-typed names (CAF abbreviations from
    # https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations)
    rg            = "rg-${local.caf_suffix}"
    vnet          = "vnet-${local.caf_suffix}"
    snet_firewall = "AzureFirewallSubnet" # FIXED by Azure
    snet_dnsr_in  = "snet-dnspr-in-${local.caf_suffix}"
    snet_dnsr_out = "snet-dnspr-out-${local.caf_suffix}"
    snet_pe       = "snet-pep-${local.caf_suffix}"
    snet_jumpbox  = "snet-jbox-${local.caf_suffix}"
    nsg_pe        = "nsg-pep-${local.caf_suffix}"
    nsg_jumpbox   = "nsg-jbox-${local.caf_suffix}"
    nsg_onprem    = "nsg-onprem-${local.caf_suffix}"

    dnspr        = "dnspr-${local.caf_suffix}"
    dnspr_in_ep  = "dnspr-${local.caf_suffix}-in"
    dnspr_out_ep = "dnspr-${local.caf_suffix}-out"

    pip_firewall = "pip-afw-${local.caf_suffix}"
    afw          = "afw-${local.caf_suffix}"
    afwp         = "afwp-${local.caf_suffix}"

    fabric_capacity = "fab-${local.caf_suffix}" # note: 24h name reservation -> bump var.instance to recreate
    pls_fabric      = "pls-fab-${local.caf_suffix}"
    pep_fabric      = "pep-fab-${local.caf_suffix}"

    onprem_vnet         = "vnet-onprem-${local.caf_suffix}"
    onprem_snet_dc      = "snet-dc-${local.caf_suffix}"
    onprem_snet_clients = "snet-clients-${local.caf_suffix}"
    onprem_vm_dc        = "vm-dc-${local.caf_suffix}"
    onprem_nic_dc       = "nic-dc-${local.caf_suffix}"
    onprem_pip_dc       = "pip-dc-${local.caf_suffix}"

    private_dns_zones = [
      "privatelink.analysis.windows.net",
      "privatelink.pbidedicated.windows.net",
      "privatelink.prod.powerquery.microsoft.com",
    ]
  }
}

output "caf_naming" {
  description = "CAF-spec resource names for every component in this stack. Consumed by notebooks/01_smoke_test.ipynb."
  value       = local.caf
}
