"""Research API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


class CreateResearchRequest(BaseModel):
    """Request to create a new research session."""

    query: str = Field(..., description="Research query", min_length=1)


class ResearchResponse(BaseModel):
    """Response for research session."""

    id: str
    query: str
    status: str
    created_at: str
    has_plan: bool = False
    has_report: bool = False


@router.post("", response_model=ResearchResponse)
async def create_research(request: Request, body: CreateResearchRequest):
    """Create a new research session.

    Args:
        request: FastAPI request
        body: Request body with query

    Returns:
        New research session info
    """
    agent = request.app.state.research_agent
    session = await agent.create_session(body.query)

    return ResearchResponse(
        id=session.id,
        query=session.query,
        status=session.status.value,
        created_at=session.created_at.isoformat(),
        has_plan=session.plan is not None,
        has_report=session.report is not None,
    )


@router.get("/{session_id}")
async def get_research(request: Request, session_id: str):
    """Get research session details.

    Args:
        request: FastAPI request
        session_id: Session ID

    Returns:
        Session details including plan and report if available
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


@router.get("/{session_id}/stream")
async def stream_research(request: Request, session_id: str, message: Optional[str] = None):
    """Stream research updates via Server-Sent Events.

    Args:
        request: FastAPI request
        session_id: Session ID
        message: Optional chat message

    Returns:
        SSE stream
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        """Generate SSE events."""
        if message:
            async for chunk in agent.chat(session_id, message):
                yield f"data: {chunk}\n\n"
        else:
            # Just return current status
            yield f"data: {session.to_dict()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/execute")
async def execute_research(request: Request, session_id: str):
    """Start research execution.

    Args:
        request: FastAPI request
        session_id: Session ID

    Returns:
        SSE stream with execution progress
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.plan:
        raise HTTPException(status_code=400, detail="No research plan - complete clarification first")

    async def event_generator():
        """Generate SSE events for execution."""
        async for chunk in agent.start_execution(session_id):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("")
async def list_research(request: Request):
    """List all research sessions.

    Args:
        request: FastAPI request

    Returns:
        List of session summaries
    """
    agent = request.app.state.research_agent
    return {"sessions": agent.list_sessions()}


@router.delete("/{session_id}")
async def delete_research(request: Request, session_id: str):
    """Delete a research session.

    Args:
        request: FastAPI request
        session_id: Session ID

    Returns:
        Success message
    """
    agent = request.app.state.research_agent

    if session_id not in agent.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del agent.sessions[session_id]
    return {"message": "Session deleted"}
