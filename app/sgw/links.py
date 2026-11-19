"""Deep links to the real workshop artifacts (patterns validated in spike 8a)."""
import os
from urllib.parse import quote_plus


def _base():
    h = os.environ.get("DATABRICKS_HOST", "")
    return h if h.startswith("http") else f"https://{h}"


def _o():
    return f"o={os.environ.get('DATABRICKS_WORKSPACE_ID', '')}"


def table(catalog, schema, name=None, tab=None):
    """Catalog Explorer. tab: permissions | policies | lineage (validated)."""
    path = "/".join(p for p in (catalog, schema, name) if p)
    url = f"{_base()}/explore/data/{path}?{_o()}"
    return f"{url}&activeTab={tab}" if tab else url


def domain(tag_key):          # Discover search filtered by domain (validated)
    q = quote_plus('domain:"' + tag_key + '"')
    return f"{_base()}/search/discover?q={q}&{_o()}"


def page(page_id):            # Pages: /discover/pages/<id> (validated)
    return f"{_base()}/discover/pages/{page_id}?{_o()}"


def genie(space_id):
    return f"{_base()}/genie/rooms/{space_id}?{_o()}"


def dashboard(dashboard_id):
    return f"{_base()}/dashboardsv3/{dashboard_id}/published?{_o()}"


def job(job_id):
    return f"{_base()}/jobs/{job_id}?{_o()}"


def group(group_id):
    return f"{_base()}/settings/workspace/identity-and-access/groups/{group_id}?{_o()}"


def github(path=""):
    return f"https://github.com/lucas-romeo-org/semantics-governance-workshop/blob/main/{path}"
