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
semantic_hit = index.as_retriever(similarity_top_k=1).retrieve(question)[0].node
keyword_hits = [node for node in nodes if "DQ-042" in node.text]

# Combine both searches and keep one copy of each hit.
hybrid_hits = list({node.node_id: node for node in keyword_hits + [semantic_hit]}.values())
context = "\n\n".join(node.text for node in hybrid_hits)
print("Question:", question)
print("Semantic match:", semantic_hit.text)
print("Hybrid evidence:", [node.text for node in hybrid_hits])

client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
response = client.messages.create(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=256,
    system="Answer from the excerpts. Cite a rule ID when available. Say if evidence is missing.",
    messages=[{"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"}],
)
print("Claude:", response.content[0].text)
