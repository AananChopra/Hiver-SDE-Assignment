# Dataset Notes

## Source

Customer Support on Twitter (Kaggle: `thoughtvector/customer-support-on-twitter`),
file `twcs.csv`.

## Schema

| Column | Type | Notes |
|---|---|---|
| `tweet_id` | int | unique, 0 duplicates |
| `author_id` | string | brand handle (e.g. `SpotifyCares`) if outbound, anonymized numeric id if inbound (customer) |
| `inbound` | bool | `True` = customer message, `False` = brand message |
| `created_at` | string | timestamp, Twitter format |
| `text` | string | tweet text, 0 missing |
| `response_tweet_id` | string | id(s) of tweet(s) replying to this one |
| `in_response_to_tweet_id` | int (nullable) | id of the tweet this one replies to; 794,335 / 2,811,774 rows have none (thread roots) |

- 2,811,774 total rows. 1,537,843 inbound (customer), 1,273,931 outbound (brand).
- Message length: mean 113.9 chars, median 115, range 1-513.
- No duplicate `tweet_id`s.

## Conversation reconstruction

Conversations were reconstructed by walking `in_response_to_tweet_id` links back to a root
tweet (the start of each thread), with path-compression memoization for efficiency
(`src/data/utils.py::build_conversation_index`). This found 798,197 conversations across
the full dataset.

## Brand selection

Computed per-brand statistics for the top 25 brands by message volume
(`data/samples/brand_statistics.csv`): conversation count, customer/brand message counts,
avg/median turns per conversation, and a resolution heuristic (conversation's last message
by timestamp is from the brand, not an unanswered customer message).

**Selected brand: SpotifyCares**

| Metric | Value |
|---|---|
| Conversations | 28,280 |
| Resolved (heuristic) | 91.0% — highest of all evaluated brands |
| Avg turns / conversation | 3.25 |
| Median turns | 2.0 |

Why SpotifyCares over higher-volume brands (AmazonHelp, AppleSupport):
- Single-product subscription service -> naturally narrow, coherent intent space
  (billing, account access, subscription changes, technical issues, feature questions),
  unlike e-commerce/device support which spans too many unrelated product lines for an
  8-15 intent taxonomy to stay meaningful.
- Highest resolution-heuristic rate in the candidate set, meaning historical
  brand responses are more likely to represent an actual resolution worth grounding
  replies in, rather than an open/abandoned thread.
- 28K conversations is comfortably enough for a 150-250 example golden set with room
  to include rare and difficult cases.
- Airline/telecom alternatives (Delta, AmericanAir, TMobileHelp) were considered but
  often involve real-time facts (flight status, line provisioning) that historical text
  alone can't ground a reply in — a worse fit for "respond using historical precedent."

## Conversation reconstruction output

`data/processed/conversations.jsonl` — 27,207 SpotifyCares conversations (1,073 threads
with ambiguous multi-customer linkage were excluded; rare, likely an artifact of the
reply-chain reconstruction crossing threads at high-traffic moments).

Each record:
```json
{
  "conversation_id": "...",
  "brand": "SpotifyCares",
  "turns": [{"tweet_id": ..., "speaker": "customer|brand", "text": "...", "created_at": "..."}],
  "n_turns": 2,
  "split": "knowledge|eval_pool"
}
```

## Conversation-level split (leakage prevention)

Split is deterministic (SHA-256 hash of `conversation_id` mod 100), not random-per-run,
so re-running the script always produces the same split without persisting a lookup table.

- `knowledge` (23,229 conversations, ~85%): used for retrieval corpus, taxonomy
  discovery, and development/iteration.
- `eval_pool` (3,978 conversations, ~15%): reserved exclusively for Day 2 golden-set
  labelling. Never touched by retrieval index building or taxonomy discovery — this is
  what prevents a golden-set test message from retrieving another message out of its own
  conversation.
