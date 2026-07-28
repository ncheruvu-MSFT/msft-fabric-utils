"""Local stand-in for the Fabric User Data Functions.

Implements the minimum surface area the Streamlit pages call so the UI is
fully usable without Fabric/Purview/Entra. Backs everything with an in-memory
dict; restart wipes state. NOT for production use.

Run:
    uvicorn api.stub_udf:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Lineage UDF (local stub)")

_GLOSSARY: dict[str, dict] = {
    "customer_id": {
        "id": "customer_id",
        "name": "customer_id",
        "definition": "Stable surrogate key identifying a customer across systems.",
        "steward": "data-stewards@contoso.com",
        "status": "Approved",
    },
    "lifetime_value": {
        "id": "lifetime_value",
        "name": "lifetime_value",
        "definition": "Modeled gross-margin contribution over the customer relationship.",
        "steward": "data-stewards@contoso.com",
        "status": "Approved",
    },
}
_ACCESS: list[dict] = []


class TermIn(BaseModel):
    name: str
    definition: str
    steward: str


class AccessIn(BaseModel):
    asset_qname: str
    permission: str
    justification: str


@app.get("/glossary/terms")
def list_terms():
    return {"value": list(_GLOSSARY.values())}


@app.post("/glossary/terms")
def upsert_term(t: TermIn):
    _GLOSSARY[t.name] = {
        "id": t.name, "name": t.name, "definition": t.definition,
        "steward": t.steward, "status": "PendingApproval",
    }
    return {"status": "submitted", "id": t.name}


@app.post("/access-requests")
def submit_access(req: AccessIn):
    rec = {
        "id": str(uuid.uuid4()),
        "asset_qname": req.asset_qname,
        "permission": req.permission,
        "justification": req.justification,
        "status": "PendingApproval",
        "created": datetime.now(timezone.utc).isoformat(),
    }
    _ACCESS.append(rec)
    return rec


@app.get("/access-requests/mine")
def list_mine():
    return {"value": _ACCESS}


@app.get("/healthz")
def healthz():
    return {"ok": True}
