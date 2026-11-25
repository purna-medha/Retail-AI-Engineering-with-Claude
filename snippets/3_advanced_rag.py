# uv add anthropic fastembed llama-index-core llama-index-embeddings-fastembed python-dotenv

import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.embeddings.fastembed import FastEmbedEmbedding

load_dotenv()
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
policy_dir = Path(__file__).with_name("rag_policies")

documents = SimpleDirectoryReader(input_dir=str(policy_dir)).load_data()
parser = SentenceWindowNodeParser.from_defaults(window_size=1)
nodes = parser.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)

question = "How many perishable items to I have, and what is the policy for them?"
hit = index.as_retriever(similarity_top_k=1).retrieve(question)[0].node
matched_sentence = hit.text
answer_window = hit.metadata["window"]
source = hit.metadata["file_name"]

print("Question:", question)
print("Matched sentence:", matched_sentence)
print("Sentence window:", answer_window)

client = Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
response = client.messages.create(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=256,
    system="Answer from the excerpt. Cite the source. Say if evidence is missing.",
    messages=[{"role": "user", "content": f"Source: {source}\n{answer_window}\n\nQuestion: {question}"}],
)
print("Claude:", response.content[0].text)
print("Source:", source)
