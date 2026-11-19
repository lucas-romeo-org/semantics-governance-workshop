"""Exactly one identity per call: the logged-in user (OBO) or a persona service principal.

The app's own service principal is never used to read business data.
"""
import os
from fastapi import HTTPException, Request
from databricks.sdk import WorkspaceClient

PERSONAS = {
    "ana": {"label": "Ana", "role": "Analyst · Spain", "groups": ["wk_analysts_es"]},
    "pedro": {"label": "Pedro", "role": "Analyst · Portugal", "groups": ["wk_analysts_pt"]},
    "marta": {"label": "Marta", "role": "Global sales lead", "groups": ["wk_sales_leads", "wk_pii_readers"]},
}


def host() -> str:
    h = os.environ.get("DATABRICKS_HOST", "")
    return h if h.startswith("http") else f"https://{h}"


def client_for(who: str, request: Request) -> WorkspaceClient:
    if who == "me":
        token = request.headers.get("x-forwarded-access-token")
        if not token:
            raise HTTPException(401, "No user token: open the app through Databricks (user authorization)")
        return WorkspaceClient(host=host(), token=token, auth_type="pat")
    if who in PERSONAS:
        p = who.upper()
        return WorkspaceClient(host=host(), client_id=os.environ[f"PERSONA_{p}_CLIENT_ID"],
                               client_secret=os.environ[f"PERSONA_{p}_CLIENT_SECRET"], auth_type="oauth-m2m")
    raise HTTPException(400, f"unknown identity '{who}'")


def app_client() -> WorkspaceClient:
    """App service principal: metadata and job status only."""
    return WorkspaceClient()
