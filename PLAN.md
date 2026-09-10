# Hiver SDE Intern — 5-Day Solo Implementation Plan

## Project Goal

Build a brand-specific AI customer-support agent from the Customer Support on Twitter dataset.

The system must:

1. Classify incoming customer messages into a small intent taxonomy discovered from the selected brand's data.
2. Draft a response grounded in how that brand historically resolved similar issues.
3. Decide whether the message should be auto-handled or escalated to a human, with a stated reason.
4. Prove the system works using a hand-labelled golden evaluation set, baselines, automated metrics, and an LLM-as-judge whose agreement with human ratings is measured.

The priority is **evaluation credibility over feature count**.

---

# 1. Final System

The final pipeline should look like:

```text
Customer message
       |
       v
+--------------------+
| Intent classifier   |
+---------+----------+
          |
          v
+--------------------+
| Historical case     |
| retrieval           |
+---------+----------+
          |
          v
+--------------------+
| Grounded response   |
| generation          |
+---------+----------+
          |
          v
+--------------------+
| Escalation / risk   |
| decision             |
+---------+----------+
          |
       +--+--+
       |     |
       v     v
     AUTO  HUMAN
     REPLY ESCALATE
```

A single prediction should expose structured output such as:

```json
{
  "intent": "refund_request",
  "intent_confidence": 0.91,
  "reply": "Draft response...",
  "decision": "escalate",
  "reason": "Refund eligibility cannot be established from the available evidence.",
  "evidence": [
    {
      "conversation_id": "123",
      "similarity": 0.87
    }
  ]
}
```

The system should be allowed to say **"I don't know"** or escalate when evidence is insufficient.

---

# 2. Scope

## In Scope

- One brand from the Twitter support dataset
- Conversation reconstruction
- Data cleaning and sampling
- Brand-specific intent taxonomy
- 150–250 example golden evaluation set
- Intent classification
- Historical-case retrieval
- Grounded reply generation
- Auto-handle vs escalation decision
- Two baselines
- Automated evaluation
- LLM-as-judge
- Human validation of the LLM judge
- Failure analysis
- Reproducible CLI pipeline
- Concise demo interface if time allows
- README/report and decision log

## Explicitly Out of Scope

Unless required to answer an evaluation question, do not build:

- A full customer-support platform
- Real CRM integration
- Real account access
- Real refunds, cancellations, or transactions
- Autonomous tool execution
- Multi-agent orchestration
- A large production frontend
- Fine-tuning before a strong baseline exists
- Support for every brand in the dataset
- Features that cannot be evaluated credibly within five days

---

# 3. Working Principles

### 3.1 Evaluation before optimization

Do not tune the system against the golden test set.

The golden set must be frozen before final model tuning.

### 3.2 Conversation-level separation

Train/knowledge data and evaluation data must be separated by conversation, not individual tweets.

This prevents a test message from retrieving another message from the same conversation.

### 3.3 Historical evidence over invented policy

The response generator should prefer evidence from historically resolved conversations.

It must not invent:

- Refund policies
- Compensation
- Timelines
- Actions already taken
- Account-specific facts

### 3.4 Escalation is a feature, not a failure

A support agent that escalates uncertain or high-risk cases can be better than one that replies to everything.

### 3.5 Every major decision gets recorded

Maintain `DECISIONS.md` throughout the project instead of reconstructing decisions on Day 5.

---

# 4. Repository Structure

```text
hiver-support-agent/
|
├── data/
│   ├── raw/                  # not committed
│   ├── processed/
│   ├── samples/
│   └── golden/
|
├── src/
│   ├── data/
│   │   ├── ingest.py
│   │   ├── clean.py
│   │   ├── threads.py
│   │   └── sample.py
│   |
│   ├── taxonomy/
│   │   └── discover.py
│   |
│   ├── retrieval/
│   │   ├── index.py
│   │   └── retrieve.py
│   |
│   ├── classification/
│   │   ├── baseline.py
│   │   └── classifier.py
│   |
│   ├── generation/
│   │   └── responder.py
│   |
│   ├── escalation/
│   │   └── policy.py
│   |
│   ├── agent.py
│   └── schemas.py
|
├── evaluation/
│   ├── golden_set.jsonl
│   ├── run_eval.py
│   ├── metrics.py
│   ├── judge.py
│   ├── judge_validation.py
│   └── failure_analysis.md
|
├── experiments/
│   ├── baseline_majority/
│   ├── baseline_simple/
│   └── agent/
|
├── app/                      # optional demo UI
|
├── tests/
├── notebooks/
├── experiments/
|
├── README.md
├── REPORT.md
├── DECISIONS.md
├── requirements.txt
└── .env.example
```

Keep the architecture modular enough to compare systems without turning the take-home into an enterprise codebase.

---

# 5. Day 1 — Dataset Reconnaissance and Brand Selection

## Objective

Understand the actual Twitter dataset and select a brand based on **evaluation suitability**, not popularity.

## Morning — Inspect the Dataset

Determine:

- Dataset schema
- Brand identifiers
- Tweet identifiers
- Conversation/thread relationships
- Customer vs brand messages
- Reply relationships
- Timestamps
- Missing values
- Duplicate records
- Message lengths
- Number of turns
- Conversation completeness

Create a basic profiling notebook:

```text
notebooks/01_dataset_recon.ipynb
```

## Brand-Level Analysis

For every plausible brand, calculate:

- Number of conversations
- Number of customer messages
- Number of brand responses
- Average turns per conversation
- Median conversation length
- Number of apparently resolved conversations
- Number of recurring support topics
- Number of usable historical cases

Create:

```text
data/samples/brand_statistics.csv
```

## Brand Selection Criteria

Choose a brand with:

- Enough conversations
- Enough repeated customer problems
- Clear brand responses
- Sufficient resolved cases
- Enough examples for a 150–250 case golden set
- Reasonable conversation structure
- A support distribution that is neither completely trivial nor impossibly fragmented

Do not choose a brand simply because it has the largest number of tweets.

## Afternoon — Conversation Reconstruction

Build the first usable representation:

```json
{
  "conversation_id": "...",
  "turns": [
    {
      "speaker": "customer",
      "text": "..."
    },
    {
      "speaker": "brand",
      "text": "..."
    }
  ]
}
```

Also preserve:

- Original tweet IDs
- Timestamps
- Raw text
- Conversation metadata

## Create Initial Experimental Split

At minimum:

```text
Historical / Knowledge Data
        |
        +---- retrieval corpus
        |
        +---- taxonomy discovery
        |
        +---- development experiments

Frozen Golden Set
        |
        +---- final evaluation only
```

Split at the conversation level.

## Day 1 Deliverables

- `notebooks/01_dataset_recon.ipynb`
- `data/samples/brand_statistics.csv`
- `data/processed/conversations.jsonl`
- `docs/dataset_notes.md`
- Initial `DECISIONS.md`
- Selected brand

## Day 1 Gate

You must be able to explain:

> Why this brand gives us enough repeated and resolvable support cases to evaluate an AI support agent meaningfully.

If the answer is weak, change brands now.

---

# 6. Day 2 — Intent Taxonomy and Golden Evaluation Set

## Objective

Define what customers are asking and create the evaluation set before building the final agent.

This is the most important anti-bias step in the project.

---

## Morning — Discover Intents

Explore customer messages from the selected brand.

Use clustering/embeddings or other exploratory techniques to identify recurring themes, then manually inspect them.

Do not blindly inherit a taxonomy from another dataset.

Create approximately:

```text
8–15 intents
```

depending on the actual data.

Possible categories might include:

```text
billing_problem
refund_request
account_access
subscription_problem
technical_issue
delivery_problem
cancellation
feature_question
complaint
other
```

These are examples only. The actual taxonomy must come from the selected brand.

---

## Intent Definition Format

Every intent should have:

```yaml
name:
description:
inclusion_criteria:
exclusion_criteria:
examples:
approximate_frequency:
```

Include:

```text
other / unclear
```

for cases that genuinely do not fit.

Create:

```text
src/taxonomy/intents.yaml
docs/intent_guidelines.md
```

---

## Afternoon — Golden Set Construction

Target:

```text
200 examples
```

within the required 150–250 range.

The set should contain a useful mixture of:

- Common intents
- Rare intents
- Short/noisy tweets
- Ambiguous cases
- Context-dependent cases
- Difficult cases
- Cases that should clearly escalate

Each example should contain:

```json
{
  "conversation_id": "...",
  "customer_message": "...",
  "intent": "...",
  "should_escalate": true,
  "expected_resolution": "...",
  "difficulty": "hard",
  "human_notes": "..."
}
```

Not every field needs to be exposed to the model.

---

## Sampling Documentation

Write a short note explaining:

- How examples were sampled
- Why the set is representative
- How rare intents were handled
- How difficult examples were included
- How leakage was prevented
- How labels were assigned

---

## Label Validation

If possible, independently re-label approximately 50 examples.

Compare the two label passes.

Record disagreements.

Use disagreements to improve the annotation guidelines **before freezing the set**.

---

## Freeze the Golden Set

Once labels and guidelines are finalized:

```text
evaluation/golden_set.jsonl
```

becomes immutable.

Do not change labels because the agent performs badly.

## Day 2 Deliverables

- `src/taxonomy/intents.yaml`
- `docs/intent_guidelines.md`
- `evaluation/golden_set.jsonl`
- `docs/golden_set_methodology.md`
- Updated `DECISIONS.md`

## Day 2 Gate

You should now have:

```text
Chosen brand
+
Clean conversations
+
Intent taxonomy
+
Frozen evaluation set
```

Do not proceed without this.

---

# 7. Day 3 — Baselines, Retrieval and Agent

## Objective

Build the smallest complete system and establish meaningful baselines.

---

# Morning — Baseline 1: Majority Classifier

The trivial baseline predicts:

```text
most frequent intent
```

for every example.

This establishes the minimum performance bar.

Record:

- Accuracy
- Macro F1
- Per-intent F1

---

# Baseline 2: Simple Similarity System

Use a transparent non-LLM method such as:

```text
TF-IDF + cosine similarity
```

or:

```text
BM25
```

Pipeline:

```text
Customer message
       |
       v
Text representation
       |
       v
Nearest historical cases
       |
       v
Infer intent / resolution
```

This gives us a meaningful comparison against the AI system.

Store:

```text
experiments/baseline_majority/
experiments/baseline_simple/
```

---

# Afternoon — Historical Retrieval

Create an index of historical support cases.

Each indexed case should contain:

```text
case_id
conversation_id
customer_problem
brand_resolution
intent
metadata
embedding
```

Only use cases available in the knowledge/training split.

Start with:

```text
Top-k = 3 or 5
```

and test whether increasing k actually helps.

Retrieval pipeline:

```text
New customer message
        |
        v
Embedding
        |
        v
Vector search
        |
        v
Top-k historical resolved cases
```

---

# Intent Classifier

Use an LLM with structured output.

Provide:

- Intent definitions
- Customer message
- Relevant historical evidence where useful

Return:

```json
{
  "intent": "...",
  "confidence": 0.0
}
```

Do not allow arbitrary intent names.

---

# Response Generator

The response model should receive:

```text
Brand
Customer message
Predicted intent
Retrieved historical cases
Response rules
```

Core instructions:

```text
Draft a response consistent with how this brand historically handled
similar customer problems.

Do not invent policies.

Do not claim an action was taken unless supported by the evidence.

Do not invent refunds, credits, timelines, or account-specific facts.

If the available evidence is insufficient, recommend escalation.
```

---

# Day 3 Deliverables

- Working majority baseline
- Working simple baseline
- Retrieval index
- Retrieval function
- LLM classifier
- Response generator
- End-to-end `agent.py`
- Structured prediction schema

Example:

```bash
python -m src.agent --message "My subscription was charged twice"
```

should produce structured output.

## Day 3 Gate

A single customer message can now go through:

```text
classification
→ retrieval
→ response generation
→ preliminary decision
```

from one command.

---

# 8. Day 4 — Escalation, Evaluation and Judge

## Objective

Turn the prototype into a measurable system.

---

# Morning — Escalation Policy

Create explicit escalation signals.

Potential signals:

### Escalate

- Low intent confidence
- Insufficient retrieval evidence
- Conflicting historical resolutions
- Sensitive account/security issue
- High-impact financial issue
- Customer explicitly asks for a human
- Case requires account-specific action
- Model cannot support its response with historical evidence

### Auto-handle

- High confidence
- Strong historical precedent
- Low-risk issue
- Consistent evidence
- Response can be grounded directly in retrieved cases

Represent the result as:

```json
{
  "decision": "auto_handle",
  "reason": "High-confidence intent with strong historical precedent."
}
```

or:

```json
{
  "decision": "escalate",
  "reason": "Historical evidence is insufficient to determine the correct resolution."
}
```

---

# Threshold Experiment

Do not arbitrarily choose the confidence threshold.

Evaluate multiple thresholds.

For example:

| Threshold | Auto-handle % | Escalation Recall | Unsafe Auto-handle % |
|---:|---:|---:|---:|
| 0.60 | | | |
| 0.70 | | | |
| 0.80 | | | |
| 0.90 | | | |

Choose a threshold based on the observed safety/coverage tradeoff.

---

# Full Evaluation Harness

Run all systems against the frozen golden set:

```text
Majority baseline
Simple baseline
AI agent
```

For every example, save:

```json
{
  "id": "...",
  "predicted_intent": "...",
  "intent_confidence": 0.91,
  "retrieved_cases": [...],
  "reply": "...",
  "decision": "auto_handle",
  "reason": "..."
}
```

---

# Automated Metrics

## Intent

Calculate:

- Accuracy
- Macro F1
- Per-intent F1
- Confusion matrix

Macro F1 should be a major metric because raw accuracy can hide poor performance on less frequent intents.

## Retrieval

Where labels permit:

- Recall@k
- Evidence relevance

## Escalation

Calculate:

- Escalation precision
- Escalation recall
- False auto-handle rate

Treat false auto-handling as an especially important failure because the system is acting without human review.

---

# LLM-as-Judge

Evaluate generated replies using a fixed rubric.

Recommended dimensions:

```text
1. Correctness
2. Groundedness
3. Resolution usefulness
4. Brand appropriateness
5. Hallucination / unsupported claims
6. Overall quality
```

Use a 1–5 scale.

The judge should receive:

```text
Customer message
Historical evidence
Agent reply
Expected resolution / human label where appropriate
Rubric
```

Do not let the judge simply decide:

> “Does this sound good?”

It should evaluate whether the response is **supported and useful**.

---

# Day 4 Deliverables

- Escalation policy
- Threshold evaluation
- `evaluation/run_eval.py`
- `evaluation/metrics.py`
- `evaluation/judge.py`
- Baseline vs agent results
- Raw evaluation outputs
- Initial judge scores

## Day 4 Gate

We can now answer:

> Is the AI system actually better than simple approaches, and where?

---

# 9. Day 5 — Judge Validation, Failure Analysis and Submission

## Objective

Turn experimental results into a defensible engineering submission.

No major new architecture on Day 5.

---

# Morning — Validate the LLM Judge

Take approximately:

```text
50 evaluation examples
```

Have a human score the responses using the same rubric.

Then compare:

```text
Human rating
vs
LLM judge rating
```

Possible statistics:

- Mean absolute difference
- Spearman correlation
- Exact agreement
- Adjacent-score agreement

The goal is not to prove that the LLM judge is perfect.

The goal is to show:

> **We measured whether our automated evaluator is aligned with human judgement.**

Document the result in:

```text
evaluation/judge_validation.md
```

---

# Failure Analysis

Find the five most important failure modes.

Each should contain a real example.

Use:

```text
## Failure 1 — [Name]

Customer:
"..."

Expected intent:
"..."

Predicted intent:
"..."

Agent reply:
"..."

Expected / preferred behaviour:
"..."

What went wrong:
...

Hypothesis:
...

Potential fix:
...
```

Good failure categories might include:

- Similar intents being confused
- Retrieval returning superficially similar but incorrect cases
- Unsupported policy claims
- Under-escalation
- Over-escalation
- Short/noisy messages
- Conflicting historical resolutions
- Missing context

Only use categories that actually occur in the experiments.

---

# “What is misleading about my headline number?”

This section is mandatory.

Do not treat it as a disclaimer.

Pick your headline metric and then attack it.

For example:

> **Headline: 87% intent Macro-F1**

Then explain why this number may overstate real-world performance.

Possible issues to investigate:

- Golden set size
- Dataset bias
- Class imbalance
- Historical support data bias
- Retrieval availability
- Distribution shift
- Ambiguous customer language
- LLM judge limitations
- Evaluation examples being easier than real production traffic

The point is to demonstrate that you understand the difference between:

```text
evaluation performance
```

and:

```text
real-world reliability
```

---

# Final Report

Keep the report within six pages.

Recommended structure:

## 1. Problem Framing

- Selected brand
- Why it was selected
- Definition of “good”
- What was intentionally not built

## 2. System

Architecture diagram and concise explanation.

## 3. Evaluation

Baseline comparison table.

Example structure:

| System | Intent Macro-F1 | Reply Quality | Escalation Recall | Unsafe Auto |
|---|---:|---:|---:|---:|
| Majority | — | — | — | — |
| Simple baseline | — | — | — | — |
| AI agent | — | — | — | — |

Use actual experimental results.

## 4. Failure Analysis

Five real failures.

## 5. What Is Misleading About My Headline Number?

Explicit limitations of the headline metric.

## 6. One More Week

Prioritize improvements based on observed failures.

Potential next steps:

1. Improve difficult-case sampling.
2. Tune escalation thresholds from validation data.
3. Test hybrid BM25 + embedding retrieval.
4. Add retrieval-quality gating.
5. Test temporal/distribution shift.
6. Expand human evaluation.

Only include improvements relevant to observed failures.

---

# 10. Decision Log

Maintain `DECISIONS.md`.

Target 10–15 non-obvious decisions.

Suggested structure:

```markdown
# Decision Log

## 1. Brand selection

Decision:
Selected [BRAND].

Why:
...

Alternatives considered:
...

Tradeoff:
...

## 2. Conversation-level split

Decision:
...

Why:
...

## 3. Intent taxonomy size

Decision:
...

Why:
...

## 4. "Other" intent

Decision:
...

Why:
...

## 5. Golden set size

Decision:
...

Why:
...

## 6. Retrieval method

Decision:
...

Why:
...

## 7. Retrieval k

Decision:
...

Why:
...

## 8. Response grounding policy

Decision:
...

Why:
...

## 9. Escalation policy

Decision:
...

Why:
...

## 10. Safety threshold

Decision:
...

Why:
...

## 11. Headline metric

Decision:
...

Why:
...

## 12. LLM judge rubric

Decision:
...

Why:
...

## 13. Judge validation sample

Decision:
...

Why:
...

## 14. Features deliberately excluded

Decision:
...

Why:
...

## 15. Final model / API choice

Decision:
...

Why:
...
```

---

# 11. Daily Working Rhythm

Because this is a solo project, avoid pretending you need formal two-person handoffs.

Instead, every day follows:

```text
Plan
  ↓
Implement
  ↓
Run experiment
  ↓
Save artifact
  ↓
Record decision
  ↓
Run checkpoint
```

Every meaningful experiment should leave behind:

```text
code
+
configuration
+
results
+
decision
```

Do not rely on notebook state or undocumented manual steps.

---

# 12. Daily Checkpoints

## End of Day 1

```text
[ ] Dataset understood
[ ] Brand selected
[ ] Conversations reconstructed
[ ] Initial split created
[ ] Dataset notes written
```

## End of Day 2

```text
[ ] Intent taxonomy defined
[ ] Annotation guidelines written
[ ] 150–250 examples labelled
[ ] Golden set frozen
[ ] Leakage prevention documented
```

## End of Day 3

```text
[ ] Majority baseline works
[ ] Simple baseline works
[ ] Retrieval works
[ ] LLM classifier works
[ ] Response generation works
[ ] End-to-end agent works
```

## End of Day 4

```text
[ ] Escalation policy works
[ ] Thresholds evaluated
[ ] Full evaluation runs automatically
[ ] Automated metrics generated
[ ] LLM judge runs
[ ] Baseline comparison available
```

## End of Day 5

```text
[ ] Judge validated against humans
[ ] Five real failure modes documented
[ ] Headline number caveated
[ ] Report complete
[ ] Decision log complete
[ ] README complete
[ ] Reproduction path tested
[ ] Repository cleaned
[ ] Optional demo works
```

---

# 13. Final Reproducibility Requirement

The README must provide a short path from clean checkout to headline results.

Target:

```bash
git clone <repo>

pip install -r requirements.txt

cp .env.example .env

python scripts/prepare_data.py
python scripts/build_index.py
python evaluation/run_eval.py
```

The complete headline evaluation should run in:

```text
< 15 minutes
```

using the documented sample.

Do not require Hiver to download or process the full 3M-tweet dataset.

---

# 14. Final Submission Checklist

## Dataset

- [ ] Brand selection justified
- [ ] Conversation reconstruction documented
- [ ] Sampling documented
- [ ] Leakage prevention documented

## Golden Set

- [ ] 150–250 examples
- [ ] Human-labelled
- [ ] Sampling methodology documented
- [ ] Annotation guidelines included
- [ ] Golden set frozen

## System

- [ ] Intent classification
- [ ] Historical retrieval
- [ ] Grounded response generation
- [ ] Escalation decision
- [ ] Escalation reason
- [ ] Structured output

## Evaluation

- [ ] Trivial baseline
- [ ] Simple baseline
- [ ] Agent evaluation
- [ ] Automated metrics
- [ ] LLM judge
- [ ] Human vs LLM judge agreement
- [ ] Failure analysis

## Report

- [ ] Problem framing
- [ ] Architecture
- [ ] Baseline comparison
- [ ] Failure analysis
- [ ] Misleading headline number
- [ ] One-week roadmap
- [ ] ≤6 pages

## Repository

- [ ] README
- [ ] Reproduction instructions
- [ ] `.env.example`
- [ ] Tests
- [ ] Decision log
- [ ] No secrets
- [ ] Clean git history
- [ ] Headline results reproducible in <15 minutes

---

# 15. Priority Order If Time Gets Tight

If the five-day schedule starts slipping, cut in this order:

### Cut first

1. Fancy frontend
2. Extra visualization
3. Fine-tuning
4. Advanced retrieval experiments
5. Non-essential engineering abstractions

### Never cut

1. Golden evaluation set
2. Baselines
3. Leakage prevention
4. Escalation evaluation
5. LLM judge validation
6. Failure analysis
7. “What is misleading about my headline number?”
8. Reproducible evaluation

The submission should be able to survive with **no UI at all**. It should not survive without credible evaluation.

---

# Final Definition of Done

The project is complete when a reviewer can:

```text
Clone repository
      ↓
Run documented commands
      ↓
Reproduce headline results
      ↓
Inspect golden examples
      ↓
Inspect baseline comparisons
      ↓
Inspect individual agent decisions
      ↓
See retrieved historical evidence
      ↓
Understand why cases were escalated
      ↓
Inspect judge/human agreement
      ↓
Read five concrete failures
      ↓
Understand what the headline metric hides
```

The final product is therefore not merely an AI chatbot.

It is:

> **A small, reproducible, brand-specific support agent accompanied by evidence that its classifications, replies, and escalation decisions are trustworthy—and clear evidence of where they are not.**
