# M6 · When RAG Gets It Wrong

**AI Engineering with Claude · Tredence**

In M5, we built a RAG pipeline. Today we’ll learn how to spot a failure, choose an improvement, and check whether it helped.

- Evaluate what the system retrieved and what the model answered.
- Understand what chunking, hybrid search, reranking, and query changes can fix.
- Finish with a worked Nano Bank example and a short code-along.

---

# Recall M5 · Follow the question

```text
Question → search the index → selected passages → model answer
```

Before looking at an answer, name what the retriever gives to the model. Where would you look if a rule was missing from the passages?

---

# Where can a RAG answer go wrong?

A RAG system searches a collection, selects passages, and gives them to a model to answer a question.

| What you see | What to check |
| --- | --- |
| The answer leaves out an exception | Did the selected passages include it? |
| The answer adds a claim | Does the evidence support that claim? |
| The system keeps returning unrelated passages | Does the collection contain the answer? |

Start by looking at the evidence the model actually received.

---

# 1 · Evaluate a baseline

A **baseline** is how the current system performs before you change it. Start with a small test set.

For each case, write down the **question**, the **facts the answer must cover**, and the **source that supports them**. Try a direct question, one with a qualifier, and one the sources cannot answer.

Run the tests and keep both the retrieved passages and the generated answers. You’ll use the same cases after making a change.

---

# Check retrieval before reading the answer

- **Context recall** asks whether the search brought back all the evidence the answer needs.
- **Context precision** asks how well the search ranks relevant passages ahead of irrelevant ones.

Suppose a question needs a rule and an exception. The top two passages contain the rule and an unrelated example. Only one of the two facts is covered. Raising the score of the rule would still leave the exception missing.

**Check.** What would you look for in the next search?

---

# Check what the model does with the evidence

**Faithfulness** asks whether the passages support the answer. **Relevance** asks whether the answer addresses the question.

The guide says, “On Friday, support is open from 9 a.m. to 5 p.m.” The question asks when it closes.

| Answer | Faithful? | Relevant? |
| --- | --- | --- |
| “It opens at 9 a.m.” | Yes | No |
| “It closes at 6 p.m.” | No | Yes |
| “It closes at 5 p.m.” | Yes | Yes |

**Try it.** How would you score “5 p.m., except on holidays” using only the guide above?

---

# 2 · Choose a chunk that holds a useful fact

A **chunk** is the piece of a document the system searches. Its boundaries affect what the model sees.

| Chunk shape | What can happen |
| --- | --- |
| A short fragment | It matches closely but leaves out an exception |
| A long section with several topics | It contains the answer alongside unrelated details |
| A rule and its qualifier together | The answer can cite both from the same passage |

When a relevant hit provides only part of the answer, inspect where the chunk starts and ends.

---

# Search a sentence and answer from its window

**Sentence-window chunking** searches individual sentences. After finding a match, it adds nearby sentences to the context supplied for answering.

```text
Search using     → matched sentence
Answer using     → previous sentence + match + next sentence
```

A window of one takes one neighbor on each side when available. Use it when nearby text explains a rule, gives a condition, or states an exception.

**Check.** Would this help if the exception lived in a separate document?

---

# 3 · Combine semantic and keyword search

**Semantic search** compares embeddings to find passages with related meaning. **Keyword search** ranks passages that match the words or identifiers in the question. BM25 is one common keyword ranking method.

| Question | A helpful search signal |
| --- | --- |
| “Why was my payment refused?” | Similar meaning to “payment declined” |
| “What does error `422` mean?” | The exact error code |

**Hybrid search** combines the candidates from both. Try it when exact names, IDs, or codes matter and semantic search misses them.

---

# 4 · Rerank the candidates you already found

A **reranker** is a second scoring step. First retrieve a set of candidates. Then compare those passages with the question again and keep the strongest few.

Suppose the explanation you need is ranked fourth and the model only receives the top two. A reranker can move that explanation up if it has been included in its candidate set.

**Check.** If the explanation never appears in the candidate set, which stage should you inspect?

---

# 5 · Improve the question you search with

A user's question can be clear to a person and still be hard to search for. Preserve the intended question while preparing useful searches.

| Technique | What it does |
| --- | --- |
| Query rewriting | Adds the subject to a vague question, such as “What does that field mean?” |
| Decomposition | Splits a question that asks for two separate facts |
| HyDE | Drafts a hypothetical answer to use as search text |

The retrieved sources support the final answer. A hypothetical answer helps guide the search.

---

# Match the change to the failure

| What you found in the baseline | What to try |
| --- | --- |
| The match cuts off a nearby qualification | Expand the chunk or use a sentence window |
| Search misses a passage with the exact field name | Add keyword search |
| The right passage is present but ranked too low | Rerank the candidates |
| The question combines two tasks | Decompose the search |
| The excerpts contain the facts but the answer changes them | Check the answer instructions and generation |

Make one change and rerun the same cases.

---

# Worked example · Read the Nano Bank statement

The bank client requests `GET /accounts/ACC101/statement/2025/1`. The server calculates totals for January and also reports the current account balance.

| Field | What it tells you |
| --- | --- |
| `month` | The statement period, `2025-01` |
| `net_flow` | The January net inflow, **$4,820** in the classroom seed |
| `current_balance` | The balance at the time of the request |

The API is the source for account figures. A statement guide can explain how to interpret the fields. [Client request](../demo_bank_nano_sandbox/nano-bank-client.py) · [Statement implementation](../demo_bank_nano_sandbox/nano-bank.py)

---

# Worked example · Write the expected facts

**Question** “What does `current_balance` mean, and can I get January's closing balance from this response?”

A short statement guide based on the API would say:

> The field current_balance shows the account balance when the request runs. The API response has no field for the requested month's closing balance.

Write down both facts before running retrieval. In a separate missing-evidence case, ask how to request an overdraft. This guide covers statement fields and gives no overdraft process.

---

# Worked example · Diagnose the missing half

Suppose the best hit is this sentence:

> The field current_balance shows the account balance when the request runs.

It supports the first half of the answer. The next sentence supplies the missing fact about the closing-balance field.

| Evidence sent | Facts supported |
| --- | --- |
| Matched sentence | 1 of 2 |
| Matched sentence and its neighbor | 2 of 2 |

A sentence window fits the observed failure. The question, retriever, and requested answer stay the same.

---

# Your turn · Find where the failure belongs

Write down what you would inspect or change first.

| What happened | Decide where to look |
| --- | --- |
| The passage explains `current_balance`, but the answer calls it January's closing balance | What did the model do with the passage? |
| The guide contains `422`. Search returns only passages about `409` | What signal could help find the right passage? |
| The right passage ranks fourth. The model receives only the first two | What could improve the order of the candidates? |

Explain your choice. Check it against the debrief after the code-along.

---

# Code-along · Predict the result first

The [standalone snippet](../snippets/3_advanced_rag.py) lets you try the same idea with the [classroom portfolio policy](../snippets/rag_policies/portfolio-policy.md).

**Question** “Is a position at exactly 35% allowed, and what happens above the limit?”

Before running the code, write two predictions. Which fact might appear in a single sentence? Which fact needs a neighboring sentence? Then locate both in the policy.

---

# Code-along · Run it and inspect the evidence

Set `CLAUDE_API_KEY` in the repo's `.env`. From the repository root, install the dependencies once and run the snippet.

```bash
uv add anthropic fastembed llama-index-core llama-index-embeddings-fastembed python-dotenv
uv run snippets/3_advanced_rag.py
```

| Output | What to notice |
| --- | --- |
| Matched sentence | Exactly 35% is within the limit |
| Sentence window | The next sentence adds that positions above the limit are flagged for manual review |
| Claude answer | Check whether it includes both facts and cites the policy |

The script searches locally and sends the selected window to Claude. The first run downloads the embedding model. Make a copy in `snippets/` before editing.

---

# Code-along · Find the change in the code

```python
parser = SentenceWindowNodeParser.from_defaults(window_size=1)
nodes = parser.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes)
hit = index.as_retriever(similarity_top_k=1).retrieve(question)[0].node

matched_sentence = hit.text
answer_window = hit.metadata["window"]
```

Find the line that retrieves the sentence and the line that reads its window. The script sends `answer_window` and the question through `client.messages.create(...)`.

---

# Code-along · Turn the evidence check into code

First score both outputs by hand. Then append this check to your copy of the script.

```python
facts = ["exactly 35% is within the limit", "flagged for manual review"]
sentence = " ".join(matched_sentence.split())
window = " ".join(answer_window.split())

print("Facts in the sentence:", sum(fact in sentence for fact in facts), "of", len(facts))
print("Facts in the window:", sum(fact in window for fact in facts), "of", len(facts))
```

Expect **1 of 2** and **2 of 2**. This check looks for exact phrases from the fixed policy. When text paraphrases a fact, inspect the meaning by hand.

---

# Mini lab · Change one parameter

Keep the question and `similarity_top_k=1` fixed. Change `window_size=1` to `window_size=2`.

1. Predict whether the matched sentence, the window, or both will change.
2. Rerun and compare what the code printed.
3. Score the same two facts again. Did the extra context add a fact this question needed?

---

# Your turn · Write a new test

Reset the window to one. Change the `question` to “How is the cash reserve calculated, and when do we flag it for manual review?” Update the phrase check for this question or score the evidence by hand.

1. Write the two expected facts and the expected source.
2. Run the script. Score the matched sentence and window by hand.
3. Try “What is the account maintenance fee?” Find out what the closest passage actually supports.

**Done when** you can show one improvement and one case that needs a new source.

---

# Run one small snippet for each concept

Run these from the repository root. Predict what changes before each run.

| Concept and snippet | Command | Look for |
| --- | --- | --- |
| [Evaluation](../snippets/rag_evaluate.py) | `uv run snippets/rag_evaluate.py` | Inspect the actual retrieved evidence and compare Claude's answer with the expected facts |
| [Sentence windows](../snippets/3_advanced_rag.py) | `uv run snippets/3_advanced_rag.py` | The neighbor adds the missing fact |
| [Hybrid search](../snippets/rag_hybrid_search.py) | `uv run snippets/rag_hybrid_search.py` | The exact match adds rule `DQ-042` to the evidence Claude sees |
| [Reranking](../snippets/rag_rerank.py) | `uv run snippets/rag_rerank.py` | Claude ranks the candidates, then answers using the top result |
| [Query decomposition](../snippets/rag_query_decomposition.py) | `uv run snippets/rag_query_decomposition.py` | Two searches supply separate facts for one answer |

In each snippet, find the LlamaIndex retrieval step and the `client.messages.create(...)` call that sends the selected evidence to Claude.

---

# Nano Bank lab · Put retrieval beside the statement GET

Start the bank API.

```bash
cd demo_bank_nano_sandbox
uv run uvicorn nano-bank:app --host 127.0.0.1 --port 8000
```

From the repository root in a second terminal, run the [lab client](../demo_bank_nano_sandbox/nano-bank-rag-client.py).

```bash
uv run demo_bank_nano_sandbox/nano-bank-rag-client.py
```

The client reads January's statement and searches the [statement guide](../demo_bank_nano_sandbox/rag_guides/statement-fields.md). Find **4,820** in the API's net flow and **1 → 2 of 2** in the evidence check. Explain which source supplies each result.

---

# Nano Bank lab · Add one more technique

Make a copy of the lab client in the same folder. Use one standalone snippet as a model. Keep the statement GET for the account figures.

| Try this | Change to make | Check |
| --- | --- | --- |
| “What does HTTP 422 mean for a withdrawal?” | Merge the semantic hits with passages that contain `422` | The [withdrawal guide](../demo_bank_nano_sandbox/rag_guides/withdrawal-errors.md) explains validation and the amount rule |
| Compare candidates for the same question | Retrieve three passages and ask Claude to pick the most relevant one | Record the first passage before and after |
| “How much did I deposit in January, and why would a withdrawal return 422?” | Split it into an API lookup and a guide search | `total_deposits` supplies 5,000. The guide supplies the error explanation. |

**Done when** you can show what your change did to the retrieved evidence and cite the source for each fact.

---

# Debrief · Check your decisions

| Exercise | What you should see |
| --- | --- |
| Friday support hours | The guide supports 5 p.m. It gives no holiday rule. |
| Nano Bank diagnosis | Check generation when the right fact was supplied. Try keyword search for `422`. Try reranking when the useful passage is already a candidate. |
| Change the window to two | The matched sentence stays the same. The window is longer and still covers two of two facts. |
| Cash reserve test | `cash-policy.md` explains the calculation and manual review below 5%. |
| Maintenance fee | The nearest passage gives no maintenance fee. The test needs a fee schedule to support an amount. |

**Exit check.** Explain one case where you would change the search and one where you would check the answer instructions.

Use the same evidence check when you evaluate a tool's output in the agents lecture.
