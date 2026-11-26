# M8 · Build Your First Agent with Claude

Build an application that uses a model to choose its next step, then checks what that step accomplished.

- Explain what the LLM, the tools, and the application each do.
- Trace how the model chooses a tool and uses its result.
- Decide when the agent has enough evidence to finish.

<!-- Teach through the pipeline example first. Use Nano Bank later to run the same decision loop and inspect the evidence. -->

---

# The LLM and the agent application

| Part | Job |
| --- | --- |
| **LLM** | Reads the context and produces a reply or a tool request. Claude is the model in this lesson. |
| **Agent application** | Gives the model a goal and tools, executes its requests, and returns results for the next decision. |

One agent run can contain several calls to the same model. [Anthropic’s guide to agent building blocks](https://www.anthropic.com/research/building-effective-agents)

---

# Who decides the next step?

| Application pattern | Who chooses what happens next? |
| --- | --- |
| Single model call | The application sends the prompt and displays the reply. |
| Fixed workflow | The developer specifies the steps, such as retrieve a document and then summarize it. |
| Agent loop | The model chooses a next action based on the goal and the results so far. |

**Ask the room.** When would you want the same steps every time? When might the next step depend on what you find? [Anthropic’s guide to workflows and agents](https://www.anthropic.com/research/building-effective-agents)

---

# Start with the goal and what counts as done

**Goal.** “Tell me whether today’s Orders pipeline ran successfully. If it failed, tell me the logged reason.”

| What the lookup finds | What the answer needs |
| --- | --- |
| The run succeeded | Confirm today’s status. |
| The run failed | Report the failed status and the logged reason for that run. |

**Instruction.** Use the recorded status and logs. Say which fact is missing if you cannot find it.

---

# A tool is a function the model can request

Tools let the application read data, run a calculation, or apply a business rule.

| Tool | What the function does | What it returns |
| --- | --- | --- |
| `get_run_status` | Reads job history | Status and run ID |
| `search_policy` | Searches documents | Matching passages |
| `check_invoice_match` | Applies an invoice matching rule | Match status and discrepancies |

A tool can make a specific decision, such as whether an invoice matches a purchase order. The LLM decides when to request that tool and how to use its result. [Claude’s tool-use guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)

---

# Describe the tool so the LLM can choose it

| Part of the contract | Example |
| --- | --- |
| Name | `get_run_status` |
| Description | Read the recorded status and run ID for a job on a given date. |
| Input schema | Requires `job` and `date` strings. |

The application sends these descriptions with the question. The LLM uses them to choose a tool and supply arguments. [Claude’s tool-use guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works)

---

# Which tool should the LLM request first?

| Available tool | Needs | Returns |
| --- | --- | --- |
| `get_run_status` | Job and date | Status and run ID |
| `get_run_error` | Run ID | Logged error |
| `get_table_schema` | Table name | Column names and types |

**Predict.** For “Did today’s Orders pipeline fail?”, which tool has the right inputs and returns the fact we need?

<!-- A status lookup can start with the job and date. If it reports failure, its run ID makes the log lookup possible. The schema tool could be useful for a later investigation into a specific column, depending on the logged error and the user's goal. -->

---

# Follow one tool request

```text
Claude requests get_run_status(job="orders", date="today")
                         ↓
Application runs the function and receives failed, run-42
                         ↓
Application gives Claude that result for its next decision
```

`tool_use` carries the request. `tool_result` carries the observation. A call ID pairs them. [Claude tool-call guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)

---

# Use the result to decide what is still missing

Ask whether the observation is for the right job and date, and whether it supplies the evidence the goal requires.

| Observation | What Claude can do next |
| --- | --- |
| Today’s Orders run succeeded | Answer with the recorded status. |
| Today’s Orders run failed, `run-42` | Request `get_run_error` for `run-42`. |
| The result is for yesterday’s run | Request the status for today’s run. |
| No run or log can be found | Explain what is missing or ask for details that could resolve it. |

**Check.** If the status is `failed` and Claude stops with just that fact, which part of the goal is still open?

---

# The agent loop repeats that decision

```text
Goal + instructions + tools + results so far
                         ↓
                   LLM chooses
          ┌──────────────┴──────────────┐
     Reply to the user             Request a tool
                                         ↓
                               Run it and return the result
                                         ↓
                                  LLM chooses again
```

The **runtime** manages these turns and keeps earlier results available. Each new observation can change the next decision. [Anthropic’s explanation of the agent loop](https://www.anthropic.com/research/building-effective-agents)

---

# The application owns the boundaries

| The builder controls | Example |
| --- | --- |
| Which tools are allowed | Give the agent read access to status and logs. |
| What makes inputs valid | Check that the run ID exists and can be read. |
| How long the run can continue | Set a turn limit and surface an incomplete result when it runs out. |
| How to verify task completion | Check that the reply covers today’s status and the logged reason if it failed. |

Claude can finish a reply with an answer or a request for clarification. Use the goal and the evidence to tell whether the work is complete.

---

# Worked example · Apply the loop to Nano Bank

**Goal.** Compare January and February’s net flow.

| Design choice | In the demo |
| --- | --- |
| Tool | `get_net_flow(month)` reads one month. |
| Result | The amount in USD, or a message that the record is missing. |
| Done when | The answer uses both amounts and explains the difference. |

**Predict.** After seeing January alone, should Claude answer, use the tool again, or ask the user for something?

---

# Nano Bank · Predict when Claude needs the tool

A classroom dictionary stands in for the statement records.

| Month | Net flow |
| --- | --- |
| January | 4,820 USD |
| February | 3,200 USD |

**Predict.** Which question calls the tool? “What does net flow mean?” or “What was January’s net flow?”

---

# Code-along · Run your first tool-using agent

Set `CLAUDE_API_KEY` in the repository’s `.env`. From the repository root, run the [single-tool snippet](../snippets/m8_bank_tool.py).

```bash
uv add anthropic python-dotenv
uv run snippets/m8_bank_tool.py
```

Look for `Tool result: January 4,820 USD` and then Claude’s answer. The first line comes from the Python function.

---

# The tool is a Python function

```python
@beta_tool
def get_net_flow(month: str) -> str:
    """Look up the net flow in USD for one month."""
    statements = {"january": "4,820 USD", "february": "3,200 USD"}
    amount = statements.get(month.lower(), "No statement for that month.")
    print("Tool result:", month, amount)
    return amount
```

`@beta_tool` derives the contract from the function’s name, docstring, and type hints. Claude gets the contract and can request a month. The Python function reads the record when it runs. [Claude SDK tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)

---

# The runner manages the conversation

```python
question = "What was January's net flow?"
runner = client.beta.messages.tool_runner(
    model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"),
    max_tokens=128,
    max_iterations=4,
    system="Use the tool for recorded amounts.",
    tools=[get_net_flow],
    messages=[{"role": "user", "content": question}],
)

answer = runner.until_done()
```

The runner sends the request, executes the requested function, and gives Claude the result. `max_iterations` bounds the run. [Claude SDK tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)

**Try.** Ask what net flow means. Then ask for March. Watch when the tool runs and what it returns.

---

# One question can use the tool twice

**Ask.** “Compare January and February’s net flow.” Each lookup gives Claude one of the two amounts.

```text
Request one month → read the result → request the other month → compare
```

Run the [agent loop snippet](../snippets/m8_bank_agent.py) with `uv run snippets/m8_bank_agent.py`. It uses the same Python function and prints each Claude turn so you can follow the lookups.

---

# Read the trace · Watch Claude decide again

```python
for reply in runner:
    print("Claude turn:", reply.stop_reason)
    if reply.stop_reason == "end_turn":
        print("Claude:", reply.content[0].text)
```

`tool_use` means Claude asked for a lookup. The runner calls the function and returns its result. `end_turn` means Claude finished its reply. [Claude SDK tool runner](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner)

---

# Follow the results across turns

```text
Claude turn: tool_use
Tool result: January 4,820 USD
Claude turn: tool_use
Tool result: February 3,200 USD
Claude turn: end_turn
```

The runner keeps the question, tool requests, and results available to Claude as the conversation continues. The API uses `tool_use_id` to pair each result with its request. [Claude tool-call guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)

**Check.** Which number has Claude received after the first lookup? What does it still need before it can compare?

---

# Did the Nano Bank agent achieve its goal?

| Evidence available | What it supports |
| --- | --- |
| January only | January’s amount. February still needs a lookup. |
| January and February | A comparison. January was **1,620 USD higher**. |
| One month’s record is missing | The known amount and an explanation of the gap. |

**Inspect the reply.** Does it use the amounts for the months asked about? Does the comparison follow from the results?

---

# Mini lab · Change the question or the limit

| Try | Inspect |
| --- | --- |
| Ask for January and February | Two tool requests, then the comparison |
| Compare January and March | The tool reports a missing record for March. Check what Claude can conclude. |
| Set `max_iterations=1` and compare again | The runner stops before Claude can finish the comparison |

**Done when** you can explain why Claude chose each action and whether the results supported its reply.

**Try it in LlamaIndex.** The [LlamaIndex snippet](../snippets/m8_bank_llamaindex_agent.py) uses the same lookup and comparison question. Follow its `uv add` comment, then run `uv run snippets/m8_bank_llamaindex_agent.py`.

---

# Debrief · Trace the complete round trip

```text
Question → Claude → tool request → Python lookup
              ↑                         ↓
              └──── result in messages ─┘
```

1. Who chose the tool and its arguments?
2. Who ran the tool and returned the data?
3. What would show that the goal was achieved? What would make the agent continue or report a gap?

<!-- Teaching source: the tool-call and agent-loop sections of the Envestnet B2 reference. -->
