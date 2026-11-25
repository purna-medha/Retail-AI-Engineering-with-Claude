# uv add anthropic fastembed llama-index-core llama-index-embeddings-fastembed python-dotenv

import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding

load_dotenv()
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
policy_dir = Path(__file__).with_name("rag_policies")
documents = SimpleDirectoryReader(input_dir=str(policy_dir)).load_data()
index = VectorStoreIndex.from_documents(documents)
retriever = index.as_retriever(similarity_top_k=1)
question = "What is the concentration limit and how is the cash reserve calculated?"
print("Question:", question)
print("Single search:", retriever.retrieve(question)[0].node.metadata["file_name"])

# Write one focused query for each fact the original question needs.
queries = ["What is the concentration limit?", "How is the cash reserve calculated?"]
hits = [retriever.retrieve(query)[0] for query in queries]
print("Split search:", [hit.node.metadata["file_name"] for hit in hits])
context = "\n\n".join(f"{hit.node.metadata['file_name']}:\n{hit.node.text}" for hit in hits)

client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
response = client.messages.create(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=256,
    system="Answer from the excerpts. Cite the source. Say if evidence is missing.",
    messages=[{"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"}],
)
print("Claude:", response.content[0].text)
