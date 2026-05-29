"""Create / update custom classification rules in Purview from YAML."""
from __future__ import annotations
import os, sys, yaml, requests, pathlib

PURVIEW_ACCOUNT = os.environ["PURVIEW_ACCOUNT"]
BASE = f"https://{PURVIEW_ACCOUNT}.purview.azure.com/scan"
API = "2023-09-01"

def token():
    t = os.environ.get("PURVIEW_ACCESS_TOKEN")
    if t: return t
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential().get_token("https://purview.azure.net/.default").token

def H():
    return {"Authorization": f"Bearer {token()}", "Content-Type": "application/json"}

def upsert_classification_rule(rule: dict):
    name = rule["name"]
    body = {
        "kind": "Custom",
        "properties": {
            "classificationName": name,
            "description": rule.get("description",""),
            "ruleStatus": "Enabled",
            "minimumPercentageMatch": int((rule.get("min_match_threshold",0.6)) * 100),
            "columnPatterns": [{"kind":"Regex","pattern": rule.get("column_pattern","")}] if rule.get("column_pattern") else [],
            "dataPatterns": [{"kind":"Regex","pattern": rule.get("regex_pattern","")}] if rule.get("regex_pattern") else [],
        }
    }
    url = f"{BASE}/classificationrules/{name}?api-version={API}"
    r = requests.put(url, headers=H(), json=body, timeout=30)
    print(f"  rule {name}: {r.status_code} {r.text[:160] if r.status_code>=400 else 'OK'}")

def main():
    yml = pathlib.Path("contracts/classifications/custom-classifications.yml")
    if not yml.exists():
        print(f"WARN {yml} not found, skipping"); return
    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    for c in data.get("classifications", []):
        upsert_classification_rule(c)
    print("Done classification rules.")

if __name__ == "__main__":
    main()
