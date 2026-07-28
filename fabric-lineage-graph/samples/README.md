# Validation samples

Three tiers to validate the harvester + graph + label-propagation + DLP gate.

| Tier | Artifacts | What it proves |
|---|---|---|
| `easy/` | 1 SQL file, 1 source, 1 target | Harvester + edge schema + single-hop label propagation |
| `medium/` | 3 SQL statements + 1 PySpark notebook | Multi-source join, view, Spark `saveAsTable`, label uplift from `Confidential-PII` to `Highly-Confidential-Restricted` |
| `complex/` | 3 sources, 3 layers, deliberate PII leak | Cross-system propagation + DLP gate must flag the `gold.public_marketing` downgrade |

Each tier has a `seed_classifications.json` declaring which sources carry which
MIP-relevant classifications and what labels/violations are expected. The
validation runner (`tests/run_validation.py`) loads each tier, runs the
harvesters, propagates labels, runs the DLP gate, and asserts the actuals
match the expected JSON.

Run all tiers:
```powershell
python -m tests.run_validation
```

Run a single tier:
```powershell
python -m tests.run_validation --tier easy
python -m tests.run_validation --tier medium
python -m tests.run_validation --tier complex
```

Output for each tier:
- `out/<tier>/edges.json`        — harvested edges
- `out/<tier>/labels.json`       — propagated label per node
- `out/<tier>/violations.json`   — DLP gate findings
- `out/<tier>/graph.html`        — PyVis interactive graph (open in a browser)
