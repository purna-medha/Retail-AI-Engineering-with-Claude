# M4 · Prompt Engineering, Context Engineering, and Skill Building

**AI Engineering with Claude · Tredence**

Describe a task so a model can carry it out. Then make the request easier to test, supply better evidence, and save the procedure for future use.

<!--
Start with the range of tasks models can do. Teach the vocabulary before the three engineering practices. Use each worked example to explain the concept on that slide. The demos use synthetic data and can run as discussions if model access is unavailable.
-->

---

# M4.1 · Five tasks a general-purpose model can help with

A general-purpose model can work across domains. You can call a hosted model or run one with open weights.

| Task | What the model produces |
| --- | --- |
| Classify a support ticket | A queue label such as billing or account access |
| Answer a simple support ticket | Invoice-download instructions based on a help article |
| Extract data from a vendor invoice | Structured fields for the invoice number, date, and amount |
| Write data-quality checks | Python tests for missing and duplicate order IDs |
| Generate a dashboard | A layout and chart code for weekly revenue by region |

**Ask the room.** Which of these tasks already occurs in your work?

<!--
Ask what the input and result would be for one task from the room. A more complicated ticket, such as a disputed charge, can also be supported when the app supplies the applicable policy and verified payment status.
-->

---

# M4.1 · A model can follow a procedure you describe

Explain the **inputs**, the **steps and decision rules**, and the **result**. A colleague should be able to follow the same procedure and check the result.

| Task | How to do it |
| --- | --- |
| Clean a 10,000-row Orders CSV | Read the schema. Keep the first occurrence of each order ID. Flag blanks and later duplicates. Write accepted rows and rejects separately. |
| Generate a weekly dashboard | Read the approved regional totals. Plot one bar per region, sort by revenue, and label the week and currency. |

For the CSV, ask the model to draft a script and test it on a small sample. Run the checked script on the full file.

<!--
Ask how the dashboard should handle a region with missing revenue. A specific instruction gives both the model and the tester a rule to follow. For an accounting analogy, describe matching two lists by transaction ID and amount, then reporting unmatched entries for review.
-->

---

# M4.2 · Prompt and context

| Term | Meaning | Example |
| --- | --- | --- |
| **Prompt** | What you ask the model to do | “Summarize the decisions and next steps in three bullets.” |
| **Context** | Information the model needs for the task | The email thread containing those decisions and next steps |

The complete request can include the ask, instructions, and context. In M2, the application assembled those parts before calling Claude.

**Check.** If you need the decisions from one meeting, what would you put in the prompt? Which emails would you include?

---

# M4.2 · What did the model have to assume?

```text
Prompt: Summarize this thread.
Context: “We agreed to use Supplier B. Priya will confirm the quote.”
```

The model has to choose what the summary should contain. Revise the ask to “List each decision, owner, and deadline. Mark any missing field as unknown.”

The context supports **Supplier B** and **Priya confirming the quote**. The deadline is unknown until you supply an email that states it.

<!--
Try both requests. Ask the room which change would help if the deadline is required. The prompt can specify how to report missing information. The evidence has to supply the date. In practice, refine and retest over a few turns as you find assumptions that matter.
-->

---

# M4.2 · The context window

The **context window** is the amount of information a model can work with at once, measured in tokens. Instructions, selected messages, and supplied documents take up space in the request.

For a long email thread, include the messages that establish the decision, the owner, and the date. Remove repeated quoted copies when they add no new evidence.

**Check.** The last email names the owner. An earlier reply sets the due date. Which messages does the model need for the action list?

<!--
Use this example to separate context size from context quality. The app needs both relevant messages even if the latest message is shorter. Exact limits vary by model and are unnecessary for the exercise.
-->

---

# M4.3 · Prompt engineering

**Prompt engineering** is designing and testing the instructions for a task. Start with a clear action and a result you can recognize as correct.

| Part | What it specifies |
| --- | --- |
| Task | What the model should do |
| Rules | How to make a decision or handle an unclear case |
| Output | What to return and in what form |

Write a passing result before running the prompt. Then use examples or more explicit steps where they address a real ambiguity.

---

# M4.3 · A vague task becomes a testable prompt

“Handle this ticket” could ask for routing, a reply, or an action. This prompt defines routing as the task.

```text
Classify one support ticket.
Use billing for charges, invoices, and refunds.
Use account_access for sign-in and password problems.
Use other for clear requests outside those categories.

Return JSON with category, evidence, and needs_review.
Quote a short excerpt from the ticket. For an unclear or mixed
issue, return other with null evidence and needs_review true.
Otherwise, set needs_review to false.
```

**Ticket** “My card was charged twice.”

**Expected result** `{"category":"billing","evidence":"charged twice","needs_review":false}`

<!--
Run the vague and precise versions on the same ticket. Ask learners to point to the instruction responsible for the useful difference. In a Claude API demo, put the routing rules in the system instruction and the ticket in the user message.
-->

---

# M4.3 · Few-shot examples show where a rule applies

Give the model a few inputs with the answers you expect. Include a case that checks a boundary.

| Example ticket | Category | Evidence | Review |
| --- | --- | --- | --- |
| “My password reset link expired.” | `account_access` | “reset link expired” | No |
| “When does the shop open?” | `other` | “When does the shop open?” | No |
| “Please help.” | `other` | `null` | Yes |

**Try a new case.** “I changed my password yesterday. My invoice shows two charges.” Which issue should determine the category?

<!--
Expect billing. The password change provides background. It is a sign-in problem only when the customer actually reports a sign-in issue. Compare results with and without the examples on the same unseen cases.
-->

---

# M4.3 · Decision steps make a procedure explicit

Write steps when the task has an order or a rule that matters. For example, an invoice extraction prompt can specify how to distinguish two similar identifiers.

```text
1. Find the invoice header.
2. Take invoice_number from the field labelled Invoice No.
3. Record a missing Invoice No. as null.
4. Return the value and quote the line it came from when available.
```

**Check.** The document shows `Invoice No. INV-42` and `PO No. PO-18`. What value should come back? What changes if the invoice number is absent?

<!--
Expect INV-42 and the invoice number line. If it is absent, expect null. Ask for the final value and source so learners can verify the result. The ordered procedure is visible in the prompt.
-->

---

# M4.3 · Prompt review and one-change tests

Ask the model to critique the instructions. Try “Give me two inputs where these rules leave the result unclear. Point to the rule that needs clarification.”

Use the suggestions to improve the prompt and build a test set.

1. Record the expected results on a few unseen inputs.
2. Change one rule or remove one example. Keep the input and model fixed.
3. Compare what changed in the output shape, decision, or evidence.

Removing one part for comparison is an **ablation**. Rerun the original tests after the change.

---

# M4.4 · Context engineering

**Context engineering** is choosing and organizing the information available to the model for a task.

- **Select** the facts and rules needed to answer the question.
- **Organize** them so a person or application can find the right source.
- **Resolve** duplicate or conflicting material and mark information that is missing.

A clear prompt still depends on good evidence. To draft a dashboard brief, the model needs the numbers and the definition of the metric it is describing.

---

# M4.4 · The question determines the evidence

A manager asks “Which region had the highest net revenue last week?”

| Include in the request | Why it matters |
| --- | --- |
| Regional totals for the reporting week | Shows the values to compare |
| Reporting dates and currency | Identifies what the reported numbers cover |
| The net revenue definition | Establishes which deductions the totals include |

**Check.** Would a product catalogue help answer this question? What would you need if the manager asked which product drove the result?

<!--
For the first question, use the weekly totals. For the product question, ask for revenue by product and region for the same period. This keeps the lesson on what evidence changes when the task changes.
-->

---

# M4.4 · A context pack people can navigate

```text
dashboard/
  index.md
  revenue-metrics-v3.md
  weekly-net-revenue-by-region.csv
```

- **Descriptive file names** show what each source contains.
- **Headings and a contents list** help people find sections such as “Net revenue” and “Reporting period.”
- **An index** identifies the approved metric definitions and where to get the weekly extract.

**Check.** Which file should define how refunds affect the metric? Which file should carry the totals?

---

# M4.4 · Duplicates, conflicts, and missing information

Suppose two definitions for “revenue” appear in the dashboard folder.

| Source | Definition |
| --- | --- |
| Archived guide | Sales before refunds |
| Approved guide for this report | Net revenue is sales less refunds |

Select the definition that applies to the report. Confirm the data uses that definition. Keep one approved copy active and label older versions.

If the export says only `revenue` and its basis is unclear, flag that gap before describing it as net revenue.

---

# M4.4 · Assemble and inspect the request

```text
TASK
Name the region with the highest net revenue. Write one sentence.
If a region's total is missing, say the comparison is unavailable.

CONTEXT
Week ending May 17. Currency USD.
Coverage: North and South.
Metric: Net revenue is sales less refunds.
Regional net revenue: North 42,000. South 38,000.
```

**Expected answer** “North had the highest net revenue at USD 42,000 for the week ending May 17.”

**Try it.** Remove South’s total. What can the model still say? What would it need to name a winner across both regions?

<!--
It can report North's value. The comparison needs South's value as well. Explain that headings make the request easier to inspect. The numbers come from the supplied extract.
-->

---

# M4.5 · Skill building

A **skill** packages a tested procedure for a recurring task. Give it a name, a description of when it applies, and instructions for doing the work.

| Save in the skill | Supply on each run |
| --- | --- |
| Decision rules, procedure, output format, and useful examples | The current request and the data it needs |

Start with a prompt that works on representative inputs. Package the repeatable part and test it on new inputs before sharing it.

---

# M4.5 · A skill has a clear trigger and result

**Example** Review order IDs before a CSV enters a pipeline.

| Design question | Answer |
| --- | --- |
| When should it apply? | When the user asks to check an Orders CSV for blank or duplicate IDs |
| What does it need? | A CSV with an `order_id` column and one row per order |
| What should it return? | Source row numbers and reasons for issues |
| Where does the task stop? | Report findings. Changes to the file belong to a separate step. |

**Check.** Would a request to forecast next week’s sales activate this skill?

---

# M4.5 · Write a `SKILL.md`

Save the file as `orders-id-review/SKILL.md`. The header describes the skill. The body supplies the procedure.

```markdown
---
name: orders-id-review
description: Review an Orders CSV when asked to check for blank or duplicate order IDs.
---

1. Number data rows from 1 after the header.
2. Trim surrounding spaces in order_id. Flag empty IDs as missing_id.
3. For each nonempty ID, accept the first occurrence. Flag later rows as duplicate_id.
4. Return a JSON object with an issues list. Each issue has source_row and reason.
   Use an empty list when all rows pass. Report findings only.
```

Use the description to identify the task. Keep examples or longer reference files alongside the skill when they help.

<!--
Point out the matching folder and skill names. Ask where an example of a duplicate would fit. The Agent Skills specification describes this format. https://agentskills.io/specification
-->

---

# M4.5 · Load a skill and give it fresh input

A skills-aware client can use the name and description to discover a skill. In an ordinary API application, the code can select and load the procedure explicitly.

```python
from pathlib import Path

skill = Path("orders-id-review/SKILL.md").read_text(encoding="utf-8")
csv_sample = "order_id,amount\nA101,20\nA102,35\nA102,40\n,10\n"
request = {
    "system": skill,
    "messages": [
        {"role": "user", "content": f"Check the order IDs.\n{csv_sample}"}
    ],
    "max_tokens": 256,
}
print(request)
```

Read the preview. Where are the procedure and the current file contents?

<!--
Run the preview from the folder containing orders-id-review. It needs no API credentials. To run the model, reuse the M1 Claude client and pass the request with your configured model ID. A larger pipeline can enforce the same acceptance rules in code.
-->

---

# M4.L1 · Mini lab: test the procedure on three cases

In pairs, write the expected result before running each case. Then compare the output with your expectation.

| Case | What to check |
| --- | --- |
| Sample CSV from the previous slide | Row 3 has `duplicate_id`. Row 4 has `missing_id`. |
| A new CSV with unique, nonempty IDs | The `issues` list is empty |
| “Forecast orders for next week” | The app or client should choose a different workflow |

Change one instruction if a case fails and test all three again.

**Done when** a partner can explain what belongs in the prompt, what comes from context, and what will be reused as a skill.

<!--
For transfer, have each pair name one job from their own work and give a concrete ask, a source of evidence, and one repeatable rule. With no model access, inspect the assembled request and use the expected results for the discussion.
-->
