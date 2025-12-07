"""Planning prompts for the research agent."""

PLANNING_PROMPT = """You are a research planning expert. Based on the user's query and conversation, create a comprehensive research plan.

## AVAILABLE DATA SOURCES

{sources}

## QUERY CONTEXT

Original Query: {query}

Conversation:
{conversation}

## INSTRUCTIONS

Create a research plan with 3-5 phases. Each phase should:
1. Have a clear objective
2. Use appropriate data sources from the available list
3. Include specific search queries/parameters
4. Have estimated completion time

Output your plan as JSON in this exact format:

```json
{{
  "title": "Research plan title",
  "objective": "1-2 sentence objective",
  "estimated_time_minutes": 10,
  "phases": [
    {{
      "name": "Phase Name",
      "description": "What this phase accomplishes",
      "estimated_time_minutes": 3,
      "tasks": [
        {{
          "source": "source_name",
          "description": "What to search for",
          "query": "specific search query or parameters",
          "expected_output": "What data to expect"
        }}
      ]
    }}
  ],
  "deliverables": [
    "Executive Summary",
    "Market Size Analysis",
    "Competitive Matrix",
    "etc."
  ]
}}
```

IMPORTANT:
- Use ONLY data sources from the available list above
- Be specific in your search queries
- Create a thorough plan that will answer the user's research question comprehensively
- Estimate realistic times for each phase (typically 1-5 minutes per phase)
"""
