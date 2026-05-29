// Parameters file for Phase 1 (main.bicep)
using './main.bicep'

param baseName = 'acaprivate'
// location and acaSubnetId are passed via CLI --parameters
// Provide a placeholder here; the deploy script overrides it.
param acaSubnetId = ''

param containerImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param containerAppName = 'helloworld'
param tags = {
  environment: 'demo'
  purpose: 'aca-private-deployment'
}
