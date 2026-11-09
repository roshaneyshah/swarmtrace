"""Alias linking: recover which names belong to the same underlying agent.

Key observation: an agent holds one name at a time, so the names of one agent
form a *chain* of non-overlapping activity intervals. Linking therefore reduces
to choosing, for every name, at most one predecessor name that went quiet
before it appeared. We solve this jointly as a min-cost bipartite matching,
scoring candidate links by stylometric similarity plus a hand-off prior on the
gap between the old name's last post and the new name's first post.
"""
from __future__ import annotations

import re
from collections import defaultdict

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score

MENTION = re.compile(r"@\S+")


def alias_table(board):
    docs, span = defaultdict(list), {}
    for m in board:
        a = m["alias"]
        docs[a].append(MENTION.sub(" ", m["text"]))
        s = span.setdefault(a, [m["t"], m["t"]])
        s[0] = min(s[0], m["t"]); s[1] = max(s[1], m["t"])
    names = sorted(docs, key=lambda a: (span[a][0], a))
    return names, [" \n ".join(docs[a]) for a in names], np.array([span[a] for a in names])


def style_matrix(docs):
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, min_df=2)
    X = vec.fit_transform(docs)
    return (X @ X.T).toarray()          # rows are L2-normalised -> cosine


def chain_link(names, S, span, beta=0.6, tau=4.0, theta=0.55, use_style=True, use_time=True):
    """Return cluster labels via predecessor matching. Cost of 'no predecessor' = -theta."""
    n = len(names)
    start, end = span[:, 0], span[:, 1]
    valid = end[None, :] < start[:, None]                    # [succ j, pred i]
    gap = start[:, None] - end[None, :]
    score = np.zeros((n, n))
    if use_style:
        score += S
    if use_time:
        score += beta * np.exp(-np.clip(gap, 0, None) / tau)
    BIG = 1e6
    cost = np.where(valid, -score, BIG)
    dummy = np.full((n, n), BIG)
    np.fill_diagonal(dummy, -theta)
    r, c = linear_sum_assignment(np.hstack([cost, dummy]))
    parent = np.arange(n)
    for j, i in zip(r, c):
        if i < n and cost[j, i] < BIG / 2:
            parent[j] = i
    # resolve chains to roots
    label = np.empty(n, dtype=int)
    for j in range(n):
        k = j
        while parent[k] != k:
            k = parent[k]
        label[j] = k
    return label


def style_cluster(S, k):
    D = np.clip(1 - S, 0, None)
    return AgglomerativeClustering(n_clusters=k, metric="precomputed", linkage="average").fit_predict(D)


def bcubed(pred, gold):
    pred, gold = np.asarray(pred), np.asarray(gold)
    P = R = 0.0
    for x in range(len(pred)):
        same_p = pred == pred[x]
        same_g = gold == gold[x]
        both = (same_p & same_g).sum()
        P += both / same_p.sum(); R += both / same_g.sum()
    P /= len(pred); R /= len(pred)
    return P, R, 2 * P * R / (P + R)


def evaluate(pred, gold):
    P, R, F = bcubed(pred, gold)
    return dict(bcubed_P=P, bcubed_R=R, bcubed_F1=F, ARI=adjusted_rand_score(gold, pred),
                n_identities=int(len(set(pred))))


def constrained_cluster(S, span, theta=0.35, T=None, beta=0.0, tau=4.0):
    """Average-linkage clustering on style with a cannot-link constraint:
    two groups of names may merge only if no two of their activity intervals
    overlap (one agent holds one name at a time). Optional hand-off bonus
    `beta*exp(-gap/tau)` for the closest end->start transition between groups.
    Stops when the best admissible average similarity falls below theta."""
    n = len(S)
    T = int(span.max()) + 1 if T is None else T
    occ = np.zeros((n, T), dtype=np.float32)
    for i, (a, b) in enumerate(span):
        occ[i, a:b + 1] = 1
    W = S.astype(np.float64).copy()            # sum of pairwise similarities
    cnt = np.ones(n)
    alive = np.ones(n, bool)
    starts = [[int(a)] for a, _ in span]
    ends = [[int(b)] for _, b in span]
    ov = (occ @ occ.T) > 0
    NEG = -1e9

    def bonus(i, js):
        if beta == 0:
            return 0.0
        out = np.zeros(len(js))
        for q, j in enumerate(js):
            g = [s - e for s in starts[j] for e in ends[i] if s > e] + [s - e for s in starts[i] for e in ends[j] if s > e]
            out[q] = beta * np.exp(-min(g) / tau) if g else 0.0
        return out

    A = W / np.outer(cnt, cnt)
    if beta:
        start, end = span[:, 0], span[:, 1]
        gap = np.minimum(np.where(start[:, None] > end[None, :], start[:, None] - end[None, :], 1e9),
                         np.where(start[None, :] > end[:, None], start[None, :] - end[:, None], 1e9))
        A = A + beta * np.exp(-gap / tau)
    A[ov] = NEG
    np.fill_diagonal(A, NEG)
    label = np.arange(n)
    while True:
        k = int(np.argmax(A))
        i, j = divmod(k, n)
        if A[i, j] < theta:
            break
        # merge j into i
        W[i] += W[j]; W[:, i] = W[i]
        cnt[i] += cnt[j]
        occ[i] = np.maximum(occ[i], occ[j])
        starts[i] += starts[j]; ends[i] += ends[j]
        alive[j] = False
        label[label == j] = i
        A[j, :] = NEG; A[:, j] = NEG
        row = W[i] / (cnt[i] * cnt)
        idx = np.where(alive)[0]
        row_b = np.full(n, 0.0)
        if beta:
            row_b[idx] = bonus(i, idx)
        new = row + row_b
        bad = (occ @ occ[i]) > 0
        new[bad | ~alive] = NEG
        new[i] = NEG
        A[i, :] = new; A[:, i] = new
    return label
