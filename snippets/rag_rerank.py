# uv add anthropic fastembed llama-index-core llama-index-embeddings-fastembed python-dotenv

import os

from anthropic import Anthropic
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.fastembed import FastEmbedEmbedding

load_dotenv()
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
nodes = [
    TextNode(text="Review order totals when the customer reports a discrepancy.", metadata={"source": "Support guide"}),
    TextNode(text="DQ-042: Quarantine the row and open a data quality ticket.", metadata={"source": "DQ-042"}),
    TextNode(text="DQ-024: Accept the row when the amount matches quantity times price.", metadata={"source": "DQ-024"}),
]
index = VectorStoreIndex(nodes)
question = "What should happen when an order total is wrong? DQ-042"
candidates = index.as_retriever(similarity_top_k=3).retrieve(question)
print("Question:", question)
print("Search order:", [hit.node.metadata["source"] for hit in candidates])

choices = {str(number): hit.node.text for number, hit in enumerate(candidates, start=1)}
passages = "\n".join(f"{number}. {text}" for number, text in choices.items())
client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
model = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

# Ask Claude to select the most relevant candidate, then answer from that passage.
ranking = client.messages.create(
    model=model,
    max_tokens=32,
    system="Choose the passage that best answers the question. Reply with only its number.",
    messages=[{"role": "user", "content": f"Question: {question}\n\nPassages:\n{passages}"}],
)
number = ranking.content[0].text.strip()
if number not in choices:
    raise ValueError(f"Expected one passage number. Claude returned {number!r}.")
context = choices[number]
print("Reranked evidence:", context)

response = client.messages.create(
    model=model,
    max_tokens=256,
    system="Answer from the excerpt. Cite a rule ID when available. Say if evidence is missing.",
    messages=[{"role": "user", "content": f"Excerpt:\n{context}\n\nQuestion: {question}"}],
)
print("Claude:", response.content[0].text)
