"""End-to-end probe: ask the live Governed Analytics agent one question."""
import time
import uuid
import typing as t
from azure.identity import AzureCliCredential
from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._types import Omit
from openai._utils import is_given

WS = "8cf25d6d-69b3-424b-ad49-bcb9fe4bc643"
AGENT = "af473ed0-27a2-4b40-8ebf-c1792b0950c6"
BASE = f"https://api.fabric.microsoft.com/v1/workspaces/{WS}/aiskills/{AGENT}/aiassistant/openai"

_cred = AzureCliCredential()
_tok_cache = {"token": None, "exp": 0}


def _token() -> str:
    if not _tok_cache["token"] or _tok_cache["exp"] <= time.time() + 300:
        t = _cred.get_token("https://api.fabric.microsoft.com/.default")
        _tok_cache["token"], _tok_cache["exp"] = t.token, t.expires_on
    return _tok_cache["token"]


class FabricOpenAI(OpenAI):
    def __init__(self, api_version="2024-05-01-preview", **kwargs):
        self.api_version = api_version
        dq = kwargs.pop("default_query", {})
        dq["api-version"] = api_version
        super().__init__(api_key="fabric", base_url=BASE, default_query=dq, **kwargs)

    def _prepare_options(self, options: FinalRequestOptions) -> None:
        headers = {**options.headers} if is_given(options.headers) else {}
        options.headers = headers
        tok = _token()
        headers["Authorization"] = f"Bearer {tok}"
        headers.setdefault("Accept", "application/json")
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        return super()._prepare_options(options)


c = FabricOpenAI()
assistant = c.beta.assistants.create(model="not used")
thread = c.beta.threads.create()
c.beta.threads.messages.create(thread_id=thread.id, role="user",
                               content="What was total revenue in 2025 versus 2024?")
run = c.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
start = time.time()
while run.status in ("queued", "in_progress"):
    if time.time() - start > 120:
        print("TIMEOUT"); break
    time.sleep(3)
    run = c.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
print("status:", run.status)
msgs = c.beta.threads.messages.list(thread_id=thread.id, order="asc")
for m in msgs.data:
    if m.role == "assistant":
        print("ASSISTANT:", m.content[0].text.value)
try:
    c.beta.threads.delete(thread_id=thread.id)
except Exception:
    pass
