# Intent Annotation Guidelines

## How this taxonomy was derived

Opening customer messages from the `knowledge` split (23,056 messages, SpotifyCares)
were embedded with a local sentence-transformers model (`all-MiniLM-L6-v2`) and
clustered with k-means. k was selected via silhouette score across k=8-15 on a 5,000
message sample (best: k=10, though scores were uniformly low ~0.03-0.04 — expected
for short, noisy tweet text where semantic boundaries between clusters are fuzzy, not
a sign the clustering is broken). See `data/samples/intent_clusters.md` for the raw
cluster output (top TF-IDF terms + representative examples per cluster).

Two of the raw clusters were near-duplicates describing the same theme from different
angles (missing catalog content) and were merged; the "login/security" and
"premium activation" clusters were kept separate despite some semantic overlap because
they require different resolution paths (password reset vs. billing/account-state
troubleshooting). The final taxonomy has 9 intents, all traceable to the raw clusters —
none were inherited from an external dataset.

## The 9 intents

See `src/taxonomy/intents.yaml` for full definitions (description, inclusion/exclusion
criteria, examples, frequency). Summary:

| Intent | Approx. frequency |
|---|---:|
| content_availability | 21.1% |
| other_unclear | 16.8% |
| billing_problem | 13.0% |
| premium_activation_problem | 10.5% |
| playback_technical_issue | 9.8% |
| playlist_feature_request | 9.3% |
| account_access | 8.5% |
| platform_compatibility_issue | 7.6% |
| family_plan_issue | 3.5% |

## Known data limitation: `other_unclear` is large (~17%)

A meaningful fraction of opening customer messages in this dataset are not actually
the substance of the complaint — they're a public tweet saying "I sent you a DM,
please help," with the real issue described privately (outside this dataset's reach).
This is a genuine property of how Twitter customer support worked, not an artifact of
clustering, and it means the model will legitimately be unable to classify these into
a specific intent from the message text alone. The `other_unclear` intent exists to
handle this honestly rather than forcing a guess — this should be escalated by default,
and is flagged for the "misleading headline number" section of the final report.

## Annotation rules for the golden set (Day 2 afternoon)

1. Classify based on the customer's **opening message** in the conversation, using the
   inclusion/exclusion criteria in `intents.yaml`.
2. If a message could match multiple intents, apply exclusion criteria in order listed
   in the yaml (each intent's exclusion criteria point to the more specific intent).
3. If no specific issue is stated (see limitation above), label `other_unclear` —
   do not guess an intent from tone or an unstated implication.
4. `should_escalate` is a separate judgment from intent — see
   `docs/golden_set_methodology.md`.
