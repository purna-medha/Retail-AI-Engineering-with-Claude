# RAG with LlamaIndex and Claude

**AI Engineering with Claude · Tredence**

Start with a question and a policy excerpt. Then build the steps that find that excerpt automatically and give it to Claude.

- Find evidence in a small document collection.
- Explain what each line of the RAG snippet does.
- Check an answer against the retrieved text.

---

# Some questions need your own documents

In M2, the chatbot fetched a statement from a known API route. Other questions require finding the right passage before the model can answer.

| Question | Where to look |
| --- | --- |
| How do I dispute a charge? | Support policies |
| What counts as a late delivery? | The Orders KPI definition |
| What is the concentration limit? | The classroom portfolio policy |

**Ask the room.** Which of these answers might change when somebody updates a document?

---

# Give Claude one useful excerpt

Start with the question alone. Then add the source and ask again.

```text
Source: portfolio-policy.md
No single asset may exceed 35% of total portfolio
value in this simulation.

Question: What is the concentration limit?
Answer using the excerpt and name the source.
```

Expect **35% per asset** and `portfolio-policy.md`. Point to the line that supports the answer. If you only had the cash policy, what could you answer?

---

# RAG automates the search for context

**Retrieval-augmented generation** adds a search step before the model answers.

```text
Question → find relevant passages → send question and passages to Claude
```

A person selected the excerpt on the previous slide. In RAG, the application selects it from a document collection for each question. Claude uses the resulting text to write the answer.

---

# Try the search first

Copy [2_rag.py](../snippets/2_rag.py) to `snippets/2_rag_search.py`. In the copy, remove the `Settings.llm = Anthropic(...)` block. Replace the last three lines with a search and a print.

```python
hits = index.as_retriever(similarity_top_k=2).retrieve(question)
print(hits[0].node.metadata["source"])
print(hits[0].node.get_content())
```

```bash
uv run snippets/2_rag_search.py
```

This runs without a Claude key. The first run downloads the local embedding model. Find the concentration rule in the excerpt from `portfolio-policy.md`.

---

# Two things happen at different times

| Prepare the collection | Answer a question |
| --- | --- |
| Load documents | Embed the question |
| Split documents into chunks | Find similar chunks |
| Embed and index the chunks | Send the selected text and question to Claude |

The classroom script builds the index in memory each time it starts. An application can reuse an index for multiple questions and update it when the source documents change.

---

# 1 · Load the documents

The [fixture folder](../snippets/rag_policies/) has two short Markdown files with fictional policy rules. LlamaIndex reads each file into a document object.

```python
documents = SimpleDirectoryReader(
    input_dir=str(policy_dir),
    file_metadata=lambda path: {"source": Path(path).name},
).load_data()
```

The reader gives us the text and a filename. The filename travels with the text so a learner can check an answer against the original source.

---

# 2 · Split documents into chunks

A **chunk** is the unit the application searches and retrieves. A long policy may contain separate rules for limits, exceptions, and review steps.

```text
Portfolio policy
  → Concentration limit and its conditions
  → What to record during a review
```

Keep a rule and its important qualifier together when possible. Our policy gives the limit and says **exactly 35% is allowed**. A chunk that drops that sentence may fail on a boundary question.

---

# 3 · Turn text into embeddings

An **embedding** is a list of numbers that represents text. The same embedding model converts chunks and questions, so the index can compare their vectors.

```python
Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
```

FastEmbed runs the embedding model locally after the first download. Claude has a separate job later, writing the answer. [LlamaIndex FastEmbed guide](https://developers.llamaindex.ai/python/framework/integrations/embeddings/fastembed/)

---

# 4 · Build a searchable index

```python
index = VectorStoreIndex.from_documents(documents)
```

With the embedding model configured, LlamaIndex splits the documents and embeds the chunks. The in-memory index lets the retriever find similar vectors and get back the matching text and source.

**Check.** If the concentration rule changes in the file, when will this script see the new value?

---

# 5 · Retrieve a few candidates

```python
retriever = index.as_retriever(similarity_top_k=2)
hits = retriever.retrieve(question)
```

`top_k` is how many candidates to return at most. Inspect the **text**, **source**, and **score** of each hit. A higher score ranks a passage above other candidates for this search. Whether it answers the question depends on what the passage says.

**Try it.** Compare the excerpts after changing the question to “What is the cash reserve?”

---

# 6 · Give Claude the retrieved text

The query engine supplies the selected excerpts and the question. The demo’s system instruction tells Claude how to use them.

```text
Answer from the policy excerpts. Cite the source filename.
If the excerpts do not answer the question, say so.
```

Ask “What is the minimum account balance?” The collection has no account-balance rule. A search may still return a nearest passage. Check whether it actually supports an answer.

---

# Claude is the generation model

```python
Settings.llm = Anthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    api_key=os.environ["CLAUDE_API_KEY"],
    system_prompt="Answer from the policy excerpts. Cite the source filename. "
    "If the excerpts do not answer the question, say so.",
)
```

`Settings.embed_model` was for search. `Settings.llm` tells LlamaIndex which model writes the answer.

---

# Run the complete RAG query

With a working `CLAUDE_API_KEY` in the repository’s `.env`, run from the repository root.

```bash
uv run snippets/2_rag.py
```

```python
response = index.as_query_engine(similarity_top_k=2).query(question)
print(response)
print("Sources:", [hit.node.metadata["source"] for hit in response.source_nodes])
```

Expect **35% per asset**. Check that the answer’s citation names a source that contains the rule. The printed source list shows the excerpts the engine worked with.

---

# The whole pipeline in four lines

Once Claude and the embedding model are configured, this is the flow.

```python
documents = SimpleDirectoryReader(input_dir=str(policy_dir)).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=2)
response = query_engine.query(question)
```

The reader loads the source. The index prepares it for search. The query engine searches and asks Claude to answer. The runnable snippet also keeps a short source label for each file.

---

# Open up the index when you need to inspect a step

The [detailed notes](../snippets/2_rag.md) show the splitter and retriever. In a copy of the runnable script, import `SentenceSplitter` from `llama_index.core.node_parser` and try these lines after `documents` and `question` are defined.

```python
splitter = SentenceSplitter(chunk_size=80, chunk_overlap=10)
nodes = splitter.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)
hits = index.as_retriever(similarity_top_k=2).retrieve(question)
```

Print `len(documents)`, `len(nodes)`, and the text of the first hit. **Which object holds the text Claude could use?**

---

# Mini lab · Check a known answer and a missing one

Change the `question` line in the search copy and inspect the evidence. With Claude configured, try the same question in `2_rag.py` and check its answer against the excerpts.

| Try this question | What to check |
| --- | --- |
| Can a single asset be 42% of the portfolio? | The 35% limit supports “no.” |
| What is the cash reserve? | `cash-policy.md` says at least 5%. |
| What is the minimum account balance? | Neither file specifies it. |

**Done when** you can point to the supporting line or explain what evidence is missing.

---

# Debrief · Where did it fail?

| What you observe | First place to look |
| --- | --- |
| The right rule is absent from the hits | Search or chunk boundaries |
| The hits contain the rule, but the answer changes the number | Grounding instruction or generation |
| The collection contains no rule | Missing source material and the response to missing evidence |

Change one thing. For example, compare `similarity_top_k=1` with `similarity_top_k=2` on the same question. Inspect which passages changed before judging the answer.
