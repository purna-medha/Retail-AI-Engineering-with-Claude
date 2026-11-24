# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "anthropic==0.79.0",
#     "fastembed",
#     "llama-index-core==0.14.26",
#     "llama-index-embeddings-fastembed==0.8.0",
#     "llama-index-llms-anthropic==0.13.0",
#     "python-dotenv==1.2.4",
# ]
# ///
import os
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.llms.anthropic import Anthropic

load_dotenv()
Settings.llm = Anthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    api_key=os.environ["CLAUDE_API_KEY"],
    system_prompt="Answer from the policy excerpts. Cite the source filename. "
    "If the excerpts do not answer the question, say so.",
)
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

policy_dir = Path(__file__).with_name("rag_policies")
documents = SimpleDirectoryReader(
    input_dir=str(policy_dir),
    file_metadata=lambda path: {"source": Path(path).name},
).load_data()
index = VectorStoreIndex.from_documents(documents)

question = "What is the concentration limit?"
response = index.as_query_engine(similarity_top_k=2).query(question)
print(response)
print("Sources:", [hit.node.metadata["source"] for hit in response.source_nodes])
