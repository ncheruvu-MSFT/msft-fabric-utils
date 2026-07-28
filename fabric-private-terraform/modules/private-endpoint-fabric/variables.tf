variable "name_prefix" { type = string }
variable "location" { type = string }
variable "resource_group_name" { type = string }
variable "tenant_id" { type = string }
variable "subnet_id" { type = string }
variable "private_dns_zone_ids" { type = list(string) }
variable "tags" { type = map(string) }
