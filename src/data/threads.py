"""Day 1 afternoon: reconstruct SpotifyCares conversations and create the initial
knowledge/eval-pool split at the conversation level."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from src.data.utils import load_raw, build_conversation_index

BRAND = "SpotifyCares"
OUT_PATH = Path("data/processed/conversations.jsonl")
EVAL_POOL_FRACTION = 0.15  # reserved for Day 2 golden-set labelling, never used for retrieval/taxonomy


def conversation_split(conversation_id: str) -> str:
    """Deterministic conversation-level split so the same conversation always lands
    in the same bucket across re-runs (no leakage between knowledge and eval pool)."""
    h = int(hashlib.sha256(str(conversation_id).encode()).hexdigest(), 16)
    return "eval_pool" if (h % 100) < (EVAL_POOL_FRACTION * 100) else "knowledge"


def main():
    print("Loading raw data...")
    df = load_raw()

    print("Building conversation index...")
    conv_map = build_conversation_index(df)

    brand_tweet_ids = set(df.loc[df["author_id"] == BRAND, "tweet_id"])
    tweet_to_root = {}
    for root, members in conv_map.items():
        for m in members:
            tweet_to_root[m] = root
    brand_conv_roots = {tweet_to_root[t] for t in brand_tweet_ids if t in tweet_to_root}
    print(f"{BRAND}: {len(brand_conv_roots):,} conversations")

    id_to_row = df.set_index("tweet_id")

    records = []
    n_multi_customer = 0
    for root in brand_conv_roots:
        members = conv_map[root]
        sub = id_to_row.loc[members].sort_values("created_at")

        customer_ids = set(sub.loc[sub["inbound"] == True, "author_id"])
        if len(customer_ids) > 1:
            n_multi_customer += 1  # skip: ambiguous multi-customer thread (rare, likely mis-linked)
            continue

        turns = []
        for tid, row in sub.iterrows():
            turns.append({
                "tweet_id": int(tid),
                "speaker": "brand" if row["author_id"] == BRAND else "customer",
                "text": row["text"],
                "created_at": row["created_at"],
            })

        conversation_id = str(root)
        records.append({
            "conversation_id": conversation_id,
            "brand": BRAND,
            "turns": turns,
            "n_turns": len(turns),
            "split": conversation_split(conversation_id),
        })

    print(f"Skipped {n_multi_customer} multi-customer/ambiguous threads")
    print(f"Writing {len(records):,} conversations to {OUT_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n_knowledge = sum(1 for r in records if r["split"] == "knowledge")
    n_eval_pool = sum(1 for r in records if r["split"] == "eval_pool")
    print(f"Split -> knowledge: {n_knowledge:,} | eval_pool: {n_eval_pool:,}")


if __name__ == "__main__":
    main()
