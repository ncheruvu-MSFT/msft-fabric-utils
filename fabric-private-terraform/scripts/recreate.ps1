#requires -Version 5.1
<#
.SYNOPSIS
  Recreate the fabric-private-terraform stack with a new CAF instance suffix.

.DESCRIPTION
  The Fabric capacity name is reserved for 24 hours after deletion. This script
  works around that by bumping `var.instance` (01 -> 02 -> 03 ...) so every
  CAF-derived resource name (rg-fabpl-demo-eus2-NN, fab-fabpl-demo-eus2-NN, ...)
  is fresh on the next apply.

  Flow:
    1. Reads current `instance` from terraform.tfvars (defaults to "01").
    2. Plans + applies a destroy at the current instance (skipped with -SkipDestroy).
    3. Bumps `instance` in terraform.tfvars (or creates the file from the example).
    4. Plans + applies the new instance.
    5. Prints the resulting `caf_naming` output.

.PARAMETER WorkingDir
  Path to the terraform stack root. Defaults to the script's parent directory.

.PARAMETER NewInstance
  Explicit instance value to bump to (e.g. "03"). If omitted, increments the
  current value by 1, zero-padded to 2 digits.

.PARAMETER SkipDestroy
  Skip the destroy step (useful when the previous stack is already gone but the
  Fabric capacity name reservation is still active).

.PARAMETER AutoApprove
  Pass -auto-approve to terraform apply/destroy. Without this, terraform will
  prompt interactively for each apply.

.EXAMPLE
  ./scripts/recreate.ps1

.EXAMPLE
  ./scripts/recreate.ps1 -NewInstance 05 -AutoApprove

.EXAMPLE
  ./scripts/recreate.ps1 -SkipDestroy
#>
[CmdletBinding()]
param(
  [string]$WorkingDir = (Split-Path -Parent $PSScriptRoot),
  [string]$NewInstance,
  [switch]$SkipDestroy,
  [switch]$AutoApprove
)

$ErrorActionPreference = 'Stop'

function Get-CurrentInstance {
  param([string]$TfvarsPath)
  if (-not (Test-Path $TfvarsPath)) { return '01' }
  $line = (Get-Content -Raw $TfvarsPath) -split "`n" | Where-Object { $_ -match '^\s*instance\s*=' } | Select-Object -First 1
  if (-not $line) { return '01' }
  if ($line -match '"([0-9]{2,3})"') { return $Matches[1] }
  return '01'
}

function Set-Instance {
  param([string]$TfvarsPath, [string]$Value)
  if (-not (Test-Path $TfvarsPath)) {
    $example = Join-Path $WorkingDir 'terraform.tfvars.example'
    if (Test-Path $example) {
      Copy-Item $example $TfvarsPath
      Write-Host "Created terraform.tfvars from terraform.tfvars.example" -ForegroundColor Yellow
    } else {
      Set-Content -Path $TfvarsPath -Value "" -Encoding UTF8
    }
  }
  $content = Get-Content -Raw $TfvarsPath
  if ($content -match '(?m)^\s*instance\s*=') {
    $new = [regex]::Replace($content, '(?m)^\s*instance\s*=.*$', "instance = `"$Value`"")
  } else {
    $new = $content.TrimEnd() + "`r`n" + "instance = `"$Value`"" + "`r`n"
  }
  Set-Content -Path $TfvarsPath -Value $new -Encoding UTF8 -NoNewline
}

function Invoke-Terraform {
  param([string[]]$Args, [string]$Cwd)
  Push-Location $Cwd
  try {
    & terraform @Args
    if ($LASTEXITCODE -ne 0) { throw "terraform $($Args -join ' ') failed (exit $LASTEXITCODE)" }
  } finally {
    Pop-Location
  }
}

# -----------------------------------------------------------------------------

$WorkingDir = (Resolve-Path $WorkingDir).Path
$tfvars     = Join-Path $WorkingDir 'terraform.tfvars'

Write-Host ""
Write-Host "=== fabric-private-terraform: recreate ===" -ForegroundColor Cyan
Write-Host "WorkingDir : $WorkingDir"
Write-Host "tfvars     : $tfvars"

# Step 0: confirm terraform is on PATH.
$tf = Get-Command terraform -ErrorAction SilentlyContinue
if (-not $tf) { throw "terraform CLI not found on PATH." }

# Step 1: figure out current + next instance.
$current = Get-CurrentInstance -TfvarsPath $tfvars
if (-not $NewInstance) {
  $n = [int]$current + 1
  $NewInstance = '{0:00}' -f $n
}
Write-Host "current instance : $current"
Write-Host "next instance    : $NewInstance"
Write-Host ""

# Step 2: terraform init -upgrade (safe to run repeatedly).
Write-Host "--- terraform init -upgrade ---" -ForegroundColor Cyan
Invoke-Terraform -Args @('init', '-upgrade') -Cwd $WorkingDir

# Step 3: destroy the current stack (unless skipped).
if (-not $SkipDestroy) {
  Write-Host ""
  Write-Host "--- terraform plan -destroy (instance=$current) ---" -ForegroundColor Cyan
  $destroyPlan = Join-Path $WorkingDir 'destroy.tfplan'
  Invoke-Terraform -Args @('plan', '-destroy', '-out', $destroyPlan) -Cwd $WorkingDir

  if (-not $AutoApprove) {
    $confirm = Read-Host "Apply DESTROY plan above? Type 'yes' to continue"
    if ($confirm -ne 'yes') { Write-Host "Aborted by user before destroy." -ForegroundColor Yellow; return }
  }

  Write-Host "--- terraform apply destroy.tfplan ---" -ForegroundColor Cyan
  Invoke-Terraform -Args @('apply', $destroyPlan) -Cwd $WorkingDir
  Remove-Item -ErrorAction SilentlyContinue $destroyPlan
} else {
  Write-Host "Skipping destroy (per -SkipDestroy)." -ForegroundColor Yellow
}

# Step 4: bump instance in tfvars.
Write-Host ""
Write-Host "--- bump instance in terraform.tfvars to $NewInstance ---" -ForegroundColor Cyan
Set-Instance -TfvarsPath $tfvars -Value $NewInstance
Write-Host "terraform.tfvars updated."

# Step 5: plan + apply the new instance.
Write-Host ""
Write-Host "--- terraform plan (instance=$NewInstance) ---" -ForegroundColor Cyan
$applyPlan = Join-Path $WorkingDir 'apply.tfplan'
Invoke-Terraform -Args @('plan', '-out', $applyPlan) -Cwd $WorkingDir

if (-not $AutoApprove) {
  $confirm = Read-Host "Apply CREATE plan above? Type 'yes' to continue"
  if ($confirm -ne 'yes') { Write-Host "Aborted by user before apply." -ForegroundColor Yellow; return }
}

Write-Host "--- terraform apply apply.tfplan ---" -ForegroundColor Cyan
Invoke-Terraform -Args @('apply', $applyPlan) -Cwd $WorkingDir
Remove-Item -ErrorAction SilentlyContinue $applyPlan

# Step 6: dump the new caf_naming output.
Write-Host ""
Write-Host "--- new CAF names (caf_naming output) ---" -ForegroundColor Cyan
Invoke-Terraform -Args @('output', '-json', 'caf_naming') -Cwd $WorkingDir

Write-Host ""
Write-Host "Done. Stack recreated at instance=$NewInstance." -ForegroundColor Green
