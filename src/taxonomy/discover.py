"""Day 2 morning: discover recurring intent themes in SpotifyCares customer messages.

Embeds each conversation's opening customer message (the clearest single signal of
"what is this customer asking about"), clusters them, and surfaces representative
examples + distinguishing terms per cluster so the taxonomy can be hand-defined from
what customers actually say, not inherited from another dataset.
"""
import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

CONV_PATH = Path("data/processed/conversations.jsonl")
OUT_PATH = Path("data/samples/intent_clusters.md")
N_EXAMPLES_PER_CLUSTER = 8
N_TERMS_PER_CLUSTER = 10


def clean_text(text: str) -> str:
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_opening_messages() -> list[dict]:
    records = []
    with open(CONV_PATH, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["split"] != "knowledge":
                continue
            first_customer_turn = next(
                (t for t in rec["turns"] if t["speaker"] == "customer"), None
            )
            if first_customer_turn is None:
                continue
            cleaned = clean_text(first_customer_turn["text"])
            if len(cleaned) < 5:
                continue
            records.append({
                "conversation_id": rec["conversation_id"],
                "raw_text": first_customer_turn["text"],
                "clean_text": cleaned,
            })
    return records


def pick_k(embeddings: np.ndarray, k_range: range) -> int:
    print("Selecting k via silhouette score on a sample...")
    sample_idx = np.random.RandomState(42).choice(
        len(embeddings), size=min(5000, len(embeddings)), replace=False
    )
    sample = embeddings[sample_idx]
    best_k, best_score = k_range[0], -1
    for k in k_range:
        labels = KMeans(n_clusters=k, random_state=42, n_init=5).fit_predict(sample)
        score = silhouette_score(sample, labels, sample_size=min(2000, len(sample)))
        print(f"  k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_k, best_score = k, score
    return best_k


def main():
    print("Loading opening customer messages from knowledge split...")
    records = load_opening_messages()
    print(f"{len(records):,} opening messages loaded")

    print("Embedding with all-MiniLM-L6-v2 (local, CPU)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [r["clean_text"] for r in records]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)

    k = pick_k(embeddings, range(8, 16))
    print(f"\nSelected k={k}")

    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    tfidf = TfidfVectorizer(max_df=0.5, min_df=5, stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = tfidf.fit_transform(texts)
    terms = np.array(tfidf.get_feature_names_out())

    lines = ["# Discovered Intent Clusters (raw, pre-labelling)\n"]
    lines.append(f"SpotifyCares knowledge split, {len(records):,} opening customer messages, k={k}\n")

    for cluster_id in range(k):
        idx = np.where(labels == cluster_id)[0]
        size = len(idx)
        pct = size / len(records) * 100

        cluster_tfidf_mean = np.asarray(tfidf_matrix[idx].mean(axis=0)).ravel()
        top_term_idx = cluster_tfidf_mean.argsort()[::-1][:N_TERMS_PER_CLUSTER]
        top_terms = terms[top_term_idx].tolist()

        centroid = kmeans.cluster_centers_[cluster_id]
        dists = np.linalg.norm(embeddings[idx] - centroid, axis=1)
        closest = idx[np.argsort(dists)[:N_EXAMPLES_PER_CLUSTER]]

        lines.append(f"\n## Cluster {cluster_id} — {size} messages ({pct:.1f}%)\n")
        lines.append(f"**Top terms:** {', '.join(top_terms)}\n")
        lines.append("**Representative examples:**")
        for i in closest:
            lines.append(f"- {records[i]['clean_text']!r}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote cluster report to {OUT_PATH}")


if __name__ == "__main__":
    main()
