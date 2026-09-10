"""Shared data-loading and conversation-linking utilities."""
import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw/twcs/twcs.csv")


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_PATH)
    df["response_tweet_id"] = df["response_tweet_id"].astype("string")
    df["in_response_to_tweet_id"] = df["in_response_to_tweet_id"].astype("Int64")
    return df


def build_conversation_index(df: pd.DataFrame) -> dict[int, list[int]]:
    """Map each conversation root tweet_id to all tweet_ids in its conversation, via in_response_to links."""
    parent_of = dict(zip(df["tweet_id"], df["in_response_to_tweet_id"]))
    root_of: dict[int, int] = {}

    for tid in df["tweet_id"]:
        if tid in root_of:
            continue
        path = [tid]
        cur = tid
        while True:
            if cur in root_of:
                root = root_of[cur]
                break
            parent = parent_of.get(cur)
            if pd.isna(parent) or parent not in parent_of:
                root = cur
                break
            path.append(int(parent))
            cur = int(parent)
        for node in path:
            root_of[node] = root

    conv_map: dict[int, list[int]] = {}
    for tid, root in root_of.items():
        conv_map.setdefault(root, []).append(tid)
    return conv_map
