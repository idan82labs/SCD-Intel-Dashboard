"""Research Executor - Executes research plans across multiple data sources."""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.data_sources.registry import DataSourceRegistry
from app.models.research import ResearchPhase, ResearchTask, TaskResult


class ResearchExecutor:
    """Executes research plans using the data source registry."""

    def __init__(self, data_sources: DataSourceRegistry):
        """Initialize the executor.

        Args:
            data_sources: Registry of available data sources
        """
        self.data_sources = data_sources

    async def execute_phase(
        self,
        phase: ResearchPhase,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[TaskResult]:
        """Execute all tasks in a research phase.

        Args:
            phase: Research phase to execute
            progress_callback: Optional callback for progress updates

        Returns:
            List of task results
        """
        # Execute tasks in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async def execute_with_semaphore(task: ResearchTask) -> TaskResult:
            async with semaphore:
                result = await self._execute_task(task)
                if progress_callback:
                    progress_callback(
                        {
                            "task": task.description,
                            "success": result.success,
                            "result_count": len(result.data) if result.data else 0,
                        }
                    )
                return result

        tasks = [execute_with_semaphore(task) for task in phase.tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to TaskResults
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    TaskResult(
                        task_name=phase.tasks[i].description,
                        source=phase.tasks[i].source,
                        success=False,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_task(self, task: ResearchTask) -> TaskResult:
        """Execute a single research task.

        Args:
            task: Task to execute

        Returns:
            TaskResult with data or error
        """
        start_time = datetime.utcnow()

        try:
            # Get the data source
            source = self.data_sources.get_source(task.source)
            if not source:
                return TaskResult(
                    task_name=task.description,
                    source=task.source,
                    success=False,
                    error=f"Data source '{task.source}' not found",
                )

            # Execute search
            results = await source.search(task.query)

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return TaskResult(
                task_name=task.description,
                source=task.source,
                success=True,
                data=results,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return TaskResult(
                task_name=task.description,
                source=task.source,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def execute_plan(
        self,
        phases: List[ResearchPhase],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute an entire research plan.

        Args:
            phases: List of phases to execute
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary mapping task names to their results
        """
        all_results: Dict[str, List[Dict[str, Any]]] = {}

        for phase in phases:
            if progress_callback:
                progress_callback(
                    {
                        "type": "phase_start",
                        "phase": phase.name,
                    }
                )

            phase_results = await self.execute_phase(phase, progress_callback)

            for result in phase_results:
                if result.success and result.data:
                    all_results[result.task_name] = result.data

            if progress_callback:
                progress_callback(
                    {
                        "type": "phase_complete",
                        "phase": phase.name,
                        "tasks_completed": len(phase_results),
                        "tasks_successful": sum(1 for r in phase_results if r.success),
                    }
                )

        return all_results
