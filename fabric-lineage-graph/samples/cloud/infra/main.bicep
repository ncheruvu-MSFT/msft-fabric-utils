// =========================================================================
// fabric-lineage-graph / samples / cloud
//
// Slim provisioning of public-endpoint PaaS sources for live lineage tests:
//   * Azure SQL Server + DB    (Entra-only auth — MCAPS-compliant)
//   * Postgres Flex Server     (Entra-only auth)
//   * Cosmos DB SQL API
//
// Oracle: not provisioned (no first-party Azure PaaS). The harvester accepts a
//   BYO connection string via env (ORACLE_DSN). See README.
// Synapse: not provisioned. Synapse Serverless SQL views can be harvested by
//   the same mssql_live harvester — point it at the workspace SQL endpoint.
//
// Toggle `enablePrivateEndpoints=true` to flip the three sources off the
// public internet and onto a private VNet. See docs/private-endpoints.md.
// =========================================================================
targetScope = 'resourceGroup'

@description('Workload short name')
@maxLength(10)
param workload string = 'fbrlin'

@allowed([ 'dev', 'tst', 'prd' ])
param env string = 'dev'

@allowed([ 'cac', 'eus', 'eus2', 'wus2', 'wus3' ])
param regionCode string = 'cac'

param location string = resourceGroup().location

@maxLength(3)
param instance string = '001'

@description('Entra UPN to set as SQL/Postgres admin (Entra-only auth, MCAPS-required)')
param adminLogin string

@description('Entra object ID matching adminLogin')
param adminObjectId string

@description('Set true to disable public network access on all sources and create private endpoints')
param enablePrivateEndpoints bool = false

@description('Existing VNet resource id (required when enablePrivateEndpoints=true)')
param vnetId string = ''

@description('Existing subnet name inside vnetId (required when enablePrivateEndpoints=true)')
param peSubnetName string = ''

param tags object = {
  workload: workload
  env: env
  managedBy: 'bicep'
  purpose: 'lineage-validation'
}

var nm = {
  sql:      'sql-${workload}-${env}-${regionCode}-${instance}'
  sqlDb:    'sqldb-crm'
  pg:       'psql-${workload}-${env}-${regionCode}-${instance}'
  pgDb:     'hr'
  cosmos:   'cosmos-${workload}-${env}-${regionCode}-${uniqueString(resourceGroup().id)}'
  cosmosDb: 'telemetry'
}

var publicAccess = enablePrivateEndpoints ? 'Disabled' : 'Enabled'

// ----------------- Azure SQL Server (Entra-only) -----------------
module sqlServer 'br/public:avm/res/sql/server:0.20.0' = {
  name: 'sql-deploy'
  params: {
    name: nm.sql
    location: location
    tags: tags
    administrators: {
      administratorType: 'ActiveDirectory'
      azureADOnlyAuthentication: true
      login: adminLogin
      sid: adminObjectId
      tenantId: subscription().tenantId
      principalType: 'User'
    }
    publicNetworkAccess: publicAccess
    firewallRules: enablePrivateEndpoints ? [] : [
      { name: 'AllowAllAzureServices', startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
    ]
    databases: [
      {
        name: nm.sqlDb
        sku: { name: 'GP_S_Gen5_1', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
        autoPauseDelay: 60
        minCapacity: '0.5'
        maxSizeBytes: 32212254720
        zoneRedundant: false
        availabilityZone: -1
      }
    ]
    privateEndpoints: enablePrivateEndpoints ? [
      {
        name: 'pe-${nm.sql}'
        service: 'sqlServer'
        subnetResourceId: '${vnetId}/subnets/${peSubnetName}'
      }
    ] : []
  }
}

// ----------------- Postgres Flexible Server (Entra-only, native resource) -----------------
// The AVM module (db-for-postgre-sql/flexible-server) at 0.13.x doesn't expose
// authConfig.activeDirectoryAuth / passwordAuth. Use the native resource so we
// can enforce Entra-only auth (MCAPS rule: no password admin).
resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: nm.pg
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    network: { publicNetworkAccess: publicAccess }
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
      tenantId: subscription().tenantId
    }
  }

  resource adminEntra 'administrators@2024-08-01' = {
    name: adminObjectId
    properties: {
      principalType: 'User'
      principalName: adminLogin
      tenantId: subscription().tenantId
    }
  }

  resource pgDatabase 'databases@2024-08-01' = {
    name: nm.pgDb
    properties: {
      charset: 'UTF8'
      collation: 'en_US.utf8'
    }
  }

  resource fwAzure 'firewallRules@2024-08-01' = if (!enablePrivateEndpoints) {
    name: 'AllowAllAzure'
    properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
  }
}

// ----------------- Cosmos DB (SQL API) -----------------
module cosmos 'br/public:avm/res/document-db/database-account:0.11.3' = {
  name: 'cosmos-deploy'
  params: {
    name: nm.cosmos
    location: location
    tags: tags
    locations: [ { locationName: location, failoverPriority: 0, isZoneRedundant: false } ]
    capabilitiesToAdd: [ 'EnableServerless' ]
    networkRestrictions: {
      publicNetworkAccess: publicAccess
      ipRules: enablePrivateEndpoints ? [] : [ '0.0.0.0' ]
    }
    sqlDatabases: [
      {
        name: nm.cosmosDb
        containers: [
          { name: 'web_sessions', paths: [ '/sessionId' ] }
          { name: 'iot_telemetry', paths: [ '/deviceId' ] }
        ]
      }
    ]
    privateEndpoints: enablePrivateEndpoints ? [
      {
        name: 'pe-${nm.cosmos}'
        service: 'Sql'
        subnetResourceId: '${vnetId}/subnets/${peSubnetName}'
      }
    ] : []
  }
}

// =============== Outputs (consumed by seeders + harvesters) ===============
output sqlServerName string = nm.sql
output sqlServerFqdn string = '${nm.sql}${environment().suffixes.sqlServerHostname}'
output sqlDatabase   string = nm.sqlDb

output pgServerName  string = nm.pg
output pgServerFqdn  string = '${nm.pg}.postgres.database.azure.com'
output pgDatabase    string = nm.pgDb
output cosmosAccount string = nm.cosmos
output cosmosEndpoint string = 'https://${nm.cosmos}.documents.azure.com:443/'
output cosmosDatabase string = nm.cosmosDb
