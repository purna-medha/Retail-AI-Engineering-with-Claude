# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anthropic<2",  # The LlamaIndex adapter expects the pre-2.0 message types.
#     "llama-index-core>=0.14.26",
#     "llama-index-llms-anthropic>=0.13.0",
#     "python-dotenv>=1.2.4",
# ]
# ///
import asyncio
import os

from dotenv import load_dotenv
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic

load_dotenv()


def get_net_flow(month: str) -> str:
    """Look up the net flow in USD for one month."""
    statements = {"january": "4,820 USD", "february": "3,200 USD"}
    amount = statements.get(month.lower(), "No statement for that month.")
    print("Tool result:", month, amount)
    return amount


llm = Anthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    api_key=os.environ["CLAUDE_API_KEY"],
    max_tokens=1024,
)
agent = FunctionAgent(
    llm=llm,
    tools=[get_net_flow],
    streaming=False,
    allow_parallel_tool_calls=False,
    system_prompt="Use the tool for recorded amounts.",
)


async def main():
    answer = await agent.run("Compare January and February net flow.", max_iterations=4)
    print("Claude:", answer)


asyncio.run(main())
