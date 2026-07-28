# Rayfin Governance — App Template

A shareable starting point for building **customer-ready governance apps on
Microsoft Fabric Apps (Rayfin)**. Every app produced from this template ships
with a premium Fluent UI v9 look and a **"Rayfin app"** badge in the header that
signals it is built on Fabric Apps.

There are two ways to use it, depending on how much you want pre-built.

---

## Option A — Clone a proven app (fastest, recommended for demos)

The five apps in [`rayfin-governance/`](../) are complete, deploy-tested Rayfin
apps. The scaffolder copies one into a new, renamed app:

```powershell
# from rayfin-governance/template
./New-RayfinGovernanceApp.ps1 -Name contoso-glossary-app -From glossary-app -Install
```

`-From` can be any of: `glossary-app`, `lineage-app`, `sdlc-governance-app`,
`data-agent-governance-app`, `infra-request-app`.

The script:

- copies the app (excluding `node_modules`, `dist`, logs and local secrets),
- clears the recorded Fabric deployment so the new app provisions fresh,
- rewrites the name in `package.json` and `rayfin/rayfin.yml`,
- optionally runs `npm install`.

Then:

```powershell
cd contoso-glossary-app
npm run dev                         # local preview at http://localhost:5173
$env:FABRIC_WORKSPACE_ID = '<workspace-guid>'
$env:FABRIC_CAPACITY_ID  = '<capacity-guid>'
rayfin login --tenant <tenant-guid>
rayfin up --yes --workspace-id <workspace-guid>
```

> The backing **Fabric capacity must be running** before `rayfin up`. Resume a
> paused capacity with:
> `az resource invoke-action -g <rg> -n <capacity> --resource-type Microsoft.Fabric/capacities --action resume`

---

## Option B — Start from the official scaffolder + apply the branding kit

For a clean, up-to-date Rayfin baseline (correct `tsconfig` with
`ESNext.Decorators`, current SDK versions), use the official generator, then drop
in the branding kit for the premium look and Rayfin badge:

```powershell
npm create @microsoft/rayfin@latest my-governance-app
cd my-governance-app
# copy the branding kit into src/
Copy-Item ../rayfin-governance/template/branding/*.ts*  ./src/
```

Then in `src/main.tsx` use the shared theme:

```tsx
import { FluentProvider } from '@fluentui/react-components';
import { governanceLightTheme } from './theme';
// <FluentProvider theme={governanceLightTheme}> ... </FluentProvider>
```

And in `src/App.tsx` use the header + styles:

```tsx
import { AppHeader, useBrandStyles, StatCard } from './branding';
import { BookDatabaseRegular } from '@fluentui/react-icons';

export function App() {
  const brand = useBrandStyles();
  return (
    <div className={brand.root}>
      <AppHeader
        icon={<BookDatabaseRegular />}
        title="Glossary"
        subtitle="Microsoft Fabric · Data governance"
        source="seed"
      />
      <main className={brand.content}>
        <div className={brand.statsRow}>
          <StatCard label="Total terms" value={42} />
          {/* ...grids use brand.gridCard... */}
        </div>
      </main>
    </div>
  );
}
```

---

## What's in the branding kit

| File | Purpose |
|------|---------|
| [`branding/theme.ts`](./branding/theme.ts) | 16-stop Fabric-aligned brand ramp, light/dark themes, and `HEADER_GRADIENT`. Re-brand by editing the ramp. |
| [`branding/branding.tsx`](./branding/branding.tsx) | `useBrandStyles` (gradient header, elevated stat cards, brand accents), `AppHeader`, `RayfinPill` (the "Rayfin app" badge), `SourceBadge`, `StatCard`. |

## Re-branding for a customer

1. Edit the 16 hex stops in `branding/theme.ts` (Fluent Theme Designer:
   https://react.fluentui.dev/?path=/docs/theme-theme-designer--docs).
2. Change the `AppHeader` `title` / `subtitle`.
3. Keep `<RayfinPill />` so the app is clearly identified as a Rayfin app, or
   remove it if the customer prefers unbranded.

## Security notes (carry over from the repo conventions)

- The static frontend is **public** — never embed secrets or policy data.
- Every Rayfin entity needs an explicit permission decorator (`@role` /
  `@authenticated` / `@anonymous`).
- Keep `allowedRedirectUris` in `rayfin.yml` scoped to your app's origin.
- Fabric SSO (Entra) works only inside the Fabric portal; email/password is for
  local dev only.
