// Minimal supporting infra for the Fabric lineage app.
//
// Fabric items (lakehouse, notebooks, pipeline, data app, UDF) are created
// via the Fabric REST API by infra/deploy_fabric_items.py — they cannot be
// declared in Bicep today. This template provisions the *external* bits:
//
//   * Key Vault to hold the Purview SPN cert/secret and any harvester creds
//   * User-assigned managed identity for the deploy pipeline
//
// Wire the MI's object id into Fabric workspace admins manually (or via
// fabric-cicd) after deployment.

@description('Location for the supporting resources')
param location string = resourceGroup().location

@description('Short name prefix for the resources')
param namePrefix string = 'fblineage'

@description('Tenant id (used by Key Vault access policies)')
param tenantId string = subscription().tenantId

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-mi'
  location: location
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}-kv'
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// Grant the MI Key Vault Secrets User
resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(kv.id, uami.id, 'kv-secrets-user')
  scope: kv
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
    )
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output managedIdentityId string = uami.id
output managedIdentityPrincipalId string = uami.properties.principalId
output keyVaultName string = kv.name
output keyVaultUri string = kv.properties.vaultUri
