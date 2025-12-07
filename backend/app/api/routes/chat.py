"""Chat API routes."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., description="User message", min_length=1)


@router.post("/{session_id}")
async def chat(request: Request, session_id: str, body: ChatRequest):
    """Send a chat message and receive streaming response.

    Args:
        request: FastAPI request
        session_id: Research session ID
        body: Chat message

    Returns:
        SSE stream with chat response
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        """Generate SSE events for chat response."""
        async for chunk in agent.chat(session_id, body.message):
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


@router.get("/{session_id}/history")
async def get_chat_history(request: Request, session_id: str):
    """Get chat history for a session.

    Args:
        request: FastAPI request
        session_id: Research session ID

    Returns:
        List of chat messages
    """
    agent = request.app.state.research_agent
    session = agent.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "messages": [m.to_dict() for m in session.messages],
        "status": session.status.value,
    }
