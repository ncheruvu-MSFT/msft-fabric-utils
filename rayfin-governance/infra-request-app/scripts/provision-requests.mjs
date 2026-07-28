// Provisioning bridge: Rayfin GraphQL  ->  GitHub Issues
//
// Polls the infra-request-app Rayfin backend for APPROVED requests that have
// not yet been pushed to GitHub, opens a labelled GitHub issue for each, and
// stamps the request back to `Submitted` with the issue URL/number.
//
// Runs from GitHub Actions (.github/workflows/infra-request-provision.yml).
// No npm dependencies — uses Node 20+ global fetch.
//
// Required env:
//   RAYFIN_API_URL     base URL of the Rayfin backend (no trailing slash)
//   RAYFIN_API_TOKEN   bearer token whose claims map to the `pipeline` role
//                      (allowed to read all requests and update GitHub fields)
//   GITHUB_TOKEN       token with `issues: write` on GITHUB_REPOSITORY
//   GITHUB_REPOSITORY  "owner/repo" (provided by Actions automatically)
//   ISSUE_LABEL        optional, defaults to "infra-request"

const RAYFIN_API_URL = requireEnv('RAYFIN_API_URL').replace(/\/$/, '');
const RAYFIN_API_TOKEN = requireEnv('RAYFIN_API_TOKEN');
const GITHUB_TOKEN = requireEnv('GITHUB_TOKEN');
const GITHUB_REPOSITORY = requireEnv('GITHUB_REPOSITORY');
const ISSUE_LABEL = process.env.ISSUE_LABEL || 'infra-request';
const [OWNER, REPO] = GITHUB_REPOSITORY.split('/');

function requireEnv(name) {
  const v = process.env[name];
  if (!v) {
    console.error(`Missing required env var: ${name}`);
    process.exit(1);
  }
  return v;
}

const LIST_QUERY = `
  query ApprovedRequests {
    infraRequests {
      id
      requestType
      displayName
      environment
      domain
      capacitySku
      region
      targetCapacity
      justification
      costCenter
      status
      ownerSub
      approverSub
      githubIssueUrl
    }
  }
`;

const UPDATE_MUTATION = `
  mutation StampGithub($id: ID!, $item: UpdateInfraRequestInput!) {
    updateInfraRequest(id: $id, item: $item) { id }
  }
`;

async function rayfin(query, variables) {
  const res = await fetch(`${RAYFIN_API_URL}/api/graphql`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${RAYFIN_API_TOKEN}`,
    },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) {
    throw new Error(`Rayfin GraphQL ${res.status}: ${await res.text()}`);
  }
  const json = await res.json();
  if (json.errors) {
    throw new Error(`Rayfin GraphQL errors: ${JSON.stringify(json.errors)}`);
  }
  return json.data;
}

function issueBody(r) {
  const spec =
    r.requestType === 'Capacity'
      ? `- **SKU:** ${r.capacitySku ?? '—'}\n- **Region:** ${r.region ?? '—'}`
      : `- **Target capacity:** ${r.targetCapacity ?? '—'}`;
  return [
    `**Type:** ${r.requestType}`,
    `**Name:** \`${r.displayName}\``,
    `**Environment:** ${r.environment}`,
    r.domain ? `**Domain:** ${r.domain}` : null,
    r.costCenter ? `**Cost center:** ${r.costCenter}` : null,
    '',
    '### Spec',
    spec,
    '',
    '### Justification',
    r.justification ?? '',
    '',
    '---',
    `Requested by **${r.ownerSub}** · approved by **${r.approverSub ?? 'n/a'}**`,
    `Rayfin request id: \`${r.id}\``,
    '',
    '_Opened automatically by the infra-request provisioning workflow._',
  ]
    .filter((l) => l !== null)
    .join('\n');
}

async function createIssue(r) {
  const title = `[infra] ${r.requestType}: ${r.displayName} (${r.environment})`;
  const res = await fetch(
    `https://api.github.com/repos/${OWNER}/${REPO}/issues`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
      body: JSON.stringify({
        title,
        body: issueBody(r),
        labels: [ISSUE_LABEL, `infra:${r.requestType.toLowerCase()}`, `env:${r.environment}`],
      }),
    },
  );
  if (!res.ok) {
    throw new Error(`GitHub create issue ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

async function main() {
  const { infraRequests } = await rayfin(LIST_QUERY);
  const pending = (infraRequests ?? []).filter(
    (r) => r.status === 'Approved' && !r.githubIssueUrl,
  );

  if (pending.length === 0) {
    console.log('No approved requests awaiting GitHub issue creation.');
    return;
  }
  console.log(`Found ${pending.length} approved request(s) to submit.`);

  for (const r of pending) {
    try {
      const issue = await createIssue(r);
      await rayfin(UPDATE_MUTATION, {
        id: r.id,
        item: {
          status: 'Submitted',
          githubIssueUrl: issue.html_url,
          githubIssueNumber: issue.number,
          auditUpdatedAt: new Date().toISOString(),
        },
      });
      console.log(`✓ ${r.displayName} -> issue #${issue.number} (${issue.html_url})`);
    } catch (e) {
      console.error(`✗ ${r.displayName}: ${e.message}`);
      process.exitCode = 1;
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
