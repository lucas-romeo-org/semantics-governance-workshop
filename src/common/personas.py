"""Run SQL as a persona service principal (Ana / Pedro / Marta) from inside Databricks.

Credentials come from the secret scope created in wave 1. They never leave the workspace.
"""
from databricks.sdk import WorkspaceClient

PERSONAS = {"ana": "Ana · ES analyst", "pedro": "Pedro · PT analyst", "marta": "Marta · global lead (PII)"}


def client(persona: str, scope: str, dbutils) -> WorkspaceClient:
    host = WorkspaceClient().config.host
    return WorkspaceClient(
        host=host,
        client_id=dbutils.secrets.get(scope, f"persona-{persona}-client-id"),
        client_secret=dbutils.secrets.get(scope, f"persona-{persona}-client-secret"),
        auth_type="oauth-m2m",
    )


def run_sql(w: WorkspaceClient, warehouse_id: str, statement: str):
    """Returns (rows, error_message)."""
    r = w.statement_execution.execute_statement(warehouse_id=warehouse_id, statement=statement, wait_timeout="50s")
    if r.status.error:
        return None, r.status.error.message
    rows = r.result.data_array if r.result and r.result.data_array else []
    return rows, None
