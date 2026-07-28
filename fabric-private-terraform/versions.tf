terraform {
  # Bumped to 1.9 for AVM module compatibility (avm-res-network-virtualnetwork >= 0.17 etc.).
  required_version = ">= 1.9.0, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.14.0, < 5.0.0"
    }
    azapi = {
      # Bumped to ~> 2.4 — required by Azure/avm-res-network-virtualnetwork/azurerm 0.17+.
      source  = "Azure/azapi"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }
}
