// Azure Databricks workspace (Premium, required for serverless SQL warehouses).
// Workspace base cost = $0 / mo; you pay only for DBUs consumed by the warehouse.
// Serverless SQL XSmall auto-stops after 10 min idle; demo cost is pennies.
//
// Kept as a separate bicep so it can be deployed independently of main.bicep.

@description('Workload short name')
param workload   string = 'fbrlin'

@description('Environment short code')
param env        string = 'dev'

@description('Azure region short code (e.g. cac)')
param regionCode string = 'cac'

@description('Azure region')
param location   string = resourceGroup().location

@description('Resource tags')
param tags       object = {
  workload: workload
  env: env
  managedBy: 'bicep'
}

var nm = '${workload}-${env}-${regionCode}-dbx'
// Databricks creates a managed RG to hold the data plane. It MUST not already exist.
var managedRgName = 'rg-${workload}-${env}-${regionCode}-dbx-managed'

resource workspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: nm
  location: location
  tags: tags
  sku: { name: 'premium' }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', managedRgName)
    parameters: {
      enableNoPublicIp: { value: false }
    }
  }
}

output workspaceName string = workspace.name
output workspaceUrl  string = 'https://${workspace.properties.workspaceUrl}'
output workspaceHost string = workspace.properties.workspaceUrl
output workspaceId   string = workspace.id
