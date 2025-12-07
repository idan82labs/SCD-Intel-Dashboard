"""Report Synthesizer - Generates comprehensive reports from research data."""

import json
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

import anthropic

from app.config import settings
from app.agent.prompts.synthesis import SYNTHESIS_PROMPT
from app.models.research import ResearchPlan
from app.models.report import Report, ReportSection, Visualization


class ReportSynthesizer:
    """Synthesizes research results into comprehensive reports."""

    def __init__(self, client: anthropic.Anthropic):
        """Initialize the synthesizer.

        Args:
            client: Anthropic API client
        """
        self.client = client

    async def generate_report(
        self,
        query: str,
        plan: ResearchPlan,
        results: Dict[str, List[Dict[str, Any]]],
        conversation: List[Dict[str, Any]],
    ) -> Report:
        """Generate a comprehensive report from research results.

        Args:
            query: Original research query
            plan: Research plan that was executed
            results: Dictionary of task results
            conversation: Chat history

        Returns:
            Report object
        """
        # Prepare data summary for prompt
        data_summary = self._prepare_data_summary(results)

        # Generate report content using Claude
        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=settings.MAX_TOKENS_SYNTHESIS,
            messages=[
                {
                    "role": "user",
                    "content": SYNTHESIS_PROMPT.format(
                        query=query,
                        objective=plan.objective,
                        data_summary=data_summary,
                    ),
                }
            ],
        )

        # Parse response
        response_text = response.content[0].text
        json_str = self._extract_json(response_text)
        report_data = json.loads(json_str)

        # Convert to Report model
        return self._parse_report(report_data, results)

    def _prepare_data_summary(
        self, results: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Prepare a summary of collected data for the prompt.

        Args:
            results: Dictionary of task results

        Returns:
            Formatted summary string
        """
        summary_parts = []

        for source_name, data in results.items():
            if not data:
                continue

            summary_parts.append(f"### {source_name}")
            summary_parts.append(f"Records collected: {len(data)}")

            # Sample first few records (truncated for context)
            sample = data[:5]
            summary_parts.append("Sample data:")
            summary_parts.append("```json")

            # Truncate to avoid token limits
            sample_str = json.dumps(sample, indent=2, default=str)
            if len(sample_str) > 2000:
                sample_str = sample_str[:2000] + "\n... (truncated)"
            summary_parts.append(sample_str)
            summary_parts.append("```")
            summary_parts.append("")

        return "\n".join(summary_parts)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks.

        Args:
            text: Text potentially containing JSON

        Returns:
            Extracted JSON string
        """
        # Try to find JSON code block
        json_start = text.find("```json")
        if json_start != -1:
            json_end = text.find("```", json_start + 7)
            if json_end != -1:
                return text[json_start + 7 : json_end].strip()

        # Try to find plain JSON
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return text[json_start:json_end]

        return text

    def _parse_report(
        self,
        report_data: Dict[str, Any],
        raw_results: Dict[str, List[Dict[str, Any]]],
    ) -> Report:
        """Parse report data into Report model.

        Args:
            report_data: Parsed JSON report data
            raw_results: Raw data from sources

        Returns:
            Report object
        """
        sections = []
        for section_data in report_data.get("sections", []):
            visualizations = []
            for v in section_data.get("visualizations", []):
                visualizations.append(
                    Visualization(
                        type=v.get("type", "table"),
                        title=v.get("title", ""),
                        description=v.get("description", ""),
                        data=v.get("data", {}),
                    )
                )

            sections.append(
                ReportSection(
                    title=section_data.get("title", "Section"),
                    content=section_data.get("content", ""),
                    visualizations=visualizations,
                )
            )

        return Report(
            id=str(uuid4()),
            title=report_data.get("title", "Research Report"),
            executive_summary=report_data.get("executive_summary", ""),
            sections=sections,
            key_findings=report_data.get("key_findings", []),
            recommendations=report_data.get("recommendations", []),
            generated_at=datetime.utcnow(),
            raw_data=raw_results,
            metadata={
                "data_sources": list(raw_results.keys()),
                "total_records": sum(len(v) for v in raw_results.values()),
            },
        )
