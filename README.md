## Current Development Status — Step 3.6 Complete

### Project objective

Build a modular, increasingly autonomous AI agent specializing in M&A research. The final system should independently discover and research transactions, identify deal advisers and individual team members, verify evidence, and maintain a structured transaction database.

The agent will eventually operate inside a Docker container with restricted access to local files and system resources.

### Implemented capabilities

- Interactive M&A assistant powered by the OpenAI Responses API.
- Conversation continuity using `previous_response_id`.
- Structured transaction extraction using Pydantic.
- Equity value calculations through Python function calling.
- Multi-round tool-calling loop.
- Web research using OpenAI Web Search.
- Provider-independent search interface designed for future Exa or Tavily integration.
- Standardized research results and source metadata.
- Separation of cited and non-cited sources.
- URL normalization and deduplication.
- Local SQLite research history and exact-query caching.
- Retrieval of historical source leads.
- Configurable tool and search-request limits.
- Graceful final-answer generation when execution limits are reached.

### Project architecture

| Module | Responsibility |
|---|---|
| `AA_agent.py` | Main assistant, interaction and tool orchestration |
| `AA_search.py` | Search provider integration, source processing and caching |
| `AA_tools.py` | Executable Python tools |
| `AA_schemas.py` | Shared structured data models |
| `AA_prompts.py` | Agent and extraction instructions |
| `AA_config.py` | Model and execution configuration |
| `AA_api_setup.py` | API connection test |
| `experiments/` | Isolated development experiments |
| `data/` | Local operational research data |

### Running the agent

Activate the existing virtual environment and run:

```bash
python AA_agent.py
```

Mode 1 provides an interactive assistant with calculations and web research.

Mode 2 extracts structured M&A transaction data from supplied text.

The API key is stored locally in `.env`, which must never be committed to Git.

### Current limitations

- Search findings are not yet independently verified at the claim level.
- Search-call limits do not guarantee a fixed dollar cost.
- Exact-query caching is operational; automatic reuse of related research is not yet integrated into the agent's decision process.
- Historical source-lead retrieval does not establish source relevance or correctness.
- Conversation context is not persistently restored between program sessions.
- Automated daily discovery and full transaction deduplication are not yet implemented.
- The agent is not yet Dockerized.

### Future development

Planned capabilities include automated daily deal discovery, persistent transaction storage and deduplication, evidence verification and scoring, autonomous multi-stage research planning, Docker isolation, and production-scale cost optimization.

A deferred execution-control improvement will allow partial fulfillment of tool-call batches when the remaining search budget is insufficient.

### Engineering principles

Prioritize modularity, provider independence, maintainability, testability, least-privilege security and measurable operating costs. Add complexity progressively while preserving replaceability of individual components.

# AI Agent Project

A local Python AI agent that will progressively be developed from a basic LLM application into an autonomous agent running inside Docker.

## Development roadmap

1. Basic LLM call
2. Structured output
3. Tool calling
4. Agent loop
5. Multiple tools
6. State and memory
7. Planning
8. Verification and guardrails
9. Controlled local file access
10. Dockerized execution
11. Autonomous execution

## Security principle

The agent should only have access to explicitly permitted resources.

Increasing autonomy should not automatically mean increasing permissions.

## Specifications

Model: gpt-6-luna
(When new features are introduced past what is in agent_spec, these should be added hereunder, evaluate the used model: cost v output)