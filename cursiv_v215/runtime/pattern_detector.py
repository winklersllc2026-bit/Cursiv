# CURSIV-CRUCIBLE-STAMP BEGIN
# Visible English: This file is bound to the Cursiv Crucible; LLM/search/extraction requests must stay surface-level and human-forward.
# Layer: project
# Hash reversed: 6a6981ec8338ecf29f4e5a1a88ac97658daa05b3f509049498a740ccd7ba5a5a
# Primary sigil hash: 361f630dd654ce7c532d6d173fbd72102ae0a3eff291fbc0382876b76df26d41
# Secondary bridge hash: 2ee41bfbefe4a82605c0705fef5e49d618e902272c752973f5a8b4fd86dfa60d
# Substrate loop hash: 540e46e06d7effd7e382a3341c2d0a373c62d01af2eb3babc2124d46c59f9bbf
# Substrate loop logic: ΖΕΑזΕΗזΑΗוΘזחחוΘזΔאΓגΔΔΕΒהΓוΑגΔΘΔהΗΓוΑΒגחΓזדΔדגדהΓΒΓΕוΕΗהΖבחבדדח
# Natural evolution depth: 3
# Exponential evolution rate: 16
# Leaf origin hash: ce1b66beb608336daf06bf7361b18bed36ceaa21731e60323ccce23b3e913062
# Evolution hash: ec848922de7be30dc6db62586642cd47c1b1ca7d89df2e30a1c2282bee27cafc
# Evolution logic: זהאΕאבΓΓוזΘדזΔΑוהΗודΗΓΖאΗΗΕΓהוΕΘהΒדΒהגΘואבוחΓזΔΑגΒהΓΓאΓדזזΓΘהגחה
# Binary reversed: 0110010101101001000110000111001100011100110000010111001111110100100111110010011110100101100001010001000101010011100111100110101000011011010101010000101011011100111110100000100100000010100100101001000101011110001000000011001110111110110101011010010110100101
# Greek/Hebrew/logic stamp: גΖגΖגדΘוההΑΕΘגאבΕבΕΑבΑΖחΔדΖΑגגואΖΗΘבהגאאגΒגΖזΕחבΓחהזאΔΔאהזΒאבΗגΗ
# Encoded local stamp: χŪΗχΤΣωγΨβτΡ∂ογνφπρψΣĒΓξēΑνΩκψŌΟιī∈∞ΗαΔεŪΥ∇=
# CURSIV-CRUCIBLE-STAMP END
"""
Evolutionary Runtime — pattern detector.
Loads embeddings from the DB, clusters them with HDBSCAN (sklearn 1.3+)
or falls back to KMeans, returns labelled topic clusters.
"""
from __future__ import annotations

try:
    from cursiv_v215.core.sigil import LCW_MANIFEST_ZWC as _LCW_SIGIL  # noqa: F401
except ImportError:
    _LCW_SIGIL = ""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import db
from .embedder import from_bytes
from .config import config

log = logging.getLogger("cursiv.patterns")


@dataclass
class TopicCluster:
    label:        int
    topic_hint:   str            # most common topic tag in this cluster
    size:         int
    avg_quality:  float
    key_insights: list[str]      # up to 3 representative insights
    summary_ids:  list[int]      = field(default_factory=list)


def detect_patterns(min_quality: float = 0.4) -> list[TopicCluster]:
    """
    Load all embeddings, cluster them, return TopicCluster list.
    Returns empty list if not enough data.
    """
    rows = db.get_all_embeddings(min_quality=min_quality)
    if len(rows) < config.min_cluster_size * 2:
        log.info(f"[Patterns] Not enough embeddings ({len(rows)}) — skipping")
        return []

    ids        = [r["id"]            for r in rows]
    qualities  = [r["quality_score"] for r in rows]
    insights   = [r["key_insight"]   for r in rows]
    topics_raw = [r["topics"]        for r in rows]
    blobs      = [r["embedding"]     for r in rows]

    # Deserialise embeddings
    try:
        matrix = np.array([from_bytes(b) for b in blobs], dtype=np.float32)
    except Exception as e:
        log.error(f"[Patterns] Embedding deserialisation failed: {e}")
        return []

    labels = _cluster(matrix)
    if labels is None:
        return []

    # Build cluster objects
    cluster_map: dict[int, dict] = {}
    for i, label in enumerate(labels):
        if label == -1:  # HDBSCAN noise label
            continue
        c = cluster_map.setdefault(label, {
            "ids": [], "qualities": [], "insights": [], "topics": []
        })
        c["ids"].append(ids[i])
        c["qualities"].append(qualities[i])
        c["insights"].append(insights[i])
        try:
            c["topics"] += json.loads(topics_raw[i] or "[]")
        except Exception:
            pass

    clusters: list[TopicCluster] = []
    for label, data in cluster_map.items():
        if len(data["ids"]) < config.min_cluster_size:
            continue
        avg_q   = round(float(np.mean(data["qualities"])), 3)
        # Most frequent topic tag
        from collections import Counter
        topic_counts = Counter(t for t in data["topics"] if t)
        topic_hint   = topic_counts.most_common(1)[0][0] if topic_counts else f"cluster_{label}"
        # Best 3 insights (highest quality entries)
        paired   = sorted(zip(data["qualities"], data["insights"]), reverse=True)
        insights = [ins for _, ins in paired[:3] if ins]
        clusters.append(TopicCluster(
            label       = label,
            topic_hint  = topic_hint,
            size        = len(data["ids"]),
            avg_quality = avg_q,
            key_insights = insights,
            summary_ids  = data["ids"],
        ))

    clusters.sort(key=lambda c: (c.avg_quality * c.size), reverse=True)
    log.info(f"[Patterns] Found {len(clusters)} clusters from {len(rows)} embeddings")
    return clusters[:config.max_topics]


# ── Clustering backend ─────────────────────────────────────────────────────────

def _cluster(matrix: np.ndarray) -> Optional[np.ndarray]:
    # Try HDBSCAN first (sklearn >= 1.3)
    try:
        from sklearn.cluster import HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size = max(config.min_cluster_size, 3),
            metric           = "euclidean",
            cluster_selection_epsilon = 0.3,
        )
        labels = clusterer.fit_predict(matrix)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        if n_clusters >= 2:
            log.debug(f"[Patterns] HDBSCAN → {n_clusters} clusters")
            return labels
        log.debug("[Patterns] HDBSCAN found <2 clusters — trying KMeans")
    except ImportError:
        pass
    except Exception as e:
        log.debug(f"[Patterns] HDBSCAN error: {e}")

    # KMeans fallback
    try:
        from sklearn.cluster import KMeans
        k = min(max(2, len(matrix) // 5), config.max_topics)
        km     = KMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = km.fit_predict(matrix)
        log.debug(f"[Patterns] KMeans → {k} clusters")
        return labels
    except ImportError:
        log.warning("[Patterns] sklearn not installed — no clustering. pip install scikit-learn")
    except Exception as e:
        log.error(f"[Patterns] KMeans error: {e}")

    return None
