variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "sku_name" { type = string }
variable "admin_members" { type = list(string) }
variable "tags" { type = map(string) }
