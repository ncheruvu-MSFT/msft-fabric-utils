using './main.bicep'

param workload      = 'fbrlin'
param env           = 'dev'
param regionCode    = 'cac'
param instance      = '001'

// REPLACE with your Entra account before deploying.
param adminLogin    = readEnvironmentVariable('ADMIN_LOGIN', '')
param adminObjectId = readEnvironmentVariable('ADMIN_OBJECT_ID', '')

// Public-endpoint demo by default. Flip to true + supply VNet/subnet for PE mode.
param enablePrivateEndpoints = false
param vnetId        = ''
param peSubnetName  = ''
