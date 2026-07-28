// Rayfin store scale test — bulk-load table_edges.json into the lineage-app
// backend and measure write throughput + k-hop read latency.
//
// The Rayfin data-plane requires a valid session. Provide auth via env:
//   RAYFIN_API_URL   e.g. https://<region>.pbidedicated.windows.net/.../appbackends/<id>
//   RAYFIN_PK        publishable key (pk-...)
//   RAYFIN_TOKEN     bearer token for the workload endpoint (from the portal
//                    session, or `az account get-access-token`), if required.
//
// Usage (Node 20+):
//   node loader.mjs --edges out/scale/table_edges.json --limit 2000 --concurrency 16
//
// NOTE: LineageEdge is an @authenticated entity, so anonymous writes are
// rejected. Fabric SSO only issues sessions inside the portal, so run this where
// you can reach the data-plane with a real session/token. It introspects the
// schema first, so it adapts to the generated create-mutation / query names.

import { readFileSync } from 'node:fs';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1]]);
    return acc;
  }, []),
);

const API = process.env.RAYFIN_API_URL;
const PK = process.env.RAYFIN_PK;
const TOKEN = process.env.RAYFIN_TOKEN;
if (!API) {
  console.error('Set RAYFIN_API_URL (and RAYFIN_PK / RAYFIN_TOKEN as needed).');
  process.exit(1);
}

const EDGES_FILE = args.edges ?? 'out/scale/table_edges.json';
const LIMIT = Number(args.limit ?? 2000);
const CONC = Number(args.concurrency ?? 16);
const ENDPOINT = `${API.replace(/\/$/, '')}/api/graphql`;

function headers() {
  const h = { 'Content-Type': 'application/json' };
  if (PK) h['X-Publishable-Key'] = PK;
  if (TOKEN) h['Authorization'] = `Bearer ${TOKEN}`;
  return h;
}

async function gql(query, variables) {
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ query, variables }),
  });
  const json = await res.json();
  if (json.errors) throw new Error(JSON.stringify(json.errors));
  return json.data;
}

// Discover the create mutation + list query names for LineageEdge.
async function discover() {
  const q = `{ __schema { mutationType { fields { name } } queryType { fields { name } } } }`;
  const d = await gql(q);
  const muts = d.__schema.mutationType.fields.map((f) => f.name);
  const queries = d.__schema.queryType.fields.map((f) => f.name);
  const create = muts.find((n) => /create.*lineageEdge/i.test(n)) ??
    muts.find((n) => /lineageEdge/i.test(n) && /create/i.test(n));
  const list = queries.find((n) => /lineageEdges/i.test(n)) ??
    queries.find((n) => /lineageEdge/i.test(n));
  if (!create || !list) {
    console.log('mutations:', muts.join(', '));
    console.log('queries:', queries.join(', '));
    throw new Error('Could not auto-detect create/list names — inspect the lists above.');
  }
  return { create, list };
}

async function pool(items, worker, concurrency) {
  let i = 0;
  let ok = 0;
  let fail = 0;
  await Promise.all(
    Array.from({ length: concurrency }, async () => {
      while (i < items.length) {
        const idx = i++;
        try {
          await worker(items[idx]);
          ok++;
        } catch (e) {
          fail++;
          if (fail <= 3) console.error('  write error:', String(e).slice(0, 160));
        }
      }
    }),
  );
  return { ok, fail };
}

async function main() {
  const all = JSON.parse(readFileSync(EDGES_FILE, 'utf-8'));
  const edges = all.slice(0, LIMIT);
  console.log(`Endpoint: ${ENDPOINT}`);
  console.log(`Loading ${edges.length} of ${all.length} edges, concurrency=${CONC}`);

  const { create, list } = await discover();
  console.log(`Using mutation "${create}", query "${list}"`);

  const mutation = `mutation($input: CreateLineageEdgeInput!) {
    ${create}(input: $input) { id }
  }`;

  const t0 = performance.now();
  const { ok, fail } = await pool(
    edges,
    (e) => gql(mutation, {
      input: {
        sourceQname: e.sourceQname, sourceType: e.sourceType,
        targetQname: e.targetQname, targetType: e.targetType,
        processName: e.processName, processType: e.processType,
        artifactRef: e.artifactRef, harvestedBySub: 'scale-loader',
        harvestedAt: e.harvestedAt,
      },
    }),
    CONC,
  );
  const dt = (performance.now() - t0) / 1000;
  console.log(`\nWrites: ok=${ok} fail=${fail} in ${dt.toFixed(1)}s (${(ok / dt).toFixed(0)}/s)`);

  // k-hop read proxy: fetch edges touching a specific source, time it.
  const focus = edges[0]?.sourceQname;
  if (focus) {
    const readQ = `query($q: String) {
      ${list}(filter: { sourceQname: { eq: $q } }) { items { id targetQname } }
    }`;
    const r0 = performance.now();
    try {
      const d = await gql(readQ, { q: focus });
      const n = d[list]?.items?.length ?? 0;
      console.log(`k-hop read (source=${focus}): ${n} rows in ${(performance.now() - r0).toFixed(0)} ms`);
    } catch (e) {
      console.log('read probe failed (filter arg may differ):', String(e).slice(0, 160));
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
