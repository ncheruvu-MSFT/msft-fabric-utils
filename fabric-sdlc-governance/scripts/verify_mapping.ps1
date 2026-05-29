$tok = az account get-access-token --resource https://purview.azure.net --query accessToken -o tsv
$h = @{ Authorization = "Bearer $tok" }
$base = "https://62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68-api.purview-service.microsoft.com"
foreach ($id in @("d2d4dde1-18dc-4588-8a99-7fb30e998a4e","c21282c3-0312-403c-b8c0-a8c4da1543f7","6c2396e6-97c6-4263-accf-d36ae96e6a42","c0ffee3f-8458-4de5-ace9-502ce6608aee")) {
  $r = Invoke-RestMethod -Uri "$base/datagovernance/catalog/businessdomains/$id`?api-version=2026-03-20-preview" -Headers $h
  Write-Host ("`n=== {0} ===" -f $r.name)
  $r.domains | ConvertTo-Json -Depth 6
}
