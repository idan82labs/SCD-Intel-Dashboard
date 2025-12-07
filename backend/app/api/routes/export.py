"""Export API routes."""

import json
from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


class ExportRequest(BaseModel):
    """Export request body."""

    format: str = Field(
        default="json",
        description="Export format: json, csv, pdf",
    )
    include_raw_data: bool = Field(
        default=False,
        description="Include raw data in export",
    )


@router.post("/{session_id}")
async def export_report(request: Request, session_id: str, body: ExportRequest):
    """Export research report.

    Args:
        request: FastAPI request
        session_id: Research session ID
        body: Export options

    Returns:
        Exported file
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.report:
        raise HTTPException(status_code=400, detail="No report available")

    if body.format == "json":
        return await _export_json(session, body.include_raw_data)
    elif body.format == "csv":
        return await _export_csv(session)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {body.format}. Supported: json, csv",
        )


async def _export_json(session, include_raw: bool):
    """Export report as JSON.

    Args:
        session: Research session
        include_raw: Include raw data

    Returns:
        JSON file response
    """
    report_data = session.report.to_dict()

    if not include_raw:
        report_data.pop("raw_data", None)

    content = json.dumps(report_data, indent=2, default=str)

    return StreamingResponse(
        BytesIO(content.encode()),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="report_{session.id}.json"'
        },
    )


async def _export_csv(session):
    """Export report data as CSV.

    Args:
        session: Research session

    Returns:
        CSV file response
    """
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # Write key findings
    writer.writerow(["Key Findings"])
    for finding in session.report.key_findings:
        writer.writerow([finding])
    writer.writerow([])

    # Write recommendations
    writer.writerow(["Recommendations"])
    for rec in session.report.recommendations:
        writer.writerow([rec])
    writer.writerow([])

    # Write raw data if available
    if session.report.raw_data:
        for source_name, data in session.report.raw_data.items():
            writer.writerow([f"Data Source: {source_name}"])
            if data:
                # Write headers from first item
                headers = list(data[0].keys())
                writer.writerow(headers)
                for item in data:
                    writer.writerow([str(item.get(h, "")) for h in headers])
            writer.writerow([])

    content = output.getvalue()

    return StreamingResponse(
        BytesIO(content.encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="report_{session.id}.csv"'
        },
    )


@router.get("/{session_id}/raw-data")
async def get_raw_data(request: Request, session_id: str):
    """Get raw data collected during research.

    Args:
        request: FastAPI request
        session_id: Research session ID

    Returns:
        Raw data from all sources
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.results:
        raise HTTPException(status_code=400, detail="No data collected yet")

    return {
        "session_id": session_id,
        "sources": list(session.results.keys()),
        "data": session.results,
        "total_records": sum(len(v) for v in session.results.values()),
    }
