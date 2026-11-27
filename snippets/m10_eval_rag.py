# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anthropic>=2.10.0",
#     "deepeval>=4.3.6",
#     "fastembed>=0.9.1",
#     "llama-index-core>=0.14.26",
#     "llama-index-embeddings-fastembed>=0.8.0",
#     "python-dotenv>=1.2.4",
# ]
# ///
# Evaluate a RAG app on three questions: did retrieval find the evidence, and did Claude use it well?
import os
from pathlib import Path

from anthropic import Anthropic
from deepeval import evaluate
from deepeval.dataset import Golden
from deepeval.metrics import AnswerRelevancyMetric, ContextualRecallMetric, FaithfulnessMetric
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding

load_dotenv()
TOP_K = 1  # How many excerpts to retrieve. Try 2 and compare the scores.

# 1 · The RAG app from M5: search the policy files, then answer from what was found.
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
documents = SimpleDirectoryReader(input_dir=str(Path(__file__).with_name("rag_policies"))).load_data()
index = VectorStoreIndex.from_documents(documents)
client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])


def rag_app(question: str) -> tuple[str, list[str]]:
    """Return Claude's answer and the excerpts it was given."""
    hits = index.as_retriever(similarity_top_k=TOP_K).retrieve(question)
    print(f"\nQ: {question}\nRetrieved: {[hit.node.metadata['file_name'] for hit in hits]}")
    excerpts = [hit.node.text for hit in hits]
    reply = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=1024,
        system="Answer only from the excerpts. If they don't contain the answer, say so.",
        messages=[{"role": "user", "content": "Excerpts:\n" + "\n\n".join(excerpts) + f"\n\nQuestion: {question}"}],
    )
    answer = "".join(block.text for block in reply.content if block.type == "text")
    return answer, excerpts


# 2 · Goldens: each question with the answer we expect, written before running the app.
answerable = [
    Golden(input="What is the concentration limit?",  # Answered by one file.
           expected_output="No single asset may exceed 35% of total portfolio value."),
    Golden(input="What is the concentration limit, and how is the cash reserve calculated?",  # Needs two files.
           expected_output="No single asset may exceed 35% of total portfolio value. "
           "The cash reserve is available cash divided by total portfolio value."),
]
unanswerable = [Golden(input="What is the daily ATM withdrawal limit?")]  # Not in the files.


# 3 · Run the app on a golden. A RAG test case also records the excerpts Claude saw.
def make_test_case(golden: Golden) -> LLMTestCase:
    answer, excerpts = rag_app(golden.input)
    print(f"A: {answer}")
    return LLMTestCase(input=golden.input, actual_output=answer,
                       expected_output=golden.expected_output, retrieval_context=excerpts)


judge = AnthropicModel(model="claude-haiku-5-5", api_key=os.environ["CLAUDE_API_KEY"])
recall = ContextualRecallMetric(model=judge, threshold=0.7)    # Retrieval: did the excerpts hold every expected fact?
# penalize_ambiguous_claims=True also fails claims the excerpts don't mention, not only ones they contradict.
faithfulness = FaithfulnessMetric(model=judge, threshold=0.7, penalize_ambiguous_claims=True)  # Answer: is every claim backed?
relevancy = AnswerRelevancyMetric(model=judge, threshold=0.7)  # Answer: does it address the question?

# 4 · Answerable questions: check retrieval and the answer.
evaluate(test_cases=[make_test_case(g) for g in answerable], metrics=[recall, faithfulness, relevancy])

# 5 · Unanswerable question: there is no evidence to find, so only check that Claude didn't invent an answer.
evaluate(test_cases=[make_test_case(g) for g in unanswerable], metrics=[faithfulness])

# With TOP_K = 1, the two-file question gets only one policy: recall drops, faithfulness stays high.
# Try: in make_test_case, set answer = "The daily ATM withdrawal limit is 500 USD." Faithfulness fails.
