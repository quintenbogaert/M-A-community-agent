
"""
Main entry point for our M&A AI agent.

Features:
- Interactive M&A assistant
- Conversation memory within a session
- Autonomous tool-calling loop
- Equity value calculations
- Web research through AA_search.py
- Structured M&A transaction extraction
- Search limits and graceful termination
- Basic error handling
"""

import json

from dotenv import load_dotenv
from openai import OpenAI

from AA_tools import calculate_equity_value
from AA_search import search_web
from AA_schemas import Transaction

from AA_prompts import (
    AGENT_INSTRUCTIONS,
    EXTRACTION_INSTRUCTIONS
)

from AA_config import (
    MODEL,
    MAX_TOOL_ROUNDS,
    MAX_SEARCH_CALLS,
    MAX_SOURCES_PER_SEARCH,
    MAX_SEARCH_ANSWER_CHARS
)


# 1. Available tools

TOOLS = [
    {
        "type": "function",
        "name": "calculate_equity_value",
        "description": (
            "Calculate equity value using enterprise "
            "value minus debt plus cash. All amounts "
            "must use the same currency and units."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "enterprise_value": {"type": "number"},
                "debt": {"type": "number"},
                "cash": {"type": "number"}
            },
            "required": [
                "enterprise_value",
                "debt",
                "cash"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "search_web",
        "description": (
            "Research publicly available information "
            "about companies, M&A transactions, "
            "financial advisers, legal advisers, "
            "deal teams and announcements. "
            "The search module handles caching."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A specific research question "
                        "or web-search instruction."
                    )
                }
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "strict": True
    }
]


# 2. Execute approved tools

def execute_tool(call, client):
    """
    Execute a tool requested by the model.

    Returns a function_call_output dictionary.
    """

    arguments = json.loads(call.arguments)

    if call.name == "calculate_equity_value":

        result = calculate_equity_value(**arguments)

        print("\n[Calculator called]")
        print("Arguments:", arguments)
        print("Result:", result)

        output = str(result)

    elif call.name == "search_web":

        query = arguments["query"]

        print("\n[Web research requested]")
        print("Query:", query)

        result = search_web(
            query=query,
            client=client
        )

        print("Provider:", result.provider)
        print("From cache:", result.from_cache)
        print("Search events:", result.search_events)
        print("Cited sources:", len(result.sources))

        # Non-cited diagnostic sources remain in SQLite.
        # Only cited sources are passed to the model.

        cited_sources = [
            {
                "title": source.title,
                "url": source.url
            }
            for source in result.sources[
                :MAX_SOURCES_PER_SEARCH
            ]
        ]

        output = json.dumps(
            {
                "query": result.query,
                "provider": result.provider,
                "from_cache": result.from_cache,
                "answer": result.answer[
                    :MAX_SEARCH_ANSWER_CHARS
                ],
                "cited_sources": cited_sources,
                "note": (
                    "Research findings are not "
                    "independently verified. "
                    "Cached findings may be outdated."
                )
            },
            ensure_ascii=False
        )

    else:
        raise ValueError(
            f"Unknown tool requested: {call.name}"
        )

    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": output
    }


# 3. Autonomous agent loop

def run_agent(client, task, previous_response_id=None):
    """
    Process a user task using the LLM and tools.

    Supports:
    - Multiple tool calls
    - Multiple rounds of tool execution
    - Conversation continuity
    - Search-call limits
    - Graceful completion when limits are reached

    Returns:
        (answer, response_id)
    """

    response = client.responses.create(
        model=MODEL,
        instructions=AGENT_INSTRUCTIONS,
        input=task,
        tools=TOOLS,
        previous_response_id=previous_response_id
    )

    tool_rounds = 0
    search_calls = 0

    while True:

        if response.status != "completed":
            raise RuntimeError(
                f"Response status: {response.status}"
            )

        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        # No tool requests means the model has finished.

        if not tool_calls:

            if not response.output_text:
                raise RuntimeError(
                    "No final answer was returned."
                )

            return response.output_text, response.id

        # Check the maximum number of tool rounds.

        if tool_rounds >= MAX_TOOL_ROUNDS:

            print("\n[Maximum tool rounds reached]")

            return finish_with_existing_research(
                client,
                response,
                tool_calls,
                "Maximum tool-calling rounds reached."
            )

        # Count requested searches before executing them.

        requested_searches = sum(
            call.name == "search_web"
            for call in tool_calls
        )

        if (
            search_calls + requested_searches
            > MAX_SEARCH_CALLS
        ):

            print("\n[Search limit reached]")
            print(
                "Preparing answer using existing research."
            )

            return finish_with_existing_research(
                client,
                response,
                tool_calls,
                "Search budget exhausted."
            )

        search_calls += requested_searches
        tool_rounds += 1

        print(f"\n--- Tool round {tool_rounds} ---")

        # Execute all approved tool requests.

        tool_results = []

        for call in tool_calls:

            tool_results.append(
                execute_tool(call, client)
            )

        # Return tool results to the LLM.

        response = client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            previous_response_id=response.id,
            input=tool_results,
            tools=TOOLS
        )


# 4. Finish gracefully when execution limits are reached

def finish_with_existing_research(
    client,
    response,
    tool_calls,
    reason
):
    """
    Stop requesting tools and generate a final
    answer using information already available.

    Pending tools are explicitly marked as
    not executed.
    """

    tool_results = []

    for call in tool_calls:

        tool_results.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": json.dumps({
                "status": "not_executed",
                "reason": reason
            })
        })

    final_response = client.responses.create(
        model=MODEL,
        instructions=(
            AGENT_INSTRUCTIONS
            + """

            Execution limits have been reached.

            Do not request further tools.

            Prepare the best possible answer using
            information already collected.

            Clearly distinguish supported findings
            from missing or uncertain information.

            Do not invent information or sources.

            Explain briefly if research was incomplete
            because execution limits were reached.
            """
        ),
        previous_response_id=response.id,
        input=tool_results,
        tools=TOOLS,
        tool_choice="none"
    )

    if final_response.status != "completed":
        raise RuntimeError(
            "Final response status: "
            f"{final_response.status}"
        )

    if not final_response.output_text:
        raise RuntimeError(
            "No final answer was returned."
        )

    return final_response.output_text, final_response.id


# 5. Structured M&A transaction extraction

def extract_transaction(client, text):
    """
    Extract structured transaction information
    from user-supplied text.
    """

    response = client.responses.parse(
        model=MODEL,
        instructions=EXTRACTION_INSTRUCTIONS,
        input=text,
        text_format=Transaction
    )

    transaction = response.output_parsed

    if transaction is None:
        raise RuntimeError(
            "No structured transaction was returned."
        )

    return transaction


# 6. Interactive interface

def main():
    """
    Start our integrated M&A AI agent.
    """

    load_dotenv()

    client = OpenAI()

    # Conversation context is maintained only
    # for the assistant mode in this session.

    last_response_id = None

    print("M&A Agent started!")
    print("Available modes:")
    print("  1 - Assistant")
    print("  2 - Transaction extraction")
    print("Type 'reset' to clear conversation history.")
    print("Type 'exit' to quit.\n")

    while True:

        try:
            mode = input(
                "Select mode (1/2): "
            ).strip().lower()

            if mode == "exit":
                print("Agent stopped.")
                break

            if mode == "reset":
                last_response_id = None
                print("Conversation reset.\n")
                continue

            if mode not in ("1", "2"):
                print("Please select 1 or 2.\n")
                continue

            task = input("You: ").strip()

            if task.lower() == "exit":
                print("Agent stopped.")
                break

            if task.lower() == "reset":
                last_response_id = None
                print("Conversation reset.\n")
                continue

            if not task:
                continue

            if mode == "1":

                answer, response_id = run_agent(
                    client,
                    task,
                    previous_response_id=last_response_id
                )

                # Store the final response ID.
                last_response_id = response_id

                print(f"\nAgent: {answer}\n")

            elif mode == "2":

                transaction = extract_transaction(
                    client,
                    task
                )

                print("\nStructured transaction:")
                print(
                    transaction.model_dump_json(
                        indent=2
                    )
                )
                print()

        except (KeyboardInterrupt, EOFError):
            print("\nAgent stopped.")
            break

        except Exception as error:

            print(f"\nError: {error}")
            print("The operation was not completed.\n")

            # Avoid continuing from an uncertain
            # conversation state after a failure.
            last_response_id = None


if __name__ == "__main__":
    main()
