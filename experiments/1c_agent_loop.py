
"""
Step 3.4 — Autonomous tool-calling loop.
"""

import json
import runpy
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 1. Project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL = "gpt-6-luna"
MAX_ROUNDS = 5

load_dotenv(PROJECT_ROOT / ".env")


# 2. Load our existing tool
tool_module = runpy.run_path(
    str(PROJECT_ROOT / "AA_tools.py")
)

calculate_equity_value = tool_module[
    "calculate_equity_value"
]


# 3. Describe the tool to the model
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


# 4. Function to execute a tool
def execute_tool(call):

    if call.name != "calculate_equity_value":
        raise ValueError(f"Unknown tool: {call.name}")

    arguments = json.loads(call.arguments)

    result = calculate_equity_value(**arguments)

    print(f"Tool called: {call.name}")
    print(f"Arguments: {arguments}")
    print(f"Result: {result}\n")

    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": str(result)
    }


# 5. Main agent
def main():

    client = OpenAI()

    print("M&A Agent — Tool Loop")
    print("Type your task below.\n")

    task = input("You: ").strip()

    if not task:
        print("No task entered.")
        return

    response = client.responses.create(
        model=MODEL,
        instructions=(
            "You are an M&A financial assistant. "
            "Always use the calculator when computing "
            "equity values. Use the same currency and "
            "units in all calculations. "
            "If the user requests multiple calculations, "
            "complete all of them before answering."
        ),
        input=task,
        tools=TOOLS
    )

    # 6. Autonomous tool-calling loop
    for round_number in range(1, MAX_ROUNDS + 1):

        print(f"\n--- Round {round_number} ---")

        if response.status != "completed":
            raise RuntimeError(
                f"Response status: {response.status}"
            )

        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        # No tool calls means the agent has finished
        if not tool_calls:
            if response.output_text:
                print("\nFinal answer:")
                print(response.output_text)
                return

            raise RuntimeError(
                "Model returned no tool calls or final text."
            )

        # Execute every requested tool call
        tool_results = []

        for call in tool_calls:
            result = execute_tool(call)
            tool_results.append(result)

        # Return the results to the LLM
        response = client.responses.create(
            model=MODEL,
            previous_response_id=response.id,
            instructions=(
                "You are an M&A financial assistant. "
                "Use the calculator for equity value "
                "calculations. Continue using tools "
                "if needed. Explain the final results "
                "with correct currency and units."
            ),
            input=tool_results,
            tools=TOOLS
        )

    print("\nMaximum number of rounds reached.")
    print("The task was stopped before completion.")


if __name__ == "__main__":
    main()
