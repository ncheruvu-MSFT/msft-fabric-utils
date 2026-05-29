// =========================================================================
// Multi-source provisioning — CAF naming + Azure Verified Modules (AVM)
//
// CAF naming convention: {abbrev}-{workload}-{env}-{region}-{instance}
//   dbw   = Databricks workspace
//   sql   = Azure SQL Server
//   sqldb = Azure SQL Database
//   psql  = Postgres Flex Server
//   cosmos= Cosmos DB account
// Region code (canadacentral): cac
// =========================================================================
targetScope = 'resourceGroup'

@description('Workload short name')
@maxLength(10)
param workload string = 'fbrcdemo'

@allowed([ 'dev', 'tst', 'prd' ])
param env string = 'dev'

@allowed([ 'cac', 'eus', 'eus2', 'wus2', 'wus3' ])
param regionCode string = 'cac'

param location string = resourceGroup().location

@maxLength(3)
param instance string = '001'

@description('Entra UPN granted SQL/Postgres admin (Entra-only auth)')
param adminLogin string = 'ncheruvu@MngEnvMCAP219373.onmicrosoft.com'

@description('Entra object ID for SQL/Postgres admin')
param adminObjectId string = 'e5fde933-199e-4b54-917a-8e6741be6941'

@secure()
param pgPassword string

@description('Entra app object ID used by ADO WIF — gets Reader on sources')
param spnObjectId string = 'b6b2a4a5-b522-4fc4-94d4-05fc9823ff66'

param tags object = {
  workload: workload
  env: env
  managedBy: 'bicep-avm'
  costCenter: 'fabric-demo'
}

// -------------- CAF names --------------
var nm = {
  dbx:      'dbw-${workload}-${env}-${regionCode}-${instance}'
  sql:      'sql-${workload}-${env}-${regionCode}-${instance}'
  sqlDb:    'sqldb-${workload}-retail-${env}'
  pg:       'psql-${workload}-${env}-${regionCode}-${instance}'
  pgDb:     'hr'
  cosmos:   'cosmos-${workload}-${env}-${regionCode}-${uniqueString(resourceGroup().id)}'
  cosmosDb: 'telemetry'
}

// =============== AVM: Databricks Workspace ===============
module databricks 'br/public:avm/res/databricks/workspace:0.11.2' = {
  name: 'dbx-${env}-deploy'
  params: {
    name: nm.dbx
    location: location
    tags: tags
    skuName: 'premium'
    managedResourceGroupResourceId: subscriptionResourceId(
      'Microsoft.Resources/resourceGroups',
      '${resourceGroup().name}-${nm.dbx}-mrg'
    )
  }
}

// =============== AVM: Azure SQL Server (Entra-only) + DB ===============
module sqlServer 'br/public:avm/res/sql/server:0.20.0' = {
  name: 'sql-${env}-deploy'
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
    publicNetworkAccess: 'Enabled'
    firewallRules: [
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
  }
}

// =============== AVM: Postgres Flexible Server (Entra-only) ===============
module postgres 'br/public:avm/res/db-for-postgre-sql/flexible-server:0.13.0' = {
  name: 'pg-${env}-deploy'
  params: {
    name: nm.pg
    location: location
    tags: tags
    skuName: 'Standard_D2ds_v5'
    tier: 'GeneralPurpose'
    version: '16'
    availabilityZone: 1
    administratorLogin: 'pgadmin'
    administratorLoginPassword: pgPassword
    storageSizeGB: 32
    administrators: [
      {
        objectId: adminObjectId
        principalName: adminLogin
        principalType: 'User'
      }
    ]
    databases: [
      { name: nm.pgDb, charset: 'UTF8', collation: 'en_US.utf8' }
    ]
    firewallRules: [
      { name: 'AllowAllAzureServices', startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
    ]
    configurations: [
      { name: 'wal_level', value: 'logical', source: 'user-override' }
    ]
  }
}

// =============== AVM: Cosmos DB (Serverless) ===============
module cosmos 'br/public:avm/res/document-db/database-account:0.15.0' = {
  name: 'cosmos-${env}-deploy'
  params: {
    name: nm.cosmos
    location: location
    tags: tags
    capabilitiesToAdd: [ 'EnableServerless' ]
    defaultConsistencyLevel: 'Session'
    failoverLocations: [
      { locationName: location, failoverPriority: 0, isZoneRedundant: false }
    ]
    sqlDatabases: [
      {
        name: nm.cosmosDb
        containers: [
          {
            name: 'events'
            paths: [ '/customerId' ]
            kind: 'Hash'
          }
        ]
      }
    ]
  }
}

// =============== RBAC: SPN Reader on the resource group ===============
resource spnReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, spnObjectId, 'Reader')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7')
    principalId: spnObjectId
    principalType: 'ServicePrincipal'
  }
}

// =============== Outputs ===============
output databricksWorkspaceName string = nm.dbx
output databricksResourceId string = databricks.outputs.resourceId
output sqlServerFqdn string = '${nm.sql}${environment().suffixes.sqlServerHostname}'
output sqlServerName string = nm.sql
output sqlDatabase string = nm.sqlDb
output postgresFqdn string = postgres.outputs.fqdn
output postgresName string = nm.pg
output postgresDatabase string = nm.pgDb
output cosmosName string = nm.cosmos
output cosmosEndpoint string = 'https://${nm.cosmos}.documents.azure.com:443/'
output cosmosDatabase string = nm.cosmosDb
