"""
Main entry point for our M&A AI agent.

Step 3.5.2 — Integrated tool-calling loop.
"""

import json

from dotenv import load_dotenv
from openai import OpenAI

from AA_tools import calculate_equity_value
from AA_schemas import Transaction
from AA_prompts import AGENT_INSTRUCTIONS, EXTRACTION_INSTRUCTIONS
from AA_config import MODEL, MAX_TOOL_ROUNDS

# Available tools
TOOLS = [
    {
        "type": "function",
        "name": "calculate_equity_value",
        "description": (
            "Calculate equity value using "
            "enterprise value - debt + cash. "
            "All amounts must use the same units."
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
    }
]


def execute_tool(call):
    """
    Execute a tool requested by the LLM.
    """

    if call.name != "calculate_equity_value":
        raise ValueError(f"Unknown tool: {call.name}")

    arguments = json.loads(call.arguments)

    result = calculate_equity_value(**arguments)

    print(f"\n[Tool: {call.name}]")
    print(f"Arguments: {arguments}")
    print(f"Result: {result}")

    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": str(result)
    }


def run_agent(client, task, previous_response_id=None):
    """
    Send a task to the LLM and handle tool calls
    until the task is finished or a limit is reached.
    """

    response = client.responses.create(
        model=MODEL,
        instructions=AGENT_INSTRUCTIONS,
        input=task,
        tools=TOOLS,
        previous_response_id=previous_response_id,
    )

    tool_rounds = 0

    while True:

        if response.status != "completed":
            raise RuntimeError(
                f"Response status: {response.status}"
            )

        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        # No tool calls: the agent has finished
        if not tool_calls:
            if not response.output_text:
                raise RuntimeError(
                    "No final answer was returned."
                )

            return response.output_text, response.id

        # Stop before exceeding our execution limit
        if tool_rounds >= MAX_TOOL_ROUNDS:
            raise RuntimeError(
                "Maximum tool-calling rounds reached."
            )

        tool_rounds += 1

        print(f"\n--- Tool round {tool_rounds} ---")

        tool_results = []

        for call in tool_calls:
            tool_results.append(execute_tool(call))

        # Return tool results to the model
        response = client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            previous_response_id=response.id,
            input=tool_results,
            tools=TOOLS
        )


def extract_transaction(client, text):
    """
    Extract structured M&A information from user text.
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



def main():
    """
    Start our integrated M&A agent.
    """

    load_dotenv()
    client = OpenAI()

    print("M&A Agent started!")
    print("Available modes:")
    print("  1 - Assistant")
    print("  2 - Transaction extraction")
    print("Type 'exit' to quit.\n")

    while True:

        mode = input(
            "Select mode (1/2): "
        ).strip().lower()

        if mode == "exit":
            print("Agent stopped.")
            break

        if mode not in ("1", "2"):
            print("Please select 1 or 2.\n")
            continue

        task = input("You: ").strip()

        if task.lower() == "exit":
            print("Agent stopped.")
            break

        if not task:
            continue

        try:
            if mode == "1":
                answer = run_agent(client, task)
                print(f"\nAgent: {answer}\n")

            elif mode == "2":
                transaction = extract_transaction(
                    client, task
                )

                print("\nStructured transaction:")
                print(
                    transaction.model_dump_json(
                        indent=2
                    )
                )
                print()

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()
