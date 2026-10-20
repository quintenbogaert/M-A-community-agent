
"""
Step 3.3 — Our first tool-calling experiment.
"""

import json
import runpy
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# Locate the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load the Python function from AA_tools.py
tool_module = runpy.run_path(
    str(PROJECT_ROOT / "AA_tools.py")
)

calculate_equity_value = tool_module[
    "calculate_equity_value"
]


# Describe the available tool to the LLM
TOOLS = [
    {
        "type": "function",
        "name": "calculate_equity_value",
        "description": (
            "Calculate equity value from enterprise "
            "value, debt and cash."
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


def main():

    # Load the API key
    load_dotenv(PROJECT_ROOT / ".env")
    client = OpenAI()

    question = (
        "A company has an enterprise value of "
        "120 million euros, debt of 35 million euros "
        "and cash of 10 million euros. "
        "What is its equity value?"
    )

    # STEP 1: Ask the LLM
    response = client.responses.create(
        model="gpt-6-luna",
        instructions=(
            "You are an M&A assistant. "
            "Use the calculator for equity value calculations."
        ),
        input=question,
        tools=TOOLS
    )

    # STEP 2: Execute requested tool calls
    tool_results = []

    for item in response.output:

        if item.type != "function_call":
            continue

        if item.name != "calculate_equity_value":
            raise ValueError("Unknown tool: " + item.name)

        arguments = json.loads(item.arguments)

        result = calculate_equity_value(**arguments)

        print("Tool called:", item.name)
        print("Arguments:", arguments)
        print("Tool result:", result)

        tool_results.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": str(result)
        })

    if not tool_results:
        print("The model did not request a tool.")
        print(response.output_text)
        return

    # STEP 3: Give tool results back to the LLM
    final_response = client.responses.create(
        model="gpt-6-luna",
        previous_response_id=response.id,
        instructions=(
            "Explain the calculation clearly. "
            "Keep the correct currency and units."
        ),
        input=tool_results,
        tools=TOOLS,
        tool_choice="none"
    )

    print("\nAgent:", final_response.output_text)


if __name__ == "__main__":
    main()
