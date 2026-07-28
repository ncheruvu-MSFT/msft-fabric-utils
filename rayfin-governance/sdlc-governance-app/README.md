# sdlc-governance-app

Rayfin port of the control-plane state currently maintained as flat files
under [fabric-sdlc-governance](../../fabric-sdlc-governance) (the YAML
contracts, `out_alldomains.txt`, `.workflows.json`, etc.).

## Entities

| Entity | Replaces |
|---|---|
| `Domain` | [domains.yml](../../fabric-sdlc-governance/contracts/governance/domains.yml) tree (`name`, `type`, parent, env, fabric workspace, purview collection) |
| `CriticalDataElement` | [critical_data_elements.yml](../../fabric-sdlc-governance/contracts/governance/critical_data_elements.yml) |
| `Workspace` | `.workspaces.json` |
| `AttestationRun` | append-only output from ADO pipelines (`scripts/*_apply*.py` runs) |

## Authorization model

- All authenticated read.
- `governance-admin` creates/updates Domains and Workspaces.
- `domain-steward` creates/updates CDEs.
- `pipeline` role (issued to ADO SP) can `create` AttestationRun rows; only
  `governance-admin` can update or delete them.

## Pipeline integration

ADO YAML calls the GraphQL endpoint with a Fabric SSO bearer token:

```yaml
- bash: |
    curl -fsS -X POST "$RAYFIN_API_URL/api/graphql" \
      -H "Authorization: Bearer $BEARER" \
      -H "Content-Type: application/json" \
      -d "$(jq -c -n --arg ws "$(WORKSPACE_ID)" --arg pol PrivateLink-Enforced \
            '{query:"mutation($ws:String!,$pol:String!){createAttestationRun(input:{workspaceId:$ws,policyName:$pol,result:\"PASS\",pipelineRunUrl:\"$(Build.BuildUri)\",commitSha:\"$(Build.SourceVersion)\",submittedBySub:\"pipeline\",runAt:\"$(date -u +%FT%TZ)\"}){id}}", variables:{ws:$ws,pol:$pol}}')"
  env:
    BEARER: $(FABRIC_SSO_TOKEN)
```

## Migration path

1. Stand up the app empty in dev workspace.
2. One-off script: read each YAML in `contracts/` → POST GraphQL mutations to
   seed `Domain` / `CriticalDataElement` rows (the YAML stays as the
   declarative source until you cut over).
3. Repoint pipelines from writing flat files to calling the GraphQL endpoint.
4. Decommission `out_alldomains.txt` and the loose `.log` files.
