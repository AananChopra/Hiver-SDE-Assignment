# Decision Log

## 1. LLM provider

Decision:
Groq API (free tier) for classification, response generation, and escalation reasoning.

Why:
Needed a free provider. Gemini's free tier was considered but rejected due to low RPM limits
(~15/min) that would bottleneck running the golden set (200 examples) through classifier +
generator + judge repeatedly during iteration. Groq's free tier has much higher throughput
and is fast enough to run full-set evaluations in seconds rather than minutes.

Tradeoff:
Groq lacks Gemini's native JSON-schema-enforced structured output. Mitigated with a thin
parse-and-retry wrapper around LLM calls (prompt for JSON, validate against schema, retry
once on parse failure).

## 2. LLM judge model

Decision:
Use a different model (or at minimum a different prompt/role framing) than the
generation model for judging, to avoid same-model self-grading bias.

Why:
A model judging its own outputs tends to rate them more favorably. This is a known
evaluation validity risk. To be finalized on Day 4 depending on which Groq-hosted models
are available/reliable at the time (e.g. Llama 3.3 70B for generation, a different
Groq-hosted model for judging).

## 3. Embedding model for retrieval

Decision:
Local sentence-transformers model (all-MiniLM-L6-v2), not an API-based embedding service.

Why:
Keeps the retrieval index build and the <15-minute reproduction path fully offline and
independent of any API quota/cost. Also removes one more rate-limit dependency from the
critical path, on top of the Groq LLM calls.

## 4. Response caching

Decision:
Disk-based cache keyed on hash(model, prompt, params) for all LLM calls, stored under
.cache/ (gitignored).

Why:
Day 3-4 involves repeated iteration on the same golden set through classifier, generator,
and judge. Without caching, every re-run re-burns free-tier quota and adds latency for
calls whose inputs haven't changed. Cache is invalidated by changing the prompt/param hash,
not manually.

## 5. Dataset

Decision:
Customer Support on Twitter (Kaggle: thoughtvector/customer-support-on-twitter).

Why:
Primary dataset specified for the project. ~3M tweets across dozens of brands, multi-turn
threads, real and noisy — matches the project's goal of evaluating against realistic support
data rather than a clean synthetic set.

## 6. Brand selection

Decision:
SpotifyCares.

Why:
Highest resolution-heuristic rate (91.0%) among the top 25 brands by volume, meaning
historical brand responses are more likely to represent an actual resolution worth
grounding replies in. Single-product subscription-service domain gives a naturally
narrow, coherent intent space (billing, account access, subscription changes, technical
issues, feature questions) vs. e-commerce/device brands (Amazon, Apple) whose support
spans too many unrelated product lines for an 8-15 intent taxonomy to stay meaningful.
28,280 conversations is comfortably enough for a 150-250 example golden set with rare
and difficult cases included.

Alternatives considered:
AmazonHelp and AppleSupport (highest volume, but too heterogeneous a support surface).
AmericanAir, Delta, TMobileHelp (airline/telecom — often involve real-time facts like
flight status or line provisioning that historical text can't ground a reply in).

Tradeoff:
SpotifyCares is a mid-volume brand (28K conversations vs. Amazon's 82K), but volume
beyond what's needed for golden-set sampling and a retrieval corpus doesn't add value —
resolution quality and domain coherence matter more for evaluation credibility.

## 7. Conversation-level split

Decision:
Historical/knowledge data and golden evaluation set are split by conversation_id, never
by individual tweet, to prevent leakage where a test message could retrieve another message
from the same conversation. Implemented as a deterministic hash of conversation_id
(SHA-256 mod 100, <15% threshold) rather than a random per-run split, so the split is
stable across re-runs without needing a persisted lookup table. Result: 23,229 conversations
in `knowledge`, 3,978 in `eval_pool` (the pool Day 2 golden-set labelling draws from).

Why:
Required per plan section 3.2 to keep evaluation credible.

## 8. Intent taxonomy size

Decision:
TBD — Day 2 deliverable (target 8-15 intents, discovered from the selected brand's data).

Why:
...

## 9. "Other" intent

Decision:
Included as a catch-all for genuinely unclear/uncategorizable messages.

Why:
Avoids forcing ambiguous cases into ill-fitting categories, which would corrupt both the
taxonomy and downstream classifier training signal.

## 10. Golden set size

Decision:
Target 200 examples (within required 150-250 range).

Why:
Per plan section 2, balances enough statistical signal for macro-F1/escalation metrics
against what's feasible to hand-label solo in one day.

## 11. Retrieval method

Decision:
TBD — Day 3 deliverable (embedding-based vector search, with BM25/TF-IDF baseline for
comparison).

Why:
...

## 12. Retrieval k

Decision:
TBD — Day 3, start at k=3-5 and test whether increasing k helps.

Why:
...

## 13. Response grounding policy

Decision:
Generator must not invent refund policies, compensation, timelines, actions already taken,
or account-specific facts. Must recommend escalation when evidence is insufficient.

Why:
Per plan section 3.3 — historical evidence over invented policy is core to evaluation
credibility and avoiding unsafe auto-handling.

## 14. Escalation policy

Decision:
TBD — Day 4 deliverable (signals + threshold experiment).

Why:
...

## 15. Safety threshold

Decision:
TBD — Day 4, chosen from observed safety/coverage tradeoff across multiple thresholds
(0.60/0.70/0.80/0.90), not arbitrarily set.

Why:
...

## 16. Headline metric

Decision:
TBD — Day 5.

Why:
...

## 17. LLM judge rubric

Decision:
TBD — Day 4 (correctness, groundedness, resolution usefulness, brand appropriateness,
hallucination, overall quality; 1-5 scale).

Why:
...

## 18. Judge validation sample

Decision:
~50 examples, human-scored on the same rubric, compared against LLM judge scores.

Why:
Per plan section 9 — demonstrates the automated evaluator is aligned (or not) with human
judgment, rather than assuming it.

## 19. Features deliberately excluded

Decision:
No real CRM integration, no real financial transactions, no multi-agent orchestration,
no fine-tuning before a strong baseline exists, no support for every brand in the dataset.

Why:
Per plan section 2 scope boundaries — these cannot be evaluated credibly within 5 days and
would dilute focus from evaluation rigor.

## 20. Final model/API choice

Decision:
Groq-hosted open model(s) — specific model IDs to be pinned once selected during Day 1
setup and recorded here.

Why:
...
