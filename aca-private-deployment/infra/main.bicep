// ============================================================================
// Phase 1: Azure Container Apps – Environment & Hello-World App
// ============================================================================
// Deploys:
//   1. Log Analytics workspace (required by ACA environment)
//   2. Azure Container Apps Environment (internal-only, VNet-injected)
//   3. Hello-World container app
//
// Prerequisites (must exist BEFORE deployment):
//   - VNet with an ACA infrastructure subnet (/23 min, delegated to
//     Microsoft.App/environments)
//   - PE subnet (can be in a different VNet/subscription/resource group)
//
// Phase 2 (private-dns.bicep) creates the Private DNS Zone & Private Endpoint.
// Public network access is disabled via CLI after deployment (see deploy.ps1).
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------
@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Base name used to derive resource names')
@minLength(3)
@maxLength(20)
param baseName string = 'acaprivate'

@description('Resource ID of the subnet for ACA infrastructure (must have Microsoft.App/environments delegation, /23 minimum). Must already exist.')
param acaSubnetId string

@description('Container image to deploy (hello-world)')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container app name')
param containerAppName string = 'helloworld'

@description('Workload profile name for the dedicated compute tier')
param workloadProfileName string = 'aca-d4'

@description('Workload profile SKU (D4, D8, D16, D32, E4, E8, E16, E32)')
@allowed([
  'D4'
  'D8'
  'D16'
  'D32'
  'E4'
  'E8'
  'E16'
  'E32'
])
param workloadProfileSize string = 'D4'

@description('Minimum number of workload profile instances')
@minValue(0)
param workloadProfileMinCount int = 1

@description('Maximum number of workload profile instances')
@minValue(1)
param workloadProfileMaxCount int = 3

@description('Tags applied to every resource')
param tags object = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------
var uniqueSuffix = uniqueString(resourceGroup().id, baseName)
var logAnalyticsName = '${baseName}-la-${uniqueSuffix}'
var acaEnvName = '${baseName}-env-${uniqueSuffix}'

// ---------------------------------------------------------------------------
// 1. Log Analytics Workspace (required by ACA)
// ---------------------------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// ---------------------------------------------------------------------------
// 2. Azure Container Apps Environment – Internal Only
// ---------------------------------------------------------------------------
resource acaEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: acaEnvName
  location: location
  tags: tags
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: acaSubnetId
      internal: true // ← makes the environment internal-only (no public IP)
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: workloadProfileName
        workloadProfileType: workloadProfileSize
        minimumCount: workloadProfileMinCount
        maximumCount: workloadProfileMaxCount
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// 3. Hello-World Container App
// ---------------------------------------------------------------------------
resource helloApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: acaEnv.id
    workloadProfileName: workloadProfileName
    configuration: {
      ingress: {
        external: true // "external" within the internal environment → reachable on VNet
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'helloworld'
          image: containerImage
          resources: {
            cpu: json('2')
            memory: '4Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs – consumed by Phase 2 (private-dns.bicep) and deploy.ps1
// ---------------------------------------------------------------------------
output acaEnvironmentId string = acaEnv.id
output acaEnvironmentName string = acaEnv.name
output acaEnvironmentDefaultDomain string = acaEnv.properties.defaultDomain
output acaEnvironmentStaticIp string = acaEnv.properties.staticIp
output containerAppFqdn string = helloApp.properties.configuration.ingress.fqdn
