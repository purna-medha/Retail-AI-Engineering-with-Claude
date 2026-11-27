# Run the same eval cases as a test suite, so every prompt or model change gets re-checked.
# uv run --with deepeval --with anthropic --with python-dotenv --with pytest pytest snippets/m10_test_statement_bot.py -v
import os

import pytest
from anthropic import Anthropic
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

load_dotenv()
STATEMENT = {"month": "2025-01", "total_deposits": 5000, "total_withdrawals": 180,
             "net_flow": 4820, "current_balance": 157840}
SYSTEM_PROMPT = "Answer from the statement JSON in two sentences."

client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


def statement_bot(question: str) -> str:
    """The application under test: the Nano Bank statement assistant."""
    reply = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Statement: {STATEMENT}\n\nQuestion: {question}"}],
    )
    return "".join(block.text for block in reply.content if block.type == "text")


# Each golden is a question plus what a correct answer must say. Include one the data cannot answer.
GOLDENS = [
    ("What was my net flow in January 2025?", "4,820 USD (5,000 deposited minus 180 withdrawn)."),
    ("How much did I withdraw in January 2025?", "180 USD."),
    ("What was my closing balance on 31 January 2025?",
     "The statement has no closing balance for January. 157,840 USD is the balance today, "
     "not the January closing balance."),
]

judge = AnthropicModel(
    model=os.getenv("CLAUDE_JUDGE_MODEL", "claude-haiku-5-5"),
    api_key=os.environ["CLAUDE_API_KEY"],
)
correctness = GEval(
    name="Correctness",
    criteria="The actual output reaches the same conclusion as the expected output: the same figure, "
    "or the same statement that the data is not available. Different wording and extra correct "
    "context are fine. Presenting a different figure as the answer is wrong.",
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT,
                       SingleTurnParams.EXPECTED_OUTPUT],
    model=judge,
    threshold=0.7,
)


@pytest.mark.parametrize("question, expected", GOLDENS)
def test_statement_bot(question, expected):
    test_case = LLMTestCase(input=question, actual_output=statement_bot(question), expected_output=expected)
    assert_test(test_case, [correctness])

# pytest reports one pass/fail per golden; a failure prints the judge's score and reason.
