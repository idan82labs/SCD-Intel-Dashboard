"""Research-related data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchStatus(str, Enum):
    """Status of a research session."""

    CREATED = "created"
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    READY = "ready"
    EXECUTING = "executing"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    ERROR = "error"


class ResearchTask(BaseModel):
    """A single research task within a phase."""

    source: str = Field(..., description="Data source to query")
    description: str = Field(..., description="What this task does")
    query: str = Field(..., description="Search query or parameters")
    expected_output: str = Field(default="", description="Expected data type")
    status: str = Field(default="pending", description="Task status")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class ResearchPhase(BaseModel):
    """A phase of the research plan containing multiple tasks."""

    name: str = Field(..., description="Phase name")
    description: str = Field(default="", description="Phase description")
    estimated_time_minutes: int = Field(default=2, description="Estimated duration")
    tasks: List[ResearchTask] = Field(default_factory=list)
    status: str = Field(default="pending", description="Phase status")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "estimated_time_minutes": self.estimated_time_minutes,
            "tasks": [t.to_dict() for t in self.tasks],
            "status": self.status,
        }


class ResearchPlan(BaseModel):
    """A complete research plan."""

    title: str = Field(..., description="Plan title")
    objective: str = Field(default="", description="Research objective")
    estimated_time_minutes: int = Field(default=10, description="Total estimated time")
    phases: List[ResearchPhase] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "objective": self.objective,
            "estimated_time_minutes": self.estimated_time_minutes,
            "phases": [p.to_dict() for p in self.phases],
            "deliverables": self.deliverables,
        }


class Message(BaseModel):
    """A chat message."""

    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ResearchSession(BaseModel):
    """A complete research session."""

    id: str = Field(..., description="Session ID")
    query: str = Field(..., description="Original research query")
    status: ResearchStatus = Field(default=ResearchStatus.CREATED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    messages: List[Message] = Field(default_factory=list)
    plan: Optional[ResearchPlan] = None
    results: Optional[Dict[str, List[Dict[str, Any]]]] = None
    report: Optional[Any] = None  # Will be Report type
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "query": self.query,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "messages": [m.to_dict() for m in self.messages],
            "plan": self.plan.to_dict() if self.plan else None,
            "has_results": self.results is not None,
            "has_report": self.report is not None,
            "error": self.error,
        }


class TaskResult(BaseModel):
    """Result from executing a single research task."""

    task_name: str = Field(..., description="Name of the task")
    source: str = Field(..., description="Data source used")
    success: bool = Field(..., description="Whether task succeeded")
    data: Optional[List[Dict[str, Any]]] = Field(default=None)
    error: Optional[str] = Field(default=None)
    execution_time_ms: int = Field(default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_name": self.task_name,
            "source": self.source,
            "success": self.success,
            "result_count": len(self.data) if self.data else 0,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


class ExecutionLog(BaseModel):
    """Log entry for research execution."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    phase: str = Field(..., description="Current phase")
    task: Optional[str] = Field(default=None)
    status: str = Field(..., description="Status: started, completed, error")
    message: str = Field(default="")
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase,
            "task": self.task,
            "status": self.status,
            "message": self.message,
            "data": self.data,
        }
