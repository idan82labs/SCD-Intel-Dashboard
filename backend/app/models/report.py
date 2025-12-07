"""Report-related data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Visualization(BaseModel):
    """A visualization within a report section."""

    type: str = Field(
        ...,
        description="Chart type: bar_chart, line_chart, pie_chart, table, metric, area_chart",
    )
    title: str = Field(..., description="Visualization title")
    description: str = Field(default="", description="What this visualization shows")
    data: Dict[str, Any] = Field(default_factory=dict, description="Chart data")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "data": self.data,
        }


class ReportSection(BaseModel):
    """A section within a report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Narrative content (markdown)")
    visualizations: List[Visualization] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list, description="Source URLs")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "visualizations": [v.to_dict() for v in self.visualizations],
            "citations": self.citations,
        }


class Report(BaseModel):
    """A complete research report."""

    id: str = Field(default="", description="Report ID")
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(..., description="Executive summary")
    sections: List[ReportSection] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        default=None, description="Raw data from sources"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "sections": [s.to_dict() for s in self.sections],
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }


class ExportRequest(BaseModel):
    """Request to export a report."""

    format: str = Field(..., description="Export format: pdf, pptx, docx, json")
    include_executive_summary: bool = Field(default=True)
    include_visualizations: bool = Field(default=True)
    include_data_tables: bool = Field(default=True)
    include_citations: bool = Field(default=True)
    include_raw_data: bool = Field(default=False)


class ShareSettings(BaseModel):
    """Settings for sharing a report."""

    require_password: bool = Field(default=False)
    password: Optional[str] = Field(default=None)
    expire_days: Optional[int] = Field(default=None)
    allow_download: bool = Field(default=True)
