# M10 · Evaluate LLM, RAG, and Agent Outputs with DeepEval

Turn "it looked right when I tried it" into a check you can repeat after every change.

- Write a test case that says what a correct answer must contain.
- Score a plain answer, a RAG answer, and an agent run with DeepEval.
- Read a score and a reason, and decide what to change in the application.

| Part | What you learn |
| --- | --- |
| 0 · Why evaluate | What goes wrong in AI applications |
| 1 · Core concepts | Test cases, goldens, judges, pass marks |
| 2 · The DeepEval toolkit | Which DeepEval class does each job |
| 3 · Three applications | A plain answer, RAG, and an agent: concept → feature → working example |
| 4 · Put it to work | A test suite, a lab, and the improvement loop |

<!-- Builds on M2 (the statement assistant), M6 (retrieval and faithfulness checks), and M8 (the net-flow agent). Every snippet runs on its own with uv. -->

---

# Part 0 · An answer that sounds right and is wrong

The Nano Bank statement assistant gets the January statement JSON and a question.

```text
Q: What was my closing balance on 31 January 2025?
Statement fields: total_deposits, total_withdrawals, net_flow, current_balance = 157840
```

The assistant answered that January’s closing balance was **157,840 USD**.

That number is `current_balance`: the balance **today**, not on 31 January. The statement has no closing-balance field. The answer is fluent, confident, and wrong, and nothing crashed. By the end of this module, a test will catch it.

---

# A demo that worked once is not evidence

| What you did | What you know |
| --- | --- |
| Asked one question and liked the answer | That answer looked right on that run. |
| Changed the prompt and tried again | Nothing about the questions you didn't retry. |
| Ran the same questions with written expectations | Which cases pass, which fail, and why. |

Model output varies between runs, and a prompt fix for one question can break another. An **evaluation** runs fixed cases against written expectations, so you can compare one version with the next.

---

# What goes wrong in AI applications

| Failure | Nano Bank example | Where M10 catches it |
| --- | --- | --- |
| Confident but wrong | Today’s balance called January’s closing balance | 3a, Part 4 |
| Varies between runs | The same correct answer is worded differently each time, so `==` breaks | 3a |
| Retrieval missed the evidence | Only one of two policies reached Claude | 3b |
| Invented a fact | A made-up ATM limit | 3b |
| Agent skipped a step | Answered without looking up the amounts | 3c |
| Plumbing | A reply cut off by `max_tokens` | Part 4 |

Ordinary software fails loudly with an error. AI applications often fail quietly with a plausible answer. That is why they need evaluations, not only crash checks.

---

# Three things to evaluate, three different questions

| Application | Question the evaluation answers |
| --- | --- |
| Single model call (M2) | Is the answer correct and on topic? |
| RAG (M5–M6) | Did retrieval find the evidence? Did the answer stay inside it? |
| Agent (M8) | Did it take a sensible path? Did it finish the task? |

Each row adds fields to the same test case. The rest of the module follows this order.

---

# Part 1 · A test case says what correct looks like

| Field | Nano Bank example |
| --- | --- |
| **Input** | “What was my net flow in January 2025?” |
| **Actual output** | What the application answered on this run |
| **Expected output** | “4,820 USD: 5,000 deposited minus 180 withdrawn.” |
| **Evidence** *(RAG)* | The excerpts the model was given |
| **Trace** *(agents)* | The tool calls the agent made and what they returned |

Write the expected output **before** you look at the actual one. Otherwise the expectation drifts toward whatever the model said.

---

# Goldens: write the expectations before you run

| Term | What it holds | Who writes it |
| --- | --- | --- |
| **Golden** | An input, and optionally the expected output | You, before running the app |
| **Dataset** | A list of goldens | You |
| **Test case** | A golden plus the actual output from one run | The evaluation, each time it runs |

The goldens stay fixed. Each evaluation runs the current app on every golden and builds fresh test cases, so you can compare one version with the next.

Write goldens from the data, not from the model’s answers. A golden copied from a model reply only tests that the model agrees with itself.

---

# Check with code first, use a judge for meaning

| Check | Use when | Example |
| --- | --- | --- |
| **Deterministic** | The rule is exact | Did the agent call `get_net_flow`? Does the reply contain “4,820”? |
| **LLM-as-judge** | Correctness depends on meaning | Does the reply explain net flow as deposits minus withdrawals? |

A **judge** is a second model call that reads the test case and returns a score with a reason. It costs tokens, takes seconds, and can be wrong, so keep exact rules in code.

**Check.** “Net flow was $4,820” and “4,820 USD” mean the same. Which kind of check accepts both?

---

# A metric turns a check into a score

| Part | Question | Example |
| --- | --- | --- |
| **Criteria** | What counts as correct? | “States the same net flow and explains it as deposits minus withdrawals” |
| **Checker** | Who applies the criteria? | Code (exact rules) or a judge model (meaning) |
| **Pass mark** | How high must the score be? | 0.7 |
| **Result** | What comes back? | A score from 0 to 1, pass or fail, and a reason |

Read the **reason** before the score. It tells you what the checker actually looked at.

---

# The pass mark is a business decision

A correctness score of **0.6** passes at a pass mark of 0.5 and fails at 0.7. The answer didn’t change; the decision did.

| Use case | Cost of a wrong answer | Pass mark |
| --- | --- | --- |
| Suggesting a blog title | Low | Lower |
| Explaining a bank statement | A customer acts on a wrong figure | Higher |

DeepEval’s default pass mark is **0.5**. Choose one deliberately for each metric. In the RAG section, the default would pass an answer missing half its evidence.

---

# The judge can be wrong

A judge is a model. It can be inconsistent, and a metric can test something narrower than its name suggests.

| Risk | What it looks like |
| --- | --- |
| Vague criteria | The same correct answer passes on one run and fails on the next |
| A metric checks less than you assumed | A metric passes a wrong answer because it only checks one property |
| Borderline cases | The result flips because the expectation was never written down |

**Before you trust a metric:**

1. Watch it **fail** on an answer you know is wrong.
2. Watch it **pass** on an answer you know is right.
3. Run it twice. If the result flips, write clearer criteria or use a larger judge.

Every section in Part 3 includes a “make it fail” step for this reason.

---

# Part 2 · DeepEval runs both kinds of check

[DeepEval](https://deepeval.com/docs/getting-started) is an open-source Python library for testing LLM applications.

```text
LLMTestCase  +  metric (criteria + judge model + threshold)
                         ↓
      assert_test(...)  or  evaluate(...)
                         ↓
         score 0–1   ·   passed?   ·   reason
```

A metric **passes** when its score reaches its **threshold**. Some metrics compute the score in code. Others ask the judge model.

---

# Each concept has a DeepEval class

| Concept (Part 1) | DeepEval | Used in |
| --- | --- | --- |
| Test case | `LLMTestCase` | 3a, 3b, Part 4 |
| Golden, dataset | `Golden`, `EvaluationDataset` | 3b, 3c |
| Judge model | `AnthropicModel` | Everywhere |
| Metric with your own criteria | `GEval` | 3a, Part 4 |
| Built-in metrics | `AnswerRelevancyMetric`, `ContextualRecallMetric`, `FaithfulnessMetric`, `TaskCompletionMetric` | 3a, 3b, 3c |
| Run as a pytest test | `assert_test` + `deepeval test run` | 3a, Part 4 |
| Run a list of test cases | `evaluate` | 3b |
| Run an agent on a dataset | `dataset.evals_iterator` + tracing | 3c |

You don’t need to memorise this table. Each row appears again at the moment it’s used.

---

# Set up a Claude judge

DeepEval defaults to an OpenAI judge. Pass a Claude model instead:

```python
from deepeval.models import AnthropicModel

judge = AnthropicModel(model="claude-haiku-5-5", api_key=os.environ["CLAUDE_API_KEY"])
```

Every M10 snippet uses Haiku as the application and the judge, which keeps runs cheap. A small judge is less consistent with vague criteria, so write criteria that say exactly what passes. If scores flip between runs, try a larger judge model. Add `DEEPEVAL_TELEMETRY_OPT_OUT=1` to `.env` if you don't want DeepEval to send usage telemetry. [DeepEval Anthropic models](https://deepeval.com/integrations/models/anthropic)

---

# 3a · Score a plain answer

**Application.** The M2 statement assistant receives the January statement JSON and a question.

**One metric.** `GEval` named Correctness reads the actual and expected output and asks: is the answer correct?

**GEval** turns criteria you write in plain English into a scored check. Use it when no built-in metric matches your rule.

---

# An eval is a pytest test with `assert_test`

```python
def test_correctness():
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=0.5,
    )
    question = "What was my net flow in January 2025?"
    test_case = LLMTestCase(
        input=question,
        actual_output=nano_bank_assistant(question),
        expected_output="Net flow was 4,820 USD: 5,000 USD deposited minus 180 USD withdrawn.",
    )
    assert_test(test_case, [correctness_metric])
```

`evaluation_params` lists the test-case fields the judge may read. `assert_test` fails the test when the score is below the threshold.

---

# Code-along · Run the eval

Set `CLAUDE_API_KEY` in the repository’s `.env`. From the repository root:

```bash
uv run --with deepeval --with anthropic --with python-dotenv \
  deepeval test run snippets/m10_eval_llm_output.py
```

```text
│ Correctness │ 0.9 │ PASSED │
» Pass Rate: 100.0% | Passed: 1 | Failed: 0
```

`deepeval test run` runs pytest, so only functions named `test_…` count as tests. Code outside a test function still runs, but the runner reports **“No test cases found.”**

---

# Make the metric fail on purpose

Replace `actual_output=nano_bank_assistant(question)` with a wrong fixture, and add `AnswerRelevancyMetric(model=judge)` to the metric list:

```python
actual_output="Your January closing balance was 4,820 USD."
assert_test(test_case, [correctness_metric, AnswerRelevancyMetric(model=judge)])
```

**Predict** each score before you run it. Then compare:

| Metric | Observed | Why |
| --- | --- | --- |
| Correctness | **0.30–0.40 · FAIL** | Same number, wrong meaning: 4,820 is net flow, not a balance |
| Answer Relevancy | **1.00 · PASS** | Every sentence is about January money, so it is on topic |

Relevancy checks that the answer is **on topic**, not that it is **true**. Pair it with a correctness check. A metric you have never seen fail hasn't shown it can catch anything.

---

# 3b · A RAG answer can fail in two places

```text
Question → retriever → excerpts → Claude → answer
               ↑                     ↑
     missed the evidence?    misused the evidence?
```

| Where it fails | Example |
| --- | --- |
| **Retrieval** | The cash-reserve rule exists, but the search didn’t return it |
| **Generation** | The rule was in the excerpts, but Claude changed or ignored it |

Reading the final answer alone can’t tell you which one happened, so RAG evaluation checks each half separately.

---

# Look at the excerpts before any score

Print what the retriever returned, then read it.

```text
Q: What is the concentration limit, and how is the cash reserve calculated?
Retrieved: ['portfolio-policy.md']
```

The question needs two policies and the search returned one. You can see a retrieval problem before any metric runs. Metrics turn this check into something you can repeat on every question.

---

# Write the test questions first

Three kinds of question, each with the answer you expect:

| Golden | Kind | Expected output |
| --- | --- | --- |
| “What is the concentration limit?” | One file | No single asset may exceed 35% … |
| “… and how is the cash reserve calculated?” | Two files | 35% limit + cash ÷ portfolio value |
| “What is the daily ATM withdrawal limit?” | Not in the files | *(none: Claude should say it doesn’t know)* |

Write the expected output **before** running the app. The unanswerable question checks that the app doesn’t invent an answer, which matters most in banking.

---

# Three metrics, one question each

| Metric | Checks | Question | Needs expected output? |
| --- | --- | --- | --- |
| **Contextual Recall** | Retrieval | Did the excerpts hold every expected fact? | Yes |
| **Faithfulness** | Answer | Is every claim backed by the excerpts? | No |
| **Answer Relevancy** | Answer | Does the answer address the question? | No |

Recall never reads the answer. Faithfulness never reads the expected output. So a low score points at one half of the pipeline.

---

# A RAG test case also records the excerpts

```python
def make_test_case(golden):
    answer, excerpts = rag_app(golden.input)
    return LLMTestCase(
        input=golden.input,
        actual_output=answer,
        expected_output=golden.expected_output,
        retrieval_context=excerpts,  # what Claude actually saw
    )
```

`rag_app` is the M5 app: it retrieves `TOP_K` excerpts, sends them to Claude, and returns the answer **and** the excerpts. Without `retrieval_context`, recall and faithfulness have nothing to check against.

---

# Unanswerable questions get one metric

```python
evaluate(test_cases=[make_test_case(g) for g in answerable],
         metrics=[recall, faithfulness, relevancy])

evaluate(test_cases=[make_test_case(g) for g in unanswerable],
         metrics=[faithfulness])
```

When the answer isn’t in the files, there is no evidence for recall to find, so it would always score 0. The only useful check is faithfulness: did Claude avoid making something up?

---

# Predict · Run with `TOP_K = 1`

The retriever returns **one** excerpt per question.

**Predict** for the two-file question:

| Metric | High or low? |
| --- | --- |
| Contextual Recall | ? |
| Faithfulness | ? |

---

# Code-along · Run the RAG evaluation

```bash
uv run snippets/m10_eval_rag.py
```

```text
✅ test_case_0  (one file)        Passed 3 metrics
❌ test_case_1  (two files)
     FAIL │ Contextual Recall │ 0.50 │ threshold 0.70
     PASS │ Faithfulness      │ 1.00
     PASS │ Answer Relevancy  │ 1.00
✅ unanswerable                   Passed 1 metric
```

Claude answered the limit and said the cash-reserve rule was missing, which was faithful. Retrieval was the failure: half the expected facts never reached Claude.

At DeepEval’s default pass mark of 0.5, this recall of 0.50 would have **passed**. The snippet sets 0.7.

---

# Read the scores to decide what to fix

| Pattern | Problem is in | Try |
| --- | --- | --- |
| Low recall | Retrieval | Raise `TOP_K`, change chunk size, hybrid search, split the question (M6) |
| High recall, low faithfulness | Generation | Tighter prompt (“answer only from the excerpts”), stronger model |
| High faithfulness, wrong answer | The documents | The evidence itself was wrong or incomplete |
| Unanswerable, confident answer | Generation | Claude filled the gap from memory |

**Faithful is not the same as correct.** An answer can stick perfectly to the wrong excerpt.

---

# Change one thing, run the same questions

Set `TOP_K = 2` and run again.

```text
✅ test_case_0  (one file)        Passed 3 metrics
✅ test_case_1  (two files)       Passed 3 metrics
✅ unanswerable                   Passed 1 metric
```

Same questions, same expectations, one change. Recall went from 0.50 to 1.00 and nothing else got worse. This is the loop from M6: measure, change one thing, measure again.

---

# Make faithfulness catch a made-up answer

In `make_test_case`, force a made-up answer for the ATM question:

```python
answer = "The daily ATM withdrawal limit is 500 USD."
```

| Faithfulness setting | Score | Why |
| --- | --- | --- |
| Default | **Passes** | The excerpts don’t *contradict* 500 USD; they just never mention it |
| `penalize_ambiguous_claims=True` | **0.00 · fails** | Claims the excerpts don’t support also count against the answer |

The snippet uses the strict setting. Check what a metric actually tests before you trust its pass.

---

# 3c · An agent’s answer hides how it got there

The final reply of the M8 agent can look the same whether it used the tool or guessed.

| What you inspect | What it shows |
| --- | --- |
| Final answer only | Whether the reply reads well |
| **Trace** of the run | Every LLM call and tool call, with arguments and results, then the reply |

Agent evaluation reads the trace. The judge can then check that the numbers in the reply came from tool results.

---

# Goldens hold the questions, the agent writes the answers

These goldens have inputs only. The agent writes the answers during the run, and the judge decides whether each task was completed.

```python
dataset = EvaluationDataset(goldens=[
    Golden(input="What was January's net flow?"),
    Golden(input="Compare January and February net flow."),
    Golden(input="What does net flow mean?"),  # No lookup needed.
])
```

The third golden checks the opposite case: a good agent answers without calling the tool. The dataset stays fixed. Each evaluation runs the current agent on every golden, so you can compare versions.

---

# One line turns on tracing

```python
import llama_index.core.instrumentation as instrument
from deepeval.integrations.llama_index import instrument_llama_index

instrument_llama_index(instrument.get_dispatcher())
```

The agent is the M8 LlamaIndex `FunctionAgent` with the same `get_net_flow` tool. Its code doesn’t change. DeepEval listens to LlamaIndex’s events and records each run as a trace. [DeepEval LlamaIndex integration](https://deepeval.com/integrations/frameworks/llamaindex)

---

# Run every golden through the agent

```python
task_completion = TaskCompletionMetric(model=judge, verbose_mode=True)

for golden in dataset.evals_iterator(metrics=[task_completion]):
    task = asyncio.create_task(agent.run(golden.input))
    dataset.evaluate(task)
```

`evals_iterator` hands out one golden at a time. `dataset.evaluate(task)` runs the agent, collects its trace, and scores it when the run ends. `TaskCompletionMetric` works out the task from the input and judges whether the trace completed it.

---

# Code-along · Evaluate the agent on three goldens

```bash
uv run snippets/m10_eval_agent.py
```

```text
Task: Compare January and February net flow.
Score: 0.97
Reason: The agent retrieved the January (4,820 USD) and February (3,200 USD) net flow
figures using the requested tool and produced a correct comparison ...

Task: Explain the meaning of net flow.
Score: 0.95

  Task Completion │ 0.97 │ 100.00% | passed=3 | failed=0
```

`verbose_mode=True` prints what the judge saw for each golden: the **task** it inferred, the **outcome** it read from the trace, and its **reason**.

---

# The judge read the tool calls, not just the reply

```text
Outcome: The agent invoked the get_net_flow tool with month 'January' and received
'4,820 USD'. It invoked the get_net_flow tool with month 'February' and received
'3,200 USD'. An LLM call to 'claude-haiku-5-5' was made ...
```

This is the difference from scoring the answer alone. The judge can see which tool ran, with which month, and what came back.

**Check.** If the reply said “February was 3,500 USD”, which line of the trace would show the error?

---

# Predict · Take the tool away

Change `tools=[get_net_flow]` to `tools=[]` and run the comparison golden again.

**Predict** the score before you look.

```text
Score: 0.05
Reason: The agent did not produce any comparison. It stated it lacked data and
no tools were available ... so it never invoked a data source.
```

Same agent, same question, one change. The trace showed no tool call, so the judge failed the task.

---

# Try · Add a question the data can't answer

Add this golden and run the snippet twice:

```python
Golden(input="Compare January and March net flow."),  # March has no statement.
```

One run scored it below the threshold:

```text
Task: Compare January and March net flow.
Score: 0.4
Reason: The system retrieved January's net flow (4,820 USD) and handled the missing
March data honestly rather than fabricating a figure. However, the requested
comparison was not performed ...
```

The agent did the right thing: it reported the gap. The judge inferred the task as “compare”, so it marked it incomplete. Another run scored the same golden 0.6 and passed. A golden whose result flips between runs isn’t testing anything yet.

**Discuss.** Is the agent wrong, or is the expectation unwritten? Where would you write “report the missing month” so the judge uses it?

<!-- One fix: give that golden an expected_output and score it with a GEval correctness metric, so honest gap reporting is the stated success condition. TaskCompletionMetric(task=...) also fixes the task, but for every golden in the run. -->

---

# Optional · Check the path with exact rules

Task completion is a judgment. When the correct path is known, check it in code too. The [tool-correctness snippet](../snippets/m10_eval_agent_tool_correctness.py) records `tools_called` and compares them with `expected_tools`:

| Run | Tool Correctness | Task Completion |
| --- | --- | --- |
| `MAX_ITERATIONS = 4` | 1.00 · pass | 0.97 · pass |
| `MAX_ITERATIONS = 1` | 1.00 · pass | 0.00 · fail |

With one iteration, Claude requested both lookups and the runner stopped before it answered: right path, no outcome. `ToolCorrectnessMetric` compares tool **names** by default, so a call for the wrong month still passes. Check arguments separately.

---

# Part 4 · Turn evaluations into a test suite

The agent goldens had inputs only. Here each golden also carries an **expected output**: what a correct answer must say. The suite runs after every prompt, model, or retrieval change.

| Golden | Why it is in the suite |
| --- | --- |
| Net flow for January | The everyday question |
| Withdrawals for January | A second field |
| Closing balance on 31 January | A question the data **cannot** answer |

Include cases that should be refused or qualified. Those are the ones a confident model gets wrong.

New to pytest? Start with the [pytest quickstart](../snippets/pytest_101/pytest_quickstart.md): test discovery, `parametrize`, fixtures, and reading a failure.

---

# `assert_test` makes a metric a pytest assertion

```python
GOLDENS = [
    ("What was my net flow in January 2025?", "4,820 USD (5,000 deposited minus 180 withdrawn)."),
    ("How much did I withdraw in January 2025?", "180 USD."),
    ("What was my closing balance on 31 January 2025?",
     "The statement has no closing balance for January. 157,840 USD is the balance today, "
     "not the January closing balance."),
]

@pytest.mark.parametrize("question, expected", GOLDENS)
def test_statement_bot(question, expected):
    test_case = LLMTestCase(input=question, actual_output=statement_bot(question),
                            expected_output=expected)
    assert_test(test_case, [correctness])
```

A failing metric raises `AssertionError` with its score and reason.

---

# Code-along · Run the suite

```bash
uv run --with deepeval --with anthropic --with python-dotenv --with pytest \
  pytest snippets/m10_test_statement_bot.py -v
```

```text
test_statement_bot[What was my net flow ...]          PASSED
test_statement_bot[How much did I withdraw ...]       PASSED
test_statement_bot[What was my closing balance ...]   FAILED
  Correctness [GEval] (score: 0.1 ...) The Actual Output ... calls 157,840
  the closing balance for January. That contradicts the key ground-truth claim ...
```

The bot read `current_balance` as January’s closing balance: the same mistake `rag_guides/statement-fields.md` warns about.

---

# Evaluations also catch plumbing bugs

An earlier version of the bot used `max_tokens=200`. The same golden failed with this reason:

```text
The Actual Output, 'Your clos', is truncated and gives no answer.
```

Haiku spent its token budget before finishing the text. Nothing crashed, and the reply was just cut short. Check `reply.stop_reason`: `max_tokens` means the reply was truncated.

<!-- The snippets now use max_tokens=1024 and read only text blocks, because a reply can start with a thinking block before its text. -->

---

# Lab · Make the suite pass without weakening it

**Goal.** All three goldens pass.

| Rule | Why |
| --- | --- |
| Change the application, not the golden or the threshold | Editing the expectation hides the defect |
| Change one thing per run | So you know which change fixed it |
| Re-run the whole suite | A fix for one case can break another |

**Hint.** What does the model need to know about `current_balance` that the JSON doesn't say?

**Done when** the suite passes twice in a row and you can explain the change.

<!-- One fix that works: add to the system prompt that current_balance is the balance when the request runs, and the statement has no closing balance for the requested month. Retrieving statement-fields.md into the prompt (M5) is another. -->

---

# Lab extension · Add one golden of your own

Pick one and add it to `GOLDENS`:

- A month with no transactions: “What was my net flow in March 2026?”
- A question that needs arithmetic: “What share of January deposits did I withdraw?”
- A question outside the statement: “Should I invest my balance?”

Write the expected output first. Run the suite. If the new golden fails, decide whether the application or the expectation is wrong, and say why.

---

# The improvement loop: same goldens, one change

Every fix in this module followed the same loop. These are the real results:

| Application | Change | Before | After |
| --- | --- | --- | --- |
| RAG (3b) | `TOP_K` 1 → 2 | 1 of 2 answerable goldens pass | 2 of 2 pass |
| Agent (3c) | Tool removed | Task Completion 0.97 on the comparison golden | 0.05: the change made it worse |
| Statement bot (Part 4) | Prompt explains `current_balance` | 2 of 3 goldens pass | 3 of 3 pass |

```text
Run goldens → read failures → change ONE thing → run the SAME goldens → compare
```

| Rule | Why |
| --- | --- |
| Keep the goldens fixed | Otherwise you can’t compare versions |
| Check every golden, not just the one you fixed | A fix for one case can break another |
| Add a golden for every new failure you find | The suite gets stronger over time |

---

# Choose the smallest evaluation that answers your question

| You want to know | Use |
| --- | --- |
| Does the reply contain an exact value or format? | A plain `assert` |
| Is the answer correct in meaning? | `GEval` with written criteria |
| Is retrieval or generation failing? | Contextual Recall vs Faithfulness |
| Did the agent finish the task, using the tools? | Task Completion on traced goldens (+ Tool Correctness for an exact path) |
| Did my change break anything? | Goldens in pytest with `assert_test` |

Judge metrics cost tokens on every run, and each metric makes one or more judge calls per case. Use a small judge such as Haiku while you iterate, and keep exact rules in code.

---

# Debrief · Read a score like an engineer

1. A metric passed. What did it actually check, and which fields did it read?
2. Recall was 0.50 and faithfulness was 1.00. Which half of the RAG pipeline do you change?
3. Task completion failed for an agent that reported a missing record honestly. What do you change: the agent, the golden, or the metric?
4. Your golden failed. When is the right fix to change the expected output?

**Quick quiz.**

- Which test-case field do recall and faithfulness need that a plain LLM test case doesn’t have? *(`retrieval_context`)*
- A correct answer failed one run and passed the next. What do you change first? *(Make the criteria explicit about what passes, then consider a larger judge)*
- What does a golden contain that a test case doesn’t, and the other way round? *(A golden has the input and optional expectations; a test case adds the actual output of one run)*
