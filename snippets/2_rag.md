## Simple
documents = SimpleDirectoryReader(input_dir=str(POLICY_DIR)).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("What is the concentration limit?")

print(response)
print("sources:", [node.node.metadata.get("file_name") for node in response.source_nodes])
print("Runtime:", runtime_evidence(llm))


## Detailed
documents = SimpleDirectoryReader(input_dir=str(POLICY_DIR)).load_data()
splitter = SentenceSplitter(chunk_size=80, chunk_overlap=10)
nodes = splitter.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)
retriever = index.as_retriever(similarity_top_k=2)
query_engine = index.as_query_engine(similarity_top_k=2)

print("documents:", len(documents))
print("nodes:", len(nodes))
print("index:", type(index).__name__)
print("retriever:", type(retriever).__name__)
print("query_engine:", type(query_engine).__name__)
