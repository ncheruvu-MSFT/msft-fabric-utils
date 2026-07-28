using './main.bicep'

param location = 'eastus2'
param appBaseName = 'costguard'

// Start in dry-run. Flip to false after you've verified one nightly run in the log.
param dryRun = true

// Optional. Paste a Teams Incoming Webhook (or leave blank).
param teamsWebhookUrl = ''

// Optional. e.g. 'https://adb-1234567890123456.7.azuredatabricks.net' (leave blank to disable).
param databricksWorkspaceUrl = ''
