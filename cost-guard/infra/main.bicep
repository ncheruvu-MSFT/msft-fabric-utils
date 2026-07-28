// Cost Guard — subscription-scoped deployment.
// Creates: RG, custom RBAC role, role assignment, and (via module) Function App stack.
targetScope = 'subscription'

@description('Azure region')
param location string = 'eastus2'

@description('Resource group name')
param resourceGroupName string = 'rg-cost-guard-${location}-01'

@description('Function app base name (used to build a globally unique name)')
param appBaseName string = 'costguard'

@description('When true, the function only logs intentions and does not stop anything.')
param dryRun bool = true

@description('Teams Incoming Webhook URL (leave blank to disable notifications)')
@secure()
param teamsWebhookUrl string = ''

@description('Databricks workspace URL e.g. https://adb-1234.5.azuredatabricks.net (blank to disable)')
param databricksWorkspaceUrl string = ''

var uniq = uniqueString(subscription().id, resourceGroupName, appBaseName)
var functionAppName = toLower('${appBaseName}-${uniq}')
var storageName = toLower('${appBaseName}sa${take(uniq, 6)}')
var planName = 'plan-${appBaseName}-${uniq}'
var aiName = 'ai-${appBaseName}-${uniq}'
var lawName = 'law-${appBaseName}-${uniq}'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    workload: 'cost-guard'
    KeepRunning: 'true' // never auto-stop the cost-guard's own RG resources
  }
}

// Custom subscription-scoped role with least privilege for what we touch.
var costGuardRoleName = guid(subscription().id, 'CostGuardOperator')

resource costGuardRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: costGuardRoleName
  properties: {
    roleName: 'Cost Guard Operator (${subscription().displayName})'
    description: 'Read all + suspend Fabric capacities + stop PG Flex servers + read Databricks workspaces.'
    type: 'CustomRole'
    permissions: [
      {
        actions: [
          'Microsoft.Resources/subscriptions/read'
          'Microsoft.Resources/subscriptions/resourceGroups/read'
          'Microsoft.Resources/subscriptions/resources/read'
          'Microsoft.Resources/resources/read'
          'Microsoft.Fabric/capacities/read'
          'Microsoft.Fabric/capacities/suspend/action'
          'Microsoft.DBforPostgreSQL/flexibleServers/read'
          'Microsoft.DBforPostgreSQL/flexibleServers/stop/action'
          'Microsoft.Databricks/workspaces/read'
        ]
        notActions: []
        dataActions: []
        notDataActions: []
      }
    ]
    assignableScopes: [
      subscription().id
    ]
  }
}

module appStack 'app.bicep' = {
  scope: rg
  name: 'cost-guard-app'
  params: {
    location: location
    functionAppName: functionAppName
    storageName: storageName
    planName: planName
    aiName: aiName
    lawName: lawName
    subscriptionId: subscription().subscriptionId
    dryRun: dryRun
    teamsWebhookUrl: teamsWebhookUrl
    databricksWorkspaceUrl: databricksWorkspaceUrl
  }
}

resource roleAssign 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, costGuardRoleName, functionAppName)
  properties: {
    principalId: appStack.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: costGuardRole.id
  }
}

output functionAppName string = appStack.outputs.functionAppName
output resourceGroupName string = rg.name
output principalId string = appStack.outputs.principalId
