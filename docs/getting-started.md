# Getting Started with Microsoft Fabric Utilities

## Importing Notebooks into Fabric

1. Open your **Microsoft Fabric** workspace in the browser
2. Click **New** → **Import notebook**
3. Upload the `.ipynb` file from the `notebooks/` folder
4. Once imported, click on the notebook to open it
5. **Attach a Lakehouse** from the left panel (optional — required for CSV/Delta export)

## Configuration

Each notebook has a **Configuration** cell near the top. Common settings:

| Setting | Description |
|---------|-------------|
| `TARGET_WORKSPACE_ID` | Set to a specific workspace GUID, or `None` to use the current workspace |
| `DRY_RUN` | Set to `True` to preview changes without applying (default) |

## Authentication

All notebooks use **Fabric-native authentication** via `mssparkutils.credentials.getToken()`. No manual credential setup is required when running inside a Fabric workspace.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: sempy` | Ensure you're running inside a Fabric notebook, not a local Jupyter environment |
| `403 Forbidden` on REST API calls | Verify you have Admin or Member role on the target workspace |
| `dm_db_partition_stats not available` | The notebook will automatically fall back to `sys.partitions` (row counts only, no size info) |
| SQL endpoint connection timeout | Ensure the Warehouse/Lakehouse SQL endpoint is active and accessible |
