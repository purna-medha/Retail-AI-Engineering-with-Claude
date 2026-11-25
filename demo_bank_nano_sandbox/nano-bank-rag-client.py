# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastembed==0.9.1",
#     "httpx==0.28.1",
#     "llama-index-core==0.14.26",
#     "llama-index-embeddings-fastembed==0.8.0",
# ]
# ///
from pathlib import Path

import httpx
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.embeddings.fastembed import FastEmbedEmbedding

# The statement GET from nano-bank-client.py.
url = "http://127.0.0.1:8000/accounts/ACC101/statement/2025/1"
statement = httpx.get(url, timeout=5).raise_for_status().json()
print("Statement month:", statement["month"])
print("Net flow:", statement["net_flow"])
print("Current balance:", statement["current_balance"])

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
documents = SimpleDirectoryReader(
    input_dir=str(Path(__file__).with_name("rag_guides")),
    file_metadata=lambda path: {"source": Path(path).name},
).load_data()
nodes = SentenceWindowNodeParser.from_defaults(window_size=1).get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)

question = "What does current_balance mean, and can I get the January closing balance from this response?"
hit = index.as_retriever(similarity_top_k=1).retrieve(question)[0]
sentence = " ".join(hit.node.get_content().split())
window = " ".join(hit.node.metadata["window"].split())

facts = ["balance when the request runs", "no field for the requested month's closing balance"]
sentence_count = sum(fact in sentence for fact in facts)
window_count = sum(fact in window for fact in facts)
print("\nQuestion:", question)
print("Guide:", hit.node.metadata["source"])
print("Matched sentence:", sentence)
print("Sentence window:", window)
print("Evidence coverage:", sentence_count, "→", window_count, "of", len(facts))
