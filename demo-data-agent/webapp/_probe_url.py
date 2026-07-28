"""Probe candidate Fabric Data Agent published-URL formats to find the working one."""
import sys
import requests
from azure.identity import AzureCliCredential

WS = "8cf25d6d-69b3-424b-ad49-bcb9fe4bc643"
AGENT = "af473ed0-27a2-4b40-8ebf-c1792b0950c6"  # Governed Analytics Assistant
API_VER = "2024-05-01-preview"

tok = AzureCliCredential().get_token("https://api.fabric.microsoft.com/.default").token
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
     "Accept": "application/json"}

candidates = [
    f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/aiskills/{AGENT}/aiassistant/openai",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/dataagents/{AGENT}/aiassistant/openai",
    f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/artifacts/{AGENT}/aiassistant/openai",
]

for base in candidates:
    url = f"{base}/assistants?api-version={API_VER}"
    try:
        r = requests.post(url, headers=H, json={"model": "not used"}, timeout=30)
        print(f"[{r.status_code}] POST {base}/assistants")
        if r.status_code in (200, 201):
            print("  -> WORKS. body:", r.text[:200])
            sys.exit(0)
        else:
            print("  ", r.text[:200])
    except Exception as e:
        print(f"[ERR] {base}: {e}")
