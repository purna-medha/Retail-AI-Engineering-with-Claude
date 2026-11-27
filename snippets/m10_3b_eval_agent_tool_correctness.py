# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anthropic>=2.10.0",
#     "deepeval>=4.3.6",
#     "python-dotenv>=1.2.4",
# ]
# ///
# Optional: check the agent path explicitly (tools_called vs expected_tools) alongside the outcome.
import os

from anthropic import Anthropic, beta_tool
from deepeval import evaluate
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, ToolCall
from dotenv import load_dotenv

load_dotenv()
MAX_ITERATIONS = 4  # Try 1: what happens to each score?


# 1 · The M8 agent: one tool, a loop that the runner manages.
@beta_tool
def get_net_flow(month: str) -> str:
    """Look up the net flow in USD for one month."""
    statements = {"january": "4,820 USD", "february": "3,200 USD"}
    return statements.get(month.lower(), "No statement for that month.")


client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
question = "Compare January and February net flow."
runner = client.beta.messages.tool_runner(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=1024,
    max_iterations=MAX_ITERATIONS,
    system="Use the tool for recorded amounts.",
    tools=[get_net_flow],
    messages=[{"role": "user", "content": question}],
)

# 2 · Record the trajectory while the agent runs: every tool request, then the final text.
tools_called, answer = [], ""
for reply in runner:
    for block in reply.content:
        if block.type == "tool_use":
            tools_called.append(ToolCall(name=block.name, input_parameters=block.input))
            print("Tool requested:", block.name, block.input)
        elif block.type == "text":
            answer = block.text
print("Agent answer:", answer or "(no final answer)")

# 3 · Path: compare called tools with the ones a correct run needs. Outcome: a judge reads the answer.
test_case = LLMTestCase(
    input=question,
    actual_output=answer or "(no final answer)",
    tools_called=tools_called,
    expected_tools=[ToolCall(name="get_net_flow"), ToolCall(name="get_net_flow")],
)
judge = AnthropicModel(
    model=os.getenv("CLAUDE_JUDGE_MODEL", "claude-haiku-5-5"),
    api_key=os.environ["CLAUDE_API_KEY"],
)
evaluate(
    test_cases=[test_case],
    metrics=[
        ToolCorrectnessMetric(model=judge, threshold=1.0),
        TaskCompletionMetric(
            task="Report January and February net flow and state which month was higher.",
            model=judge,
            threshold=0.8,
        ),
    ],
)

# A good run requests get_net_flow twice and compares 4,820 USD with 3,200 USD.
