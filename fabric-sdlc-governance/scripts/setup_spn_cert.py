"""Generate self-signed cert, upload to Entra app registration, and write
local .env values for cert-based auth.

Run once. Idempotent: skips upload if a cert with same thumbprint already exists.

Outputs:
  <repo>/.secrets/<APP_ID>.pfx   (cert with private key, no password)
  <repo>/.secrets/<APP_ID>.cer   (public cert for upload)
  Updates <repo>/.env with AZURE_CLIENT_ID, AZURE_TENANT_ID,
    AZURE_CLIENT_CERTIFICATE_PATH so DefaultAzureCredential picks it up.
"""
from __future__ import annotations
import os, sys, json, base64, pathlib, subprocess, datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

ROOT = pathlib.Path(__file__).resolve().parents[1]
SECRETS = ROOT / ".secrets"
SECRETS.mkdir(exist_ok=True)
ENV = ROOT / ".env"

APP_ID  = os.environ.get("SPN_APP_ID", "47a48c18-47f4-4f90-a5e7-f5add3cb2ee3")
TENANT  = os.environ.get("TENANT_ID",  "62c0cb46-1fcc-4c79-ba1b-d7d9fdfbaa68")

PFX = SECRETS / f"{APP_ID}.pfx"
CER = SECRETS / f"{APP_ID}.cer"
PEM = SECRETS / f"{APP_ID}.pem"   # cert + key combined PEM (DefaultAzureCredential uses this)

def ensure_cert():
    if PFX.exists() and PEM.exists() and CER.exists():
        print(f"= cert exists: {PEM}")
        return
    print("+ generating self-signed cert (RSA 2048, 2-year)")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"fabric-cicd-{APP_ID}")])
    now  = datetime.datetime.utcnow()
    cert = (x509.CertificateBuilder()
            .subject_name(subj).issuer_name(subj)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after (now + datetime.timedelta(days=730))
            .sign(key, hashes.SHA256()))
    # PFX (no password)
    PFX.write_bytes(pkcs12.serialize_key_and_certificates(
        name=b"fabric-cicd", key=key, cert=cert, cas=None,
        encryption_algorithm=serialization.NoEncryption()))
    # CER (DER)
    CER.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    # PEM (key + cert) — used by DefaultAzureCredential CertificateCredential
    pem_bytes = (
        key.private_bytes(serialization.Encoding.PEM,
                          serialization.PrivateFormat.PKCS8,
                          serialization.NoEncryption()) +
        cert.public_bytes(serialization.Encoding.PEM))
    PEM.write_bytes(pem_bytes)
    print(f"  wrote {PFX.name}, {CER.name}, {PEM.name}")

def upload_cert_to_app():
    print(f"+ uploading cert to app {APP_ID}")
    # Use az ad app credential reset would replace all creds; we use
    # `az ad app credential` which only adds. But the CLI doesn't have
    # an 'add cert without reset' flag — use Graph.
    import requests, time
    tok = subprocess.check_output(
        "az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv",
        text=True, shell=True).strip()
    H = {"Authorization": f"Bearer {tok}", "Content-Type":"application/json"}
    # GET current app
    r = requests.get(f"https://graph.microsoft.com/v1.0/applications(appId='{APP_ID}')", headers=H)
    r.raise_for_status()
    app = r.json()
    obj_id = app["id"]
    existing = app.get("keyCredentials", [])
    cer_b64 = base64.b64encode(CER.read_bytes()).decode("ascii")
    # Compute thumbprint to check for dups
    cert_obj = x509.load_der_x509_certificate(CER.read_bytes())
    thumb = cert_obj.fingerprint(hashes.SHA1()).hex()
    print(f"  thumbprint: {thumb}")
    if any(k.get("customKeyIdentifier","").lower()==base64.b64encode(bytes.fromhex(thumb)).decode().lower()
           for k in existing):
        print("  = already uploaded"); return thumb
    new = existing + [{
        "type":"AsymmetricX509Cert","usage":"Verify","key": cer_b64,
        "displayName": f"fabric-cicd local {datetime.date.today().isoformat()}"
    }]
    r2 = requests.patch(f"https://graph.microsoft.com/v1.0/applications/{obj_id}",
                        headers=H, json={"keyCredentials": new})
    if r2.status_code >= 400:
        print(f"  ! upload failed {r2.status_code}: {r2.text[:300]}")
        sys.exit(1)
    print("  uploaded.")
    return thumb

def update_env(thumb:str):
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    keys = {
        "AZURE_TENANT_ID": TENANT,
        "AZURE_CLIENT_ID": APP_ID,
        "AZURE_CLIENT_CERTIFICATE_PATH": str(PEM).replace("\\","/"),
        "AZURE_CLIENT_SEND_CERTIFICATE_CHAIN": "true",
        "SPN_CERT_THUMBPRINT": thumb,
    }
    out = []
    seen = set()
    for ln in lines:
        if "=" in ln and not ln.startswith("#"):
            k = ln.split("=",1)[0]
            if k in keys:
                out.append(f"{k}={keys[k]}"); seen.add(k); continue
        out.append(ln)
    for k,v in keys.items():
        if k not in seen: out.append(f"{k}={v}")
    ENV.write_text("\n".join(out)+"\n")
    print(f"+ updated {ENV} with cert auth vars")

def main():
    ensure_cert()
    thumb = upload_cert_to_app()
    update_env(thumb)
    print("\nDone. To test locally:")
    print("  az logout")
    print(f"  az login --service-principal -u {APP_ID} -t {TENANT} \\")
    print(f"           -p {PEM} --tenant {TENANT}")
    print("Or just rely on DefaultAzureCredential (env vars set).")

if __name__ == "__main__":
    main()
