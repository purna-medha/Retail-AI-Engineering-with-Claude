# Simple LLM eval: one test case, one GEval metric, a Claude judge.
# uv run --with deepeval --with anthropic --with python-dotenv deepeval test run snippets/m10_1_eval_llm_output.py
import os

from anthropic import Anthropic
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])

# The judge model. Without it, GEval tries to use OpenAI.
judge = AnthropicModel(model="claude-haiku-5-5", api_key=os.environ["CLAUDE_API_KEY"])

def nano_bank_assistant(question: str) -> str:
    """The LLM application under test."""
    statement = {"month": "2025-01", "total_deposits": 5000, "total_withdrawals": 180, "net_flow": 4820}
    reply = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=1024,
        system="Answer from the statement JSON in two sentences.",
        messages=[{"role": "user", "content": f"Statement: {statement}\n\nQuestion: {question}"}],
    )
    return "".join(block.text for block in reply.content if block.type == "text")


def test_correctness():
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=0.5,
    )
    question = "What was my net flow in January 2025?"
    test_case = LLMTestCase(
        input=question,
        actual_output=nano_bank_assistant(question),
        expected_output="Net flow was 4,820 USD: 5,000 USD deposited minus 180 USD withdrawn.",
    )
    assert_test(test_case, [correctness_metric])
