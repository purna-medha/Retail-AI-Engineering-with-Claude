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
question = "What was January's net flow?"
runner = client.beta.messages.tool_runner(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=128,
    max_iterations=4,
    system="Use the tool for recorded amounts.",
    tools=[get_net_flow],
    messages=[{"role": "user", "content": question}],
)

answer = runner.until_done()
if answer.stop_reason == "end_turn":
    print("Claude:", answer.content[0].text)
else:
    print("Claude stopped:", answer.stop_reason)
