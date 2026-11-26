# uv add anthropic python-dotenv
import os

from anthropic import Anthropic, beta_tool
from dotenv import load_dotenv

load_dotenv()

@beta_tool
def get_net_flow(month: str) -> str:
    """Look up the net flow in USD for one month."""
    statements = {"january": "4,820 USD", "february": "3,200 USD"}
    amount = statements.get(month.lower(), "No statement for that month.")
    print("Tool result:", month, amount)
    return amount


client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
question = "Compare January and February net flow."
runner = client.beta.messages.tool_runner(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=1028,
    max_iterations=4,
    system="Use the tool for recorded amounts.",
    tools=[get_net_flow],
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=[{"role": "user", "content": question}],
)

for reply in runner:
    print("Claude turn:", reply.stop_reason)
    if reply.stop_reason == "end_turn":
        answer = "\n".join(block.text for block in reply.content if block.type == "text")
        print("Claude:", answer)
