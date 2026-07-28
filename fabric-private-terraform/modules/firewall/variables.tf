variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "sku_tier" { type = string }
variable "firewall_subnet_id" { type = string }
variable "home_region" {
  description = "Home region of the Fabric capacity (drives regional service tags)."
  type        = string
}
variable "paired_regions" {
  description = "Paired regions to also allow for regional service tags."
  type        = list(string)
  default     = []
}
variable "tags" { type = map(string) }
