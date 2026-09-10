"""Day 1 dataset recon: schema profiling, conversation reconstruction, brand statistics."""
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.utils import load_raw, build_conversation_index

OUT_PATH = Path("data/samples/brand_statistics.csv")


def profile_schema(df: pd.DataFrame) -> None:
    print("=== Schema ===")
    print(df.dtypes)
    print(f"\nRows: {len(df):,}")
    print(f"Duplicate tweet_id: {df['tweet_id'].duplicated().sum()}")
    print(f"Missing text: {df['text'].isna().sum()}")
    print(f"Missing in_response_to_tweet_id: {df['in_response_to_tweet_id'].isna().sum()}")
    lengths = df["text"].str.len()
    print(f"\nMessage length: mean={lengths.mean():.1f} median={lengths.median():.0f} "
          f"min={lengths.min()} max={lengths.max()}")
    inbound_counts = df["inbound"].value_counts()
    print(f"\nInbound (customer) vs outbound (brand) messages:\n{inbound_counts}")


def identify_brands(df: pd.DataFrame) -> list[str]:
    brand_msgs = df[df["inbound"] == False]
    brand_ids = brand_msgs["author_id"].value_counts()
    print("\n=== Top 20 brand accounts by message volume ===")
    print(brand_ids.head(20))
    return brand_ids.index.tolist()


def brand_statistics(df: pd.DataFrame, conv_map: dict[int, list[int]], brands: list[str]) -> pd.DataFrame:
    id_to_row = df.set_index("tweet_id")
    tweet_to_root = {}
    for root, members in conv_map.items():
        for m in members:
            tweet_to_root[m] = root

    rows = []
    for brand in brands:
        brand_tweet_ids = set(df.loc[df["author_id"] == brand, "tweet_id"])
        conv_roots = {tweet_to_root[t] for t in brand_tweet_ids if t in tweet_to_root}

        n_conversations = len(conv_roots)
        turn_counts = []
        n_customer_msgs = 0
        n_brand_msgs = 0
        n_resolved = 0

        for root in conv_roots:
            members = conv_map[root]
            sub = id_to_row.loc[members]
            turn_counts.append(len(members))
            n_customer_msgs += (sub["inbound"] == True).sum()
            n_brand_msgs += (sub["inbound"] == False).sum()
            last_by_time = sub.sort_values("created_at").iloc[-1]
            if last_by_time["inbound"] == False:
                n_resolved += 1

        rows.append({
            "brand": brand,
            "n_conversations": n_conversations,
            "n_customer_messages": n_customer_msgs,
            "n_brand_messages": n_brand_msgs,
            "avg_turns": np.mean(turn_counts) if turn_counts else 0,
            "median_turns": np.median(turn_counts) if turn_counts else 0,
            "n_resolved_heuristic": n_resolved,
            "pct_resolved_heuristic": n_resolved / n_conversations if n_conversations else 0,
        })

    return pd.DataFrame(rows).sort_values("n_conversations", ascending=False)


def main():
    print("Loading raw data...")
    df = load_raw()
    profile_schema(df)

    brands = identify_brands(df)

    print("\nBuilding conversation index (this walks reply chains)...")
    conv_map = build_conversation_index(df)
    print(f"Total conversations found: {len(conv_map):,}")

    top_brands = brands[:25]
    print(f"\nComputing per-brand statistics for top {len(top_brands)} brands by volume...")
    stats = brand_statistics(df, conv_map, top_brands)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats.to_csv(OUT_PATH, index=False)
    print(f"\nSaved brand statistics to {OUT_PATH}")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
