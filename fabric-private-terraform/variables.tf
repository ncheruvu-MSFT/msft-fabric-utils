variable "name_prefix" {
  description = "Short prefix for all resource names (lowercase, 3-8 chars)."
  type        = string
  default     = "fabpl"
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{2,7}$", var.name_prefix))
    error_message = "name_prefix must be 3-8 chars, lowercase, starting with a letter."
  }
}

variable "location" {
  description = "Primary Azure region (capacity home region)."
  type        = string
  default     = "eastus2"
}

variable "paired_regions" {
  description = "Additional regions to allow in service-tag firewall rules (e.g. paired region of the capacity)."
  type        = list(string)
  default     = ["centralus"]
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default = {
    workload    = "fabric-private-demo"
    environment = "demo"
    managed_by  = "terraform"
  }
}

# ---- VNet ----

variable "vnet_address_space" {
  description = "Hub VNet address space."
  type        = list(string)
  default     = ["10.50.0.0/16"]
}

variable "subnet_firewall_prefix" {
  description = "AzureFirewallSubnet prefix (must be /26 or larger)."
  type        = string
  default     = "10.50.1.0/26"
}

variable "subnet_dnsr_inbound_prefix" {
  description = "Private DNS Resolver inbound endpoint subnet."
  type        = string
  default     = "10.50.2.0/28"
}

variable "subnet_dnsr_outbound_prefix" {
  description = "Private DNS Resolver outbound endpoint subnet."
  type        = string
  default     = "10.50.2.16/28"
}

variable "subnet_pe_prefix" {
  description = "Private endpoints subnet."
  type        = string
  default     = "10.50.3.0/24"
}

variable "subnet_jumpbox_prefix" {
  description = "Optional jumpbox subnet."
  type        = string
  default     = "10.50.4.0/27"
}

# ---- Fabric capacity ----

variable "capacity_sku" {
  description = "Fabric SKU (F2..F2048). Demo default = F2."
  type        = string
  default     = "F2"
}

variable "capacity_admin_members" {
  description = <<-EOT
    Capacity administrators. Entra user UPNs OR service-principal object IDs.
    For Entra groups, provide the group's object ID.
  EOT
  type        = list(string)
}

# ---- Fabric tenant private link service ----

variable "fabric_tenant_id" {
  description = "Entra tenant ID that owns the Fabric tenant being private-linked."
  type        = string
}

# ---- Firewall behaviour toggles ----

variable "enable_firewall" {
  description = "Set false to skip Azure Firewall (useful for cost-minimal demos)."
  type        = bool
  default     = true
}

variable "firewall_sku_tier" {
  description = "Azure Firewall SKU tier. Standard is cheapest with rule-collection groups."
  type        = string
  default     = "Standard"
}

# ---- Simulated on-prem lab (peered second VNet with AD DS + DNS) ----

variable "enable_simulated_onprem" {
  description = "Set true to deploy a peered VNet + Windows Server promoted to AD DS + DNS, simulating an on-prem ExpressRoute landing zone."
  type        = bool
  default     = false
}

variable "onprem_vnet_address_space" {
  type    = list(string)
  default = ["10.60.0.0/16"]
}

variable "onprem_subnet_dc_prefix" {
  type    = string
  default = "10.60.1.0/24"
}

variable "onprem_subnet_clients_prefix" {
  type    = string
  default = "10.60.2.0/24"
}

variable "onprem_dc_static_ip" {
  type    = string
  default = "10.60.1.10"
}

variable "onprem_ad_domain_name" {
  type    = string
  default = "lab.contoso.local"
}

variable "onprem_ad_netbios_name" {
  type    = string
  default = "LAB"
}

variable "onprem_admin_username" {
  type    = string
  default = "labadmin"
}

variable "onprem_admin_password" {
  description = "Local + DSRM password for the lab DC. Required when enable_simulated_onprem = true."
  type        = string
  sensitive   = true
  default     = null
}

variable "onprem_vm_size" {
  type    = string
  default = "Standard_B2ms"
}

variable "onprem_admin_source_ip_cidr" {
  description = "CIDR allowed to RDP the lab DC. Restrict to your IP/32. Ignored when enable_public_ip = false."
  type        = string
  default     = "0.0.0.0/0"
}

variable "onprem_enable_public_ip" {
  description = "Set false to keep the lab DC fully private (use Bastion / Run Command instead)."
  type        = bool
  default     = true
}

