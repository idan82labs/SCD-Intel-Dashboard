"""Research Planner - Creates dynamic research plans based on query analysis."""

import json
from typing import List, Dict, Any

import anthropic

from app.config import settings
from app.agent.prompts.planning import PLANNING_PROMPT
from app.models.research import ResearchPlan, ResearchPhase, ResearchTask
from app.data_sources.registry import SourceCapability


class ResearchPlanner:
    """Creates research plans based on query analysis."""

    def __init__(self, client: anthropic.Anthropic):
        """Initialize the planner.

        Args:
            client: Anthropic API client
        """
        self.client = client

    async def create_plan(
        self,
        query: str,
        conversation: List[Dict[str, Any]],
        available_sources: List[SourceCapability],
    ) -> ResearchPlan:
        """Create a research plan based on query and conversation.

        Args:
            query: Original research query
            conversation: Chat history
            available_sources: List of available data sources

        Returns:
            ResearchPlan object
        """
        # Format sources for prompt
        sources_text = "\n".join(
            [
                f"- **{s.name}**: {s.description}\n"
                f"  Query types: {', '.join(s.query_types)}\n"
                f"  Returns: {', '.join(s.data_types)}"
                for s in available_sources
            ]
        )

        # Format conversation
        conv_text = "\n".join(
            [f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}" for msg in conversation]
        )

        # Generate plan using Claude
        response = self.client.messages.create(
            model=settings.DEFAULT_MODEL,
            max_tokens=settings.MAX_TOKENS_PLAN,
            messages=[
                {
                    "role": "user",
                    "content": PLANNING_PROMPT.format(
                        sources=sources_text,
                        query=query,
                        conversation=conv_text,
                    ),
                }
            ],
        )

        # Parse JSON from response
        response_text = response.content[0].text

        # Extract JSON block
        json_str = self._extract_json(response_text)
        plan_data = json.loads(json_str)

        # Convert to ResearchPlan model
        return self._parse_plan(plan_data)

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

    def _parse_plan(self, plan_data: Dict[str, Any]) -> ResearchPlan:
        """Parse plan data into ResearchPlan model.

        Args:
            plan_data: Parsed JSON plan data

        Returns:
            ResearchPlan object
        """
        phases = []
        for phase_data in plan_data.get("phases", []):
            tasks = [
                ResearchTask(
                    source=t.get("source", "web_search"),
                    description=t.get("description", ""),
                    query=t.get("query", ""),
                    expected_output=t.get("expected_output", ""),
                )
                for t in phase_data.get("tasks", [])
            ]

            phases.append(
                ResearchPhase(
                    name=phase_data.get("name", "Research Phase"),
                    description=phase_data.get("description", ""),
                    estimated_time_minutes=phase_data.get("estimated_time_minutes", 2),
                    tasks=tasks,
                )
            )

        return ResearchPlan(
            title=plan_data.get("title", "Research Plan"),
            objective=plan_data.get("objective", ""),
            estimated_time_minutes=plan_data.get("estimated_time_minutes", 10),
            phases=phases,
            deliverables=plan_data.get("deliverables", []),
        )
