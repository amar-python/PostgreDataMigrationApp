"""Report generation — JSON and HTML reports for migration runs.

Aggregates validation, migration, and evaluation data into downloadable reports.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import MigrationRun, UploadedFile
from services.migration_service import UPLOAD_DIR

REPORT_DIR = os.environ.get("MEP_REPORT_DIR", os.path.join(os.getcwd(), "reports"))


def _ensure_report_dir(run_id: int) -> str:
    d = os.path.join(REPORT_DIR, str(run_id))
    os.makedirs(d, exist_ok=True)
    return d


def generate_report(
    db: Session,
    run_id: int,
    fmt: str,
    validation_data: Optional[dict] = None,
    migration_data: Optional[dict] = None,
    evaluation_data: Optional[dict] = None,
) -> Optional[dict[str, Any]]:
    """Generate a report for a migration run.

    Args:
        fmt: "json" or "html"
        validation_data, migration_data, evaluation_data: pre-computed results

    Returns report metadata dict or None if run not found.
    """
    run = db.query(MigrationRun).filter(MigrationRun.id == run_id).first()
    if not run:
        return None

    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.migration_run_id == run_id)
        .all()
    )

    report_data = {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "run": {
            "id": run.id,
            "name": run.name,
            "environment": run.environment,
            "description": run.description,
            "status": run.status.value if hasattr(run.status, "value") else str(run.status),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        },
        "files": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "file_size": f.file_size,
                "row_count": f.row_count,
                "column_count": f.column_count,
            }
            for f in files
        ],
        "validation": validation_data,
        "migration": migration_data,
        "evaluation": evaluation_data,
    }

    report_dir = _ensure_report_dir(run_id)

    if fmt == "json":
        path = os.path.join(report_dir, "report.json")
        with open(path, "w") as fh:
            json.dump(report_data, fh, indent=2, default=str)
        return {
            "run_id": run_id,
            "format": "json",
            "path": path,
            "download_url": f"/api/reports/{run_id}/download/json",
        }

    elif fmt == "html":
        path = os.path.join(report_dir, "report.html")
        html = _render_html_report(report_data)
        with open(path, "w") as fh:
            fh.write(html)
        return {
            "run_id": run_id,
            "format": "html",
            "path": path,
            "download_url": f"/api/reports/{run_id}/download/html",
        }

    return None


def get_report_path(run_id: int, fmt: str) -> Optional[str]:
    """Return the path to a generated report file, or None."""
    ext = "json" if fmt == "json" else "html"
    path = os.path.join(REPORT_DIR, str(run_id), f"report.{ext}")
    return path if os.path.exists(path) else None


def _render_html_report(data: dict) -> str:
    """Render a self-contained HTML report from report data."""
    run = data.get("run", {})
    files = data.get("files", [])
    validation = data.get("validation")
    migration = data.get("migration")
    evaluation = data.get("evaluation")

    def _badge(status: str) -> str:
        colors = {
            "pass": "#107C10", "passed": "#107C10", "completed": "#107C10",
            "fail": "#D13438", "failed": "#D13438", "error": "#D13438",
            "warning": "#FFB900", "info": "#0078D4",
        }
        bg = colors.get(status.lower(), "#605E5C")
        return f'<span style="background:{bg};color:#fff;padding:2px 10px;border-radius:12px;font-size:12px;">{status.upper()}</span>'

    # Build file rows
    file_rows = ""
    for f in files:
        file_rows += f"""<tr>
            <td>{f['filename']}</td>
            <td>{f.get('row_count', '—')}</td>
            <td>{f.get('column_count', '—')}</td>
            <td>{f.get('file_size', 0):,} B</td>
        </tr>"""

    # Validation section
    val_section = ""
    if validation and validation.get("files"):
        val_rows = ""
        for vf in validation["files"]:
            issues = vf.get("issues", [])
            errors = sum(1 for i in issues if i.get("severity") == "error")
            warnings = sum(1 for i in issues if i.get("severity") == "warning")
            status = "pass" if errors == 0 else "fail"
            val_rows += f"""<tr>
                <td>{vf['filename']}</td>
                <td>{errors}</td><td>{warnings}</td>
                <td>{_badge(status)}</td>
            </tr>"""
        val_summary = validation.get("summary", {})
        val_section = f"""
        <h2>Validation</h2>
        <p>Overall: {_badge(val_summary.get('status', validation.get('status', '—')))}</p>
        <table><tr><th>File</th><th>Errors</th><th>Warnings</th><th>Status</th></tr>
        {val_rows}</table>"""

    # Migration section
    mig_section = ""
    if migration and migration.get("files"):
        mig_rows = ""
        for mf in migration["files"]:
            mig_rows += f"""<tr>
                <td>{mf['filename']}</td>
                <td>{mf.get('table_name', '—')}</td>
                <td>{mf.get('rows_loaded', 0):,}</td>
                <td>{_badge(mf.get('status', '—'))}</td>
            </tr>"""
        mig_summary = migration.get("summary", {})
        mig_section = f"""
        <h2>Migration</h2>
        <p>Tables created: {mig_summary.get('tables_created', 0)} | Rows loaded: {mig_summary.get('total_rows_loaded', 0):,}</p>
        <table><tr><th>File</th><th>Table</th><th>Rows</th><th>Status</th></tr>
        {mig_rows}</table>"""

    # Evaluation section
    eval_section = ""
    if evaluation and evaluation.get("files"):
        eval_rows = ""
        for ef in evaluation["files"]:
            eval_rows += f"""<tr>
                <td>{ef['filename']}</td>
                <td>{ef.get('source_rows', '—')}</td>
                <td>{ef.get('target_rows', '—')}</td>
                <td>{ef.get('score', '—')}</td>
                <td>{_badge(ef.get('status', '—'))}</td>
            </tr>"""
        eval_summary = evaluation.get("summary", {})
        eval_section = f"""
        <h2>Evaluation</h2>
        <p>Overall Score: <strong>{eval_summary.get('overall_score', 0)}</strong>/100
           — Verdict: {_badge(eval_summary.get('verdict', '—'))}</p>
        <table><tr><th>File</th><th>Source Rows</th><th>Target Rows</th><th>Score</th><th>Status</th></tr>
        {eval_rows}</table>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MEP Report — {run.get('name', 'Migration')}</title>
<style>
    body {{ font-family: "Segoe UI", Roboto, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; color: #201F1E; }}
    h1 {{ color: #0078D4; border-bottom: 2px solid #0078D4; padding-bottom: 8px; }}
    h2 {{ color: #005A9E; margin-top: 32px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
    th, td {{ border: 1px solid #EDEBE9; padding: 8px 12px; text-align: left; }}
    th {{ background: #F3F2F1; font-weight: 600; }}
    tr:nth-child(even) {{ background: #FAFAFA; }}
    .meta {{ color: #605E5C; font-size: 14px; }}
</style>
</head>
<body>
    <h1>Migration Report — {run.get('name', '')}</h1>
    <p class="meta">
        Environment: <strong>{run.get('environment', '—')}</strong> |
        Status: {_badge(run.get('status', '—'))} |
        Generated: {data.get('report_generated_at', '—')}
    </p>
    {f'<p>{run.get("description", "")}</p>' if run.get('description') else ''}

    <h2>Uploaded Files ({len(files)})</h2>
    <table>
        <tr><th>Filename</th><th>Rows</th><th>Columns</th><th>Size</th></tr>
        {file_rows}
    </table>

    {val_section}
    {mig_section}
    {eval_section}

    <hr style="margin-top:40px;">
    <p class="meta">Migration Evaluation Platform (MEP) — Automated Report</p>
</body>
</html>"""
