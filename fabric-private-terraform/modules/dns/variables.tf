variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "resource_group_id" {
  description = "Resource ID of the parent resource group (required by Azure/avm-res-network-privatednszone/azurerm `parent_id`)."
  type        = string
}
variable "vnet_id" { type = string }
variable "dnsr_inbound_subnet_name" {
  description = "Name (NOT resource id) of the inbound endpoint subnet inside the hub VNet. AVM dnsresolver looks it up by name."
  type        = string
  default     = "snet-dnsr-inbound"
}
variable "dnsr_outbound_subnet_name" {
  description = "Name (NOT resource id) of the outbound endpoint subnet inside the hub VNet."
  type        = string
  default     = "snet-dnsr-outbound"
}
variable "tags" { type = map(string) }
