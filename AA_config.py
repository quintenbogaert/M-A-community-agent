
"""
Configuration settings for our M&A AI agent.
"""

# OpenAI model
MODEL = "gpt-6-luna"

# Maximum consecutive rounds of tool calls
MAX_TOOL_ROUNDS = 5

# Search configuration
SEARCH_PROVIDER = "openai"

# Local search-history cache
SEARCH_CACHE_ENABLED = True
SEARCH_CACHE_DAYS = 7

# Maximum search_web() requests per user task
MAX_SEARCH_CALLS = 3

# Maximum number of cited sources returned to the agent
MAX_SOURCES_PER_SEARCH = 10

# Maximum characters of research text passed to the agent
MAX_SEARCH_ANSWER_CHARS = 12000