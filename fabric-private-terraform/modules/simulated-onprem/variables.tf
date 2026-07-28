variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "resource_group_id" {
  description = "Resource ID of the parent resource group (required by Azure/avm-res-network-virtualnetwork/azurerm `parent_id`)."
  type        = string
}
variable "tags" { type = map(string) }

variable "vnet_address_space" {
  type    = list(string)
  default = ["10.60.0.0/16"]
}

variable "subnet_dc_prefix" {
  type    = string
  default = "10.60.1.0/24"
}

variable "subnet_clients_prefix" {
  type    = string
  default = "10.60.2.0/24"
}

variable "dc_static_ip" {
  description = "Static IP for the DC (must be inside subnet_dc_prefix and not in the first 4 reserved addresses)."
  type        = string
  default     = "10.60.1.10"
}

variable "ad_domain_name" {
  type    = string
  default = "lab.contoso.local"
}

variable "ad_netbios_name" {
  type    = string
  default = "LAB"
}

variable "admin_username" {
  type    = string
  default = "labadmin"
}

variable "admin_password" {
  description = "Local + DSRM password for the lab DC. Use a strong value (>= 12 chars, mixed case + digit + symbol)."
  type        = string
  sensitive   = true
}

variable "vm_size" {
  description = "Demo DC VM size. B2ms is the smallest size that comfortably runs AD DS + DNS."
  type        = string
  default     = "Standard_B2ms"
}

variable "admin_source_ip_cidr" {
  description = "CIDR allowed to RDP into the DC. Default 0.0.0.0/0 is OPEN — restrict to your IP for real use."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_public_ip" {
  description = "Set false to keep the DC fully private (use Bastion or a runbook to manage it)."
  type        = bool
  default     = true
}

# ---- Hub linkage ----

variable "hub_vnet_id" {
  description = "Hub VNet ID — used for peering."
  type        = string
}

variable "hub_vnet_name" {
  description = "Hub VNet name. Unused since the AVM VNet module's peerings.create_reverse_peering handles the reverse link; kept for backwards-compatible interface."
  type        = string
  default     = ""
}

variable "dns_resolver_inbound_ip" {
  description = "Private DNS Resolver inbound endpoint IP — passed to the bootstrap script for AD-integrated conditional forwarders."
  type        = string
}

variable "fabric_tenant_id" {
  description = "Used inside the lab DC to compute and verify Fabric private FQDNs."
  type        = string
}
