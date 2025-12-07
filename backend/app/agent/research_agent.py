"""
Research Agent - Orchestrates the entire research process.

This is the main agent that handles:
1. Query understanding and clarification
2. Research planning
3. Multi-source data collection
4. Report synthesis and visualization
"""

import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import anthropic

from app.config import settings
from app.data_sources.registry import DataSourceRegistry
from app.agent.planner import ResearchPlanner
from app.agent.executor import ResearchExecutor
from app.agent.synthesizer import ReportSynthesizer
from app.agent.prompts.system import CLARIFICATION_PROMPT
from app.models.research import (
    ResearchSession,
    ResearchPlan,
    ResearchStatus,
    Message,
)
from app.models.report import Report


class ResearchAgent:
    """
    Main research agent that orchestrates the entire research workflow.
    """

    def __init__(self, data_sources: DataSourceRegistry):
        """Initialize the research agent.

        Args:
            data_sources: Registry of available data sources
        """
        self.data_sources = data_sources
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.planner = ResearchPlanner(self.client)
        self.executor = ResearchExecutor(data_sources)
        self.synthesizer = ReportSynthesizer(self.client)

        # Active sessions
        self.sessions: Dict[str, ResearchSession] = {}

    async def create_session(self, initial_query: str) -> ResearchSession:
        """Create a new research session.

        Args:
            initial_query: User's initial research query

        Returns:
            New ResearchSession object
        """
        session_id = str(uuid4())
        session = ResearchSession(
            id=session_id,
            query=initial_query,
            status=ResearchStatus.CLARIFYING,
            created_at=datetime.utcnow(),
            messages=[],
            plan=None,
            results=None,
            report=None,
        )
        self.sessions[session_id] = session
        return session

    async def chat(
        self,
        session_id: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """Handle chat interaction with streaming response.

        Args:
            session_id: Session ID
            user_message: User's message

        Yields:
            JSON chunks for real-time UI updates
        """
        session = self.sessions.get(session_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return

        # Add user message
        session.messages.append(
            Message(role="user", content=user_message, timestamp=datetime.utcnow())
        )
        session.updated_at = datetime.utcnow()

        # Handle based on status
        if session.status == ResearchStatus.CLARIFYING:
            async for chunk in self._handle_clarification(session, user_message):
                yield chunk

        elif session.status == ResearchStatus.PLANNING:
            async for chunk in self._generate_plan(session):
                yield chunk

        elif session.status == ResearchStatus.READY:
            # User confirmed plan, start execution
            async for chunk in self._execute_research(session):
                yield chunk

    async def _handle_clarification(
        self,
        session: ResearchSession,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """Handle the clarification phase.

        Args:
            session: Research session
            user_message: User's message

        Yields:
            JSON chunks
        """
        # Build conversation context
        messages = self._build_messages(session)

        # Stream response
        assistant_message = ""

        with self.client.messages.stream(
            model=settings.DEFAULT_MODEL,
            max_tokens=settings.MAX_TOKENS_CHAT,
            system=CLARIFICATION_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                assistant_message += text
                yield json.dumps({"type": "chat_delta", "content": text}) + "\n"

        # Check if ready to plan
        if "[READY_TO_PLAN]" in assistant_message:
            session.status = ResearchStatus.PLANNING
            assistant_message = assistant_message.replace("[READY_TO_PLAN]", "").strip()
            yield json.dumps({"type": "status_change", "status": "planning"}) + "\n"

            # Automatically start planning
            async for chunk in self._generate_plan(session):
                yield chunk

        # Save assistant message
        session.messages.append(
            Message(
                role="assistant",
                content=assistant_message,
                timestamp=datetime.utcnow(),
            )
        )

    async def _generate_plan(
        self,
        session: ResearchSession,
    ) -> AsyncGenerator[str, None]:
        """Generate research plan based on conversation.

        Args:
            session: Research session

        Yields:
            JSON chunks
        """
        yield json.dumps(
            {"type": "planning_start", "message": "Creating research plan..."}
        ) + "\n"

        try:
            # Generate plan
            plan = await self.planner.create_plan(
                query=session.query,
                conversation=[m.to_dict() for m in session.messages],
                available_sources=self.data_sources.list_sources(),
            )

            session.plan = plan
            session.status = ResearchStatus.READY

            yield json.dumps({"type": "plan_ready", "plan": plan.to_dict()}) + "\n"

        except Exception as e:
            session.status = ResearchStatus.ERROR
            session.error = str(e)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    async def _execute_research(
        self,
        session: ResearchSession,
    ) -> AsyncGenerator[str, None]:
        """Execute the research plan with real-time updates.

        Args:
            session: Research session

        Yields:
            JSON chunks
        """
        if not session.plan:
            yield json.dumps({"error": "No research plan"})
            return

        session.status = ResearchStatus.EXECUTING

        yield json.dumps(
            {
                "type": "execution_start",
                "total_phases": len(session.plan.phases),
            }
        ) + "\n"

        # Execute each phase
        all_results: Dict[str, List[Dict[str, Any]]] = {}

        for phase_idx, phase in enumerate(session.plan.phases):
            yield json.dumps(
                {
                    "type": "phase_start",
                    "phase_index": phase_idx,
                    "phase_name": phase.name,
                    "tasks": [t.description for t in phase.tasks],
                }
            ) + "\n"

            # Execute phase tasks
            try:
                phase_results = await self.executor.execute_phase(phase)

                # Yield task completions
                for task_result in phase_results:
                    yield json.dumps(
                        {
                            "type": "task_complete",
                            "phase_index": phase_idx,
                            "task": task_result.task_name,
                            "success": task_result.success,
                            "result_count": len(task_result.data) if task_result.data else 0,
                        }
                    ) + "\n"

                    if task_result.success and task_result.data:
                        all_results[task_result.task_name] = task_result.data

            except Exception as e:
                yield json.dumps(
                    {
                        "type": "phase_error",
                        "phase_index": phase_idx,
                        "error": str(e),
                    }
                ) + "\n"

            yield json.dumps(
                {
                    "type": "phase_complete",
                    "phase_index": phase_idx,
                }
            ) + "\n"

        session.results = all_results
        session.status = ResearchStatus.SYNTHESIZING

        yield json.dumps({"type": "synthesis_start"}) + "\n"

        # Generate report
        try:
            report = await self.synthesizer.generate_report(
                query=session.query,
                plan=session.plan,
                results=all_results,
                conversation=[m.to_dict() for m in session.messages],
            )

            session.report = report
            session.status = ResearchStatus.COMPLETE

            yield json.dumps(
                {
                    "type": "report_ready",
                    "report": report.to_dict(),
                }
            ) + "\n"

        except Exception as e:
            session.status = ResearchStatus.ERROR
            session.error = str(e)
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    def _build_messages(self, session: ResearchSession) -> List[Dict[str, str]]:
        """Build messages array for Claude API.

        Args:
            session: Research session

        Returns:
            List of message dicts
        """
        messages = []

        # Add initial query if not in messages
        if session.query and not any(
            m.content == session.query for m in session.messages
        ):
            messages.append({"role": "user", "content": session.query})

        # Add conversation history
        for msg in session.messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def start_execution(
        self, session_id: str
    ) -> AsyncGenerator[str, None]:
        """Start research execution (called when user confirms plan).

        Args:
            session_id: Session ID

        Yields:
            JSON chunks
        """
        session = self.sessions.get(session_id)
        if not session:
            yield json.dumps({"error": "Session not found"})
            return

        async for chunk in self._execute_research(session):
            yield chunk

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            ResearchSession or None
        """
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with basic info.

        Returns:
            List of session summaries
        """
        return [
            {
                "id": s.id,
                "query": s.query,
                "status": s.status.value,
                "created_at": s.created_at.isoformat(),
                "has_report": s.report is not None,
            }
            for s in self.sessions.values()
        ]
