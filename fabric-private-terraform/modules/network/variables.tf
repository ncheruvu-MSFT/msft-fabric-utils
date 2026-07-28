variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "resource_group_id" {
  description = "Resource ID of the parent resource group (required by Azure/avm-res-network-virtualnetwork/azurerm `parent_id`)."
  type        = string
}
variable "vnet_address_space" { type = list(string) }
variable "subnet_firewall_prefix" { type = string }
variable "subnet_dnsr_inbound_prefix" { type = string }
variable "subnet_dnsr_outbound_prefix" { type = string }
variable "subnet_pe_prefix" { type = string }
variable "subnet_jumpbox_prefix" { type = string }
variable "tags" { type = map(string) }
