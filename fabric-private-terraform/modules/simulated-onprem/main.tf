################################################################################
# Simulated on-prem module — partial AVM
#
# AVM-wrapped:
#   - Azure/avm-res-network-virtualnetwork/azurerm  (~> 0.17) for VNet + subnets + peering
#   - Azure/avm-res-network-networksecuritygroup/azurerm (~> 0.5) for the NSG
#   - Azure/avm-res-network-publicipaddress/azurerm (~> 0.2) for the optional PIP
#
# Kept native (intentional):
#   - azurerm_network_interface (the static IP allocation pattern is direct)
#   - azurerm_windows_virtual_machine
#   - azurerm_virtual_machine_extension (the UTF-16LE base64 bootstrap invoker
#     pattern is fragile; native keeps the JSON-encoded protected_settings path
#     stable). AVM compute/virtualmachine 0.21 nests extensions differently and
#     swapping it risks breaking the AD DS install.
#
# Reverse peering is now driven by the AVM VNet `peerings.create_reverse_peering`
# flag, so `var.hub_vnet_name` is no longer used but is kept in variables.tf
# for backwards compatibility.
################################################################################

locals {
  vm_name        = "vm-${var.name_prefix}-dc"
  nic_name       = "nic-${var.name_prefix}-dc"
  pip_name       = "pip-${var.name_prefix}-dc"
  nsg_name       = "nsg-${var.name_prefix}-onprem"
  vnet_name      = "vnet-${var.name_prefix}-onprem"
  computer_name  = "labdc01"
  bootstrap_path = "${path.module}/scripts/install-ad-and-forwarders.ps1"
}

# -------------------- NSG (AVM) --------------------

module "nsg" {
  source  = "Azure/avm-res-network-networksecuritygroup/azurerm"
  version = "~> 0.5"

  name                = local.nsg_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  enable_telemetry    = false

  security_rules = {
    allow_rdp_from_admin = {
      name                       = "allow-rdp-from-admin"
      access                     = var.enable_public_ip ? "Allow" : "Deny"
      direction                  = "Inbound"
      priority                   = 200
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "3389"
      source_address_prefix      = var.admin_source_ip_cidr
      destination_address_prefix = "*"
    }
    deny_all_other_internet_inbound = {
      name                       = "deny-all-other-internet-inbound"
      access                     = "Deny"
      direction                  = "Inbound"
      priority                   = 4096
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }
  }
}

# -------------------- VNet, subnets, peering (AVM) --------------------

module "vnet" {
  source  = "Azure/avm-res-network-virtualnetwork/azurerm"
  version = "~> 0.17"

  name             = local.vnet_name
  location         = var.location
  parent_id        = var.resource_group_id
  address_space    = toset(var.vnet_address_space)
  tags             = var.tags
  enable_telemetry = false

  # Spoke uses the DC as its DNS server so peered resolution of Fabric
  # private FQDNs flows through the AD-integrated conditional forwarders.
  dns_servers = {
    dns_servers = [var.dc_static_ip]
  }

  subnets = {
    dc = {
      name             = "snet-dc"
      address_prefixes = [var.subnet_dc_prefix]
      network_security_group = {
        id = module.nsg.resource_id
      }
    }
    clients = {
      name             = "snet-clients"
      address_prefixes = [var.subnet_clients_prefix]
      network_security_group = {
        id = module.nsg.resource_id
      }
    }
  }

  peerings = {
    to_hub = {
      name                                 = "peer-onprem-to-hub"
      remote_virtual_network_resource_id   = var.hub_vnet_id
      allow_forwarded_traffic              = true
      allow_virtual_network_access         = true
      allow_gateway_transit                = false
      use_remote_gateways                  = false
      create_reverse_peering               = true
      reverse_name                         = "peer-hub-to-onprem"
      reverse_allow_forwarded_traffic      = true
      reverse_allow_virtual_network_access = true
      reverse_allow_gateway_transit        = false
      reverse_use_remote_gateways          = false
    }
  }
}

# -------------------- Public IP (optional, AVM) --------------------

module "pip" {
  source  = "Azure/avm-res-network-publicipaddress/azurerm"
  version = "~> 0.2"

  count = var.enable_public_ip ? 1 : 0

  name                = local.pip_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  allocation_method = "Static"
  sku               = "Standard"
  enable_telemetry  = false
}

# -------------------- NIC + VM (native, intentional) --------------------

resource "azurerm_network_interface" "dc" {
  name                = local.nic_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  ip_configuration {
    name                          = "ipcfg"
    subnet_id                     = module.vnet.subnets["dc"].resource_id
    private_ip_address_allocation = "Static"
    private_ip_address            = var.dc_static_ip
    public_ip_address_id          = var.enable_public_ip ? module.pip[0].resource_id : null
  }
}

resource "azurerm_windows_virtual_machine" "dc" {
  name                = local.vm_name
  computer_name       = local.computer_name
  location            = var.location
  resource_group_name = var.resource_group_name
  size                = var.vm_size
  admin_username      = var.admin_username
  admin_password      = var.admin_password
  network_interface_ids = [
    azurerm_network_interface.dc.id
  ]
  tags = var.tags

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2022-datacenter-azure-edition"
    version   = "latest"
  }

  provision_vm_agent = true
}

# -------------------- Custom Script Extension: install AD DS + DNS --------------------

# UTF-16LE base64 — required by powershell.exe -EncodedCommand.
locals {
  bootstrap_script_b64 = textencodebase64(
    file(local.bootstrap_path),
    "UTF-16LE"
  )

  bootstrap_invoker = <<-PWSH
    $args = '-DomainName "${var.ad_domain_name}" -NetBiosName "${var.ad_netbios_name}" -SafeModePassword "${var.admin_password}" -ResolverIp "${var.dns_resolver_inbound_ip}" -FabricTenantId "${var.fabric_tenant_id}"'
    $script = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('${local.bootstrap_script_b64}'))
    $tmp = "$env:TEMP\install-ad.ps1"
    Set-Content -Path $tmp -Value $script -Encoding UTF8 -Force
    Invoke-Expression "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$tmp`" $args"
  PWSH

  bootstrap_invoker_b64 = textencodebase64(local.bootstrap_invoker, "UTF-16LE")
}

resource "azurerm_virtual_machine_extension" "ad_install" {
  name                       = "InstallADDS"
  virtual_machine_id         = azurerm_windows_virtual_machine.dc.id
  publisher                  = "Microsoft.Compute"
  type                       = "CustomScriptExtension"
  type_handler_version       = "1.10"
  auto_upgrade_minor_version = true

  protected_settings = jsonencode({
    commandToExecute = "powershell.exe -ExecutionPolicy Bypass -NoProfile -EncodedCommand ${local.bootstrap_invoker_b64}"
  })
}
