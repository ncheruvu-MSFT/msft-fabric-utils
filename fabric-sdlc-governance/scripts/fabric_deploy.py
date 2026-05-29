"""Thin CLI wrapper around fabric-cicd for use in ADO pipelines.

Picks up federated token / azure identity from the AzureCLI@2 task env.
"""
from __future__ import annotations
import argparse, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-name", required=True)
    ap.add_argument("--items-path", required=True)
    ap.add_argument("--environment", required=True)
    ap.add_argument("--item-types", default="Notebook,Lakehouse,DataPipeline,Warehouse")
    args = ap.parse_args()

    try:
        from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items
    except ImportError:
        print("fabric-cicd not installed (expected in pipeline runtime)"); sys.exit(2)

    # AzureCLI@2 leaves an authenticated `az` session in the agent; reuse it.
    from azure.identity import AzureCliCredential
    cred = AzureCliCredential()

    ws = FabricWorkspace(
        workspace_name=args.workspace_name,
        repository_directory=args.items_path,
        item_type_in_scope=[t.strip() for t in args.item_types.split(",") if t.strip()],
        environment=args.environment,
        token_credential=cred,
    )
    publish_all_items(ws)
    unpublish_all_orphan_items(ws)
    print(f"[fabric-cicd] deployed → {args.workspace_name} ({args.environment})")

if __name__ == "__main__":
    main()
