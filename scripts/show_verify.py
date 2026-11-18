"""Print the ✅/❌ lines of the 'verify' task of a bundle job's latest run.

    python scripts/show_verify.py --profile <ws> --job "sgw · w3 security"
"""
import argparse, base64, json, re, urllib.parse

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import ViewsToExport

ap = argparse.ArgumentParser()
ap.add_argument("--profile", required=True)
ap.add_argument("--job", required=True)
ap.add_argument("--task", default="verify")
args = ap.parse_args()

w = WorkspaceClient(profile=args.profile)
job = next(j for j in w.jobs.list(name=args.job))
run = next(iter(w.jobs.list_runs(job_id=job.job_id, limit=1)))
run = w.jobs.get_run(run.run_id)
task = next(t for t in run.tasks if t.task_key == args.task)
html = w.jobs.export_run(task.run_id, views_to_export=ViewsToExport.CODE).views[0].content
model = json.loads(urllib.parse.unquote(base64.b64decode(re.search(r"__DATABRICKS_NOTEBOOK_MODEL = '([^']+)'", html).group(1)).decode()))
print(f"{args.job} · run {run.run_id} · {run.state.result_state}")
for cmd in model["commands"]:
    for r in (cmd.get("results") or {}).get("data") or []:
        if isinstance(r, dict) and r.get("type") == "ansi":
            for line in r.get("data", "").splitlines():
                if line.startswith(("✅", "❌", "ℹ️", "All ", "temporary")):
                    print(" ", line)
