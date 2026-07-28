"""samples/cloud/seed/run_all.py

Applies the seed scripts against the deployed PaaS sources. Reads connection
details from .env.cloud (created by samples/cloud/infra/deploy.ps1).

Auth pattern (Entra-only — MCAPS compliant):
  * Azure SQL  : pyodbc with `Authentication=ActiveDirectoryDefault`
  * Postgres   : psycopg with the DefaultAzureCredential token as the password
  * Cosmos     : DefaultAzureCredential -> hand off to seed_cosmos.main()
  * Oracle     : oracledb thin mode using ORACLE_DSN + ORACLE_USER / ORACLE_PWD (BYO)

Usage:
    python samples/cloud/seed/run_all.py            # all sources
    python samples/cloud/seed/run_all.py --only sql # comma-separated subset
"""
from __future__ import annotations
import argparse
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent

# Load .env.cloud into os.environ
_env_file = ROOT / ".env.cloud"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _split_batches(sql: str) -> list[str]:
    """Split T-SQL on GO batch separators (case-insensitive, own line)."""
    out, cur = [], []
    for ln in sql.splitlines():
        if ln.strip().upper() == "GO":
            if cur:
                out.append("\n".join(cur).strip())
                cur = []
        else:
            cur.append(ln)
    if cur:
        tail = "\n".join(cur).strip()
        if tail:
            out.append(tail)
    return out


def _pick_odbc_driver(pyodbc_mod) -> str:
    drivers = pyodbc_mod.drivers()
    for d in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"):
        if d in drivers:
            return d
    raise RuntimeError(f"No supported SQL Server ODBC driver found. Installed: {drivers}")


def seed_sql() -> None:
    try:
        import pyodbc  # type: ignore
    except ImportError:
        print("SKIP sql: install `pyodbc` and the MS ODBC Driver 18 (or 17) first.")
        return
    from azure.identity import DefaultAzureCredential
    import struct

    driver = _pick_odbc_driver(pyodbc)
    fqdn = os.environ["SQL_SERVER_FQDN"]
    db   = os.environ["SQL_DATABASE"]
    trust = "yes" if "17" in driver else "no"
    # No `Authentication=` in conn-string — passes a raw AAD token via
    # the ODBC SQL_COPT_SS_ACCESS_TOKEN=1256 attribute, which works on both
    # Driver 17 and 18.
    conn_str = (
        f"Driver={{{driver}}};"
        f"Server=tcp:{fqdn},1433;Database={db};"
        f"Encrypt=yes;TrustServerCertificate={trust};Connection Timeout=30;"
    )
    token = DefaultAzureCredential().get_token("https://database.windows.net/.default").token
    tok_bytes = token.encode("utf-16-le")
    token_struct = struct.pack(f"=i{len(tok_bytes)}s", len(tok_bytes), tok_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256
    print(f"sql:      connecting to {fqdn}/{db} ...")
    with pyodbc.connect(
        conn_str,
        autocommit=True,
        attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct},
    ) as cx:
        cx.cursor()
        sql = (HERE / "seed_mssql.sql").read_text(encoding="utf-8")
        for batch in _split_batches(sql):
            cx.execute(batch)
    print(f"sql:      done")


def seed_pg() -> None:
    try:
        import psycopg  # type: ignore
    except ImportError:
        print("SKIP pg: install `psycopg[binary]`.")
        return
    from azure.identity import DefaultAzureCredential
    host = os.environ["PG_SERVER_FQDN"]
    db   = os.environ["PG_DATABASE"]
    user = os.environ["PG_ADMIN_LOGIN"]
    token = DefaultAzureCredential().get_token(
        "https://ossrdbms-aad.database.windows.net/.default"
    ).token
    dsn = f"host={host} dbname={db} user={user} password={token} sslmode=require"
    print(f"pg:       connecting to {host}/{db} as {user} ...")
    with psycopg.connect(dsn, autocommit=True) as cx:
        sql = (HERE / "seed_postgres.sql").read_text(encoding="utf-8")
        with cx.cursor() as cur:
            cur.execute(sql)
    print(f"pg:       done")


def seed_cosmos() -> None:
    try:
        from azure.cosmos import CosmosClient  # noqa: F401
    except ImportError:
        print("SKIP cosmos: install `azure-cosmos`.")
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_cosmos", HERE / "seed_cosmos.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.main()


def seed_oracle() -> None:
    dsn = os.environ.get("ORACLE_DSN")
    if not dsn:
        print("SKIP oracle: ORACLE_DSN not set (BYO instance).")
        return
    try:
        import oracledb  # type: ignore
    except ImportError:
        print("SKIP oracle: install `oracledb`.")
        return
    user = os.environ.get("ORACLE_USER", "system")
    pwd  = os.environ.get("ORACLE_PWD",  "oracle")
    print(f"oracle:   connecting to {dsn} as {user} ...")
    with oracledb.connect(user=user, password=pwd, dsn=dsn) as cx:
        sql = (HERE / "seed_oracle.sql").read_text(encoding="utf-8")
        with cx.cursor() as cur:
            for stmt in [s.strip() for s in sql.split(";\n") if s.strip()]:
                if stmt.upper() == "COMMIT":
                    cx.commit(); continue
                try:
                    cur.execute(stmt)
                except oracledb.DatabaseError as e:
                    # 955 = already exists; ignore on repeat runs
                    if "ORA-00955" in str(e) or "ORA-00001" in str(e):
                        continue
                    raise
        cx.commit()
    print(f"oracle:   done")


def seed_databricks() -> None:
    host = os.environ.get("DATABRICKS_HOST")
    if not host:
        print("SKIP databricks: DATABRICKS_HOST not set (run deploy_databricks.ps1 first).")
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_databricks", HERE / "seed_databricks.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.main()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="Comma-separated subset: sql,pg,cosmos,oracle,databricks")
    args = p.parse_args()
    targets = set(args.only.split(",")) if args.only else {"sql", "pg", "cosmos", "oracle", "databricks"}
    for name, fn in [("sql", seed_sql), ("pg", seed_pg),
                     ("cosmos", seed_cosmos), ("oracle", seed_oracle),
                     ("databricks", seed_databricks)]:
        if name in targets:
            try:
                fn()
            except Exception as exc:
                print(f"{name:10} FAILED: {exc!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
