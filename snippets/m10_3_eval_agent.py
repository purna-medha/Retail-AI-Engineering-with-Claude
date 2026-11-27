# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anthropic<2",  # The LlamaIndex adapter expects the pre-2.0 message types.
#     "deepeval>=4.3.6",
#     "llama-index-core>=0.14.26",
#     "llama-index-llms-anthropic>=0.13.0",
#     "python-dotenv>=1.2.4",
# ]
# ///
# Evaluate the M8 agent on a dataset of goldens. DeepEval traces each run and a judge scores it.
import asyncio
import os

import llama_index.core.instrumentation as instrument
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.integrations.llama_index import instrument_llama_index
from deepeval.metrics import TaskCompletionMetric
from deepeval.models import AnthropicModel
from dotenv import load_dotenv
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic

load_dotenv()

# 1 · Tracing: record every LLM call and tool call the agent makes.
instrument_llama_index(instrument.get_dispatcher())


# 2 · The agent under test: the M8 net-flow agent.
def get_net_flow(month: str) -> str:
    """Look up the net flow in USD for one month."""
    statements = {"january": "4,820 USD", "february": "3,200 USD"}
    return statements.get(month.lower(), "No statement for that month.")


agent = FunctionAgent(
    tools=[get_net_flow],  # Try tools=[]: what does the judge say now?
    llm=Anthropic(model="claude-haiku-5-5", api_key=os.environ["CLAUDE_API_KEY"], max_tokens=1024),
    system_prompt="Use the tool for recorded amounts.",
)

# 3 · Goldens: the questions to run. The agent produces the answers during the eval.
dataset = EvaluationDataset(goldens=[
    Golden(input="What was January's net flow?"),
    Golden(input="Compare January and February net flow."),
    Golden(input="What does net flow mean?"),  # No lookup needed.
])

# 4 · The judge reads each trace: the task, the tool calls, and the final answer.
judge = AnthropicModel(model="claude-haiku-5-5", api_key=os.environ["CLAUDE_API_KEY"])
task_completion = TaskCompletionMetric(model=judge, verbose_mode=True)

for golden in dataset.evals_iterator(metrics=[task_completion]):
    task = asyncio.create_task(agent.run(golden.input))
    dataset.evaluate(task)

# The verbose logs show what the judge saw: "invoked get_net_flow with month 'January' ..."
# Try adding Golden(input="Compare January and March net flow.") and run twice: March has no statement.
