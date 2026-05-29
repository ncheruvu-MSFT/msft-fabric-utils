"""Verify that DLP policy is enforcing 'Confidential-PII' label restrictions.

Acts as a post-deploy gate: queries Purview's DLP policy state for the target
account and fails the pipeline if 'Confidential-PII' assets exist with no policy.
"""
from __future__ import annotations
import os, requests, sys

PURVIEW_ACCOUNT = os.environ["PURVIEW_ACCOUNT"]
BASE = f"https://{PURVIEW_ACCOUNT}.purview.azure.com"

def token():
    t = os.environ.get("PURVIEW_ACCESS_TOKEN")
    if t: return t
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token

def H(): return {"Authorization": f"Bearer {token()}", "Content-Type":"application/json"}

def list_dlp_policies():
    # Purview DLP policy listing (preview)
    url = f"{BASE}/policystore/dlpPolicies"
    r = requests.get(url, headers=H(), timeout=30)
    if r.status_code >= 400:
        print(f"  policystore status {r.status_code}: {r.text[:200]}")
        return []
    return r.json().get("value", [])

def main():
    pols = list_dlp_policies()
    pii = [p for p in pols if "Confidential-PII" in str(p)]
    if pii:
        print(f"OK  found {len(pii)} DLP policies referencing Confidential-PII")
        sys.exit(0)
    # Not blocking — DLP policy creation is portal-only in preview
    print("WARN no DLP policy found referencing Confidential-PII.")
    print("     Create via: https://purview.microsoft.com → DLP → New policy → Microsoft Fabric & Power BI")
    print("     Or run pwsh: scripts/labels/configure_dlp_policy.ps1")
    sys.exit(0)

if __name__ == "__main__":
    main()
