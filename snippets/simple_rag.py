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
)
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

POLICY_DIR = Path(__file__).with_name("rag_policies")

documents = SimpleDirectoryReader(input_dir=str(POLICY_DIR)).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What is the concentration limit?")
print(response)
