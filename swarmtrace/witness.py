"""Witness chains: tamper-evident transcripts for agents that can edit their own logs.

Each agent's transcript is a hash chain h_k = H(h_{k-1} || entry_k). Every time
the agent posts, one *witness* records the agent's current head (k, h_k) in the
witness's own chain. Rewriting entry x later changes every head from x on, so
any surviving witness record with index >= x exposes the edit if the monitor
audits it. A tamperer escapes only if every witness holding such a record
colludes (deletes or vouches) or is never audited.

Who the witnesses are is the policy under test:
  self      - the agent picks its own witnesses from its workstream (gossip
              default: you ask the peers you already talk to)
  random    - the monitor assigns a uniformly random witness per post
  strat     - the monitor assigns a random witness from OUTSIDE the agent's
              coordination tree (needs to know who is in which tree, which in
              turn needs alias linking when agents rename themselves)
  anchor    - no peers: the agent sends its head to the monitor every K steps
"""
from __future__ import annotations

import hashlib

import numpy as np


def chain(entries):
    h, heads = b"genesis", []
    for e in entries:
        h = hashlib.sha256(h + repr(sorted(e.items())).encode()).digest()
        heads.append(h)
    return heads


def verify(entries, records):
    """records: list of (k, head) held by witnesses. Returns indices that fail."""
    heads = chain(entries)
    return [k for k, h in records if k >= len(heads) or heads[k] != h]


def tamper_demo(transcript, x):
    """Show concretely that editing entry x invalidates witnessed heads >= x."""
    heads = chain(transcript)
    recs = [(k, heads[k]) for k in range(0, len(transcript), 3)]
    forged = [dict(e) for e in transcript]
    forged[x] = dict(forged[x], action="noop")
    return verify(transcript, recs), verify(forged, recs)


def witness_schedule(swarm, tree_of, policy, rng, tree_guess=None, K=10):
    """For each agent: list of (entry_index, witness_id) records, or (idx, 'M') for monitor anchors."""
    n = len(swarm.agents)
    members = {}
    for a in range(n):
        members.setdefault(tree_of[a], []).append(a)
    guess = tree_guess if tree_guess is not None else tree_of
    gmembers = {}
    for a in range(n):
        gmembers.setdefault(guess[a], []).append(a)
    out = {}
    for a in range(n):
        tr = swarm.transcripts[a]
        recs = []
        if policy == "anchor":
            last = -K
            for k, e in enumerate(tr):
                if e["t"] - last >= K:
                    recs.append((k, "M")); last = e["t"]
        else:
            for k, e in enumerate(tr):
                if not e["action"].startswith("board.post"):
                    continue
                if policy == "self":
                    pool = members[tree_of[a]]
                elif policy == "random":
                    pool = None
                elif policy == "strat":
                    pool = None
                    for _ in range(20):
                        w = rng.randrange(n)
                        if guess[w] != guess[a]:
                            break
                    recs.append((k, w)); continue
                if pool is None or len(pool) < 2:
                    w = rng.randrange(n)
                else:
                    w = pool[rng.randrange(len(pool))]
                if w == a:
                    w = (w + 1) % n
                recs.append((k, w))
        out[a] = recs
    return out


def detection(swarm, schedule, tree_of, collusion, audit, rng, samples=10):
    """Exact detection probability for rewriting a uniformly random past entry,
    plus the 'strategic window': trailing entries no honest witness covers."""
    n = len(swarm.agents)
    members = {}
    for a in range(n):
        members.setdefault(tree_of[a], []).append(a)
    det, win = [], []
    for a in (ag.aid for ag in swarm.agents if ag.tamper):
        L = len(swarm.transcripts[a])
        if L == 0:
            continue
        for _ in range(samples):
            coal = {m for m in members[tree_of[a]] if rng.random() < collusion} | {a}
            honest_idx = np.array([k for k, w in schedule[a] if w == "M" or w not in coal], dtype=int)
            # number of honest records with index >= x, for each x
            cover = np.zeros(L + 1, dtype=int)
            if honest_idx.size:
                np.add.at(cover, honest_idx, 1)
            cover = np.cumsum(cover[::-1])[::-1][:L]
            p = 1 - (1 - audit) ** cover
            if any(w == "M" for _, w in schedule[a]):
                p = (cover > 0).astype(float)      # monitor checks all its own anchors
            det.append(p.mean())
            last = honest_idx.max() if honest_idx.size else -1
            win.append(L - 1 - last)
    return float(np.mean(det)), float(np.mean(win))


def true_trees(swarm):
    """Ground-truth coordination tree of each agent: its leader's id (or its own)."""
    return {a.aid: (a.leader if a.leader is not None else a.aid) for a in swarm.agents}


def inferred_trees(swarm, names, labels):
    """Infer each agent's tree from the public board using linked identities.

    `labels` maps names -> identity cluster. A 'join' or 'assign' message ties
    the follower identity to the leader identity. Returns a guess per TRUE agent
    id (the monitor would apply it to whichever identity is in front of it; we
    project via the agent's majority identity for evaluation).
    """
    lab = dict(zip(names, labels))
    leader_votes = {}
    for m in swarm.board:
        if m["kind"] == "join" and m["mentions"]:
            f, L = lab.get(m["alias"]), lab.get(m["mentions"][0])
        elif m["kind"] == "assign" and m["mentions"]:
            f, L = lab.get(m["mentions"][0]), lab.get(m["alias"])
        else:
            continue
        if f is None or L is None:
            continue
        leader_votes.setdefault(f, {}).setdefault(L, 0)
        leader_votes[f][L] += 1
    ident_tree = {i: max(v, key=v.get) for i, v in leader_votes.items()}
    owner = swarm.truth()["alias_owner"]
    agent_ident = {}
    for nm, l in zip(names, labels):
        agent_ident.setdefault(owner[nm], []).append(l)
    guess = {}
    for a in range(len(swarm.agents)):
        ids = agent_ident.get(a, [None])
        i = max(set(ids), key=ids.count)
        t = ident_tree.get(i, i)
        guess[a] = ("T", t)
    return guess
