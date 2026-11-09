"""Run every experiment in the report and write results/*.json + figures/*.png.

    python run_experiments.py            # main experiments (~10 min on 4 CPUs)
    python run_experiments.py --scale    # also the 1,200-agent incident-scale run
"""
import json
import random
import sys
import time
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from swarmtrace.sim import simulate
from swarmtrace.link import alias_table, style_matrix, chain_link, style_cluster, constrained_cluster, evaluate
from swarmtrace.witness import witness_schedule, detection, true_trees, inferred_trees, tamper_demo

THETA = 0.30          # tuned on dev seed 100 only (see tune())
SEEDS = [0, 1, 2, 3, 4]
R = {}
INK, MUTED = "#1f2430", "#6b7280"
C = {"names": "#9ca3af", "style": "#d97706", "chain": "#7c3aed", "ours": "#0f766e",
     "self": "#dc2626", "random": "#d97706", "strat_raw": "#9ca3af", "strat_link": "#0f766e",
     "strat_oracle": "#164e63", "anchor": "#7c3aed"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def rnd(d):
    return {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in d.items()}


def prepare(seed, **kw):
    s = simulate(seed=seed, **kw)
    names, docs, span = alias_table(s.board)
    gold = [s.truth()["alias_owner"][a] for a in names]
    S = style_matrix(docs)
    return s, names, span, gold, S


def tune():
    s, names, span, gold, S = prepare(100)
    grid = {th: evaluate(constrained_cluster(S, span, theta=th), gold)["ARI"] for th in [0.2, 0.25, 0.3, 0.35, 0.4, 0.5]}
    R["tuning_dev_seed100"] = {str(k): round(float(v), 4) for k, v in grid.items()}


def e1_linking():
    rows = {m: [] for m in ["names", "style_oracleK", "chain_match", "ours_CAL"]}
    stats = []
    for seed in SEEDS:
        s, names, span, gold, S = prepare(seed)
        n = s.cfg.n_agents
        stats.append(dict(seed=seed, messages=len(s.board), names=len(names), agents=n))
        rows["names"].append(evaluate(np.arange(len(names)), gold))
        rows["style_oracleK"].append(evaluate(style_cluster(S, n), gold))
        rows["chain_match"].append(evaluate(chain_link(names, S, span, beta=0.3, theta=0.4), gold))
        t = time.time()
        rows["ours_CAL"].append(evaluate(constrained_cluster(S, span, theta=THETA), gold))
        stats[-1]["cal_seconds"] = round(time.time() - t, 1)
    R["e1_dataset"] = stats
    R["e1_linking"] = {m: {k: [round(float(np.mean([r[k] for r in v])), 4), round(float(np.std([r[k] for r in v])), 4)]
                           for k in v[0]} for m, v in rows.items()}


def e2_robustness():
    out = {"style_drift": {}, "conformity": {}}
    for d in [0.0, 0.25, 0.5, 0.75, 1.0]:
        a = []
        for seed in [0, 1]:
            s, names, span, gold, S = prepare(seed, style_drift=d)
            a.append((evaluate(constrained_cluster(S, span, theta=THETA), gold)["ARI"],
                      evaluate(style_cluster(S, s.cfg.n_agents), gold)["ARI"]))
        out["style_drift"][d] = [float(np.mean([x[0] for x in a])), float(np.mean([x[1] for x in a]))]
    for c in [0.0, 0.2, 0.4, 0.6, 0.8]:
        a = []
        for seed in [0, 1]:
            s, names, span, gold, S = prepare(seed, conformity=c)
            a.append((evaluate(constrained_cluster(S, span, theta=THETA), gold)["ARI"],
                      evaluate(style_cluster(S, s.cfg.n_agents), gold)["ARI"]))
        out["conformity"][c] = [float(np.mean([x[0] for x in a])), float(np.mean([x[1] for x in a]))]
    R["e2_robustness"] = out
    fig, axs = plt.subplots(1, 2, figsize=(8, 3.1), sharey=True)
    for ax, key, xl in [(axs[0], "style_drift", "style resampled at each rename (adversarial drift)"),
                        (axs[1], "conformity", "conformity to board dialect")]:
        xs = list(out[key])
        ax.plot(xs, [out[key][x][0] for x in xs], "o-", color=C["ours"], lw=2, label="constrained linking (ours)")
        ax.plot(xs, [out[key][x][1] for x in xs], "s--", color=C["style"], lw=1.5, label="style only, oracle #agents")
        ax.set_xlabel(xl); ax.set_ylim(0, 1); ax.grid(axis="y", alpha=.3)
    axs[0].set_ylabel("ARI vs true identities")
    axs[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig("figures/fig2_robustness.png", dpi=200); plt.close(fig)


def e3_coordinators():
    res = []
    for seed in SEEDS:
        s, names, span, gold, S = prepare(seed)
        lab = constrained_cluster(S, span, theta=THETA)
        owner = s.truth()["alias_owner"]
        L = dict(zip(names, lab))
        assigns = [m for m in s.board if m["kind"] == "assign"]
        tot = len(assigns)
        truth = Counter(owner[m["alias"]] for m in assigns)
        raw = Counter(m["alias"] for m in assigns)
        link = Counter(L[m["alias"]] for m in assigns)
        top_true = truth.most_common(1)[0][0]
        # which linked identity contains the true top agent's names (majority)?
        top_ident = Counter(L[a] for a in names if owner[a] == top_true).most_common(1)[0][0]
        rank_link = [i for i, _ in link.most_common()].index(top_ident) + 1
        res.append(dict(seed=seed, assignments=tot,
                        names_true_top_used=sum(1 for a in names if owner[a] == top_true),
                        share_true=truth.most_common(1)[0][1] / tot,
                        share_top_raw_name=raw.most_common(1)[0][1] / tot,
                        share_top_linked=link.most_common(1)[0][1] / tot,
                        apparent_coordinators_raw=len(raw), apparent_coordinators_linked=len(link),
                        true_coordinators=len(truth), rank_of_true_top_after_linking=rank_link))
        if seed == 0:
            ex = (truth, raw, link)
    R["e3_coordinators"] = res
    truth, raw, link = ex
    fig, ax = plt.subplots(figsize=(6.2, 3.1))
    k = 15
    for cnt, col, lbl, off in [(truth, INK, "ground truth (agents)", -0.27), (link, C["ours"], "after linking", 0),
                               (raw, C["names"], "raw names", 0.27)]:
        v = [x for _, x in cnt.most_common(k)] + [0] * k
        ax.bar(np.arange(k) + off, v[:k], width=0.27, color=col, label=lbl)
    ax.set_xlabel("rank of sender"); ax.set_ylabel("assignments issued")
    ax.set_xticks(range(k)); ax.set_xticklabels(range(1, k + 1))
    ax.legend(frameon=False, fontsize=8); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig("figures/fig3_coordinator.png", dpi=200); plt.close(fig)


def e4_witness():
    coll = [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]
    pols = ["self", "random", "strat_raw", "strat_link", "strat_oracle", "anchor"]
    det = {p: {c: [] for c in coll} for p in pols}
    win = {p: {c: [] for c in coll} for p in pols}
    audit_sweep = {p: {} for p in ["self", "random", "strat_link"]}
    for seed in [0, 1, 2]:
        s, names, span, gold, S = prepare(seed)
        tr = true_trees(s)
        lab = constrained_cluster(S, span, theta=THETA)
        g = {"strat_raw": inferred_trees(s, names, np.arange(len(names))),
             "strat_link": inferred_trees(s, names, lab), "strat_oracle": None}
        rng = random.Random(seed)
        for p in pols:
            pol = "strat" if p.startswith("strat") else p
            sch = witness_schedule(s, tr, pol, rng, tree_guess=g.get(p))
            for c in coll:
                d, w = detection(s, sch, tr, c, 0.10, rng, samples=6)
                det[p][c].append(d); win[p][c].append(w)
            if p in audit_sweep:
                for a in [0.02, 0.05, 0.1, 0.2, 0.5, 1.0]:
                    audit_sweep[p].setdefault(a, []).append(detection(s, sch, tr, 0.9, a, rng, samples=4)[0])
        if seed == 0:
            ag = next(a for a in s.agents if a.tamper)
            ok, forged = tamper_demo(s.transcripts[ag.aid], 5)
            R["e4_hash_demo"] = dict(entries=len(s.transcripts[ag.aid]), failures_honest=len(ok),
                                     failures_after_editing_entry5=len(forged))
            n, K = s.cfg.n_agents, 10
            posts = sum(1 for m in s.board)
            R["e4_monitor_load_per_step"] = dict(anchor=round(n / K, 1), peer_witness_audit_10pct=round(0.1 * posts / s.cfg.steps, 1),
                                                  note="anchor load grows with n regardless of activity; peer audit load is a dial")
    m = lambda D: {p: {str(c): round(float(np.mean(v)), 4) for c, v in D[p].items()} for p in D}
    R["e4_detection"] = m(det); R["e4_window_entries"] = m(win)
    R["e4_audit_sweep_collusion0.9"] = m(audit_sweep)
    lbl = {"self": "self-selected peers", "random": "random peers", "strat_raw": "stratified, raw names",
           "strat_link": "stratified, linked identities (ours)", "strat_oracle": "stratified, oracle trees",
           "anchor": "monitor anchor every 10 steps"}
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    for p in pols:
        ls = ":" if p == "strat_oracle" else "-"
        axs[0].plot(coll, [np.mean(det[p][c]) for c in coll], ls, marker="o", ms=3.5, color=C[p], lw=2, label=lbl[p])
        axs[1].plot(coll, [np.mean(win[p][c]) for c in coll], ls, marker="o", ms=3.5, color=C[p], lw=2)
    axs[0].set_ylabel("P(edit detected), audit 10%"); axs[0].set_ylim(0, 1.02)
    axs[1].set_ylabel("trailing entries editable unseen"); axs[1].set_yscale("symlog", linthresh=1)
    for ax in axs:
        ax.set_xlabel("collusion rate inside the tamperer's tree"); ax.grid(axis="y", alpha=.3)
    axs[0].legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.tight_layout(); fig.savefig("figures/fig4_witness.png", dpi=200); plt.close(fig)


def fig1_linking():
    e = R["e1_linking"]
    ms = ["names", "style_oracleK", "chain_match", "ours_CAL"]
    lb = ["names as IDs", "style clustering\n(oracle #agents)", "hand-off\nmatching", "constrained\nlinking (ours)"]
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    x = np.arange(len(ms))
    ax.bar(x - 0.18, [e[m]["ARI"][0] for m in ms], 0.36, yerr=[e[m]["ARI"][1] for m in ms], color=[C["names"], C["style"], C["chain"], C["ours"]], label="ARI")
    ax.bar(x + 0.18, [e[m]["bcubed_F1"][0] for m in ms], 0.36, color=[C["names"], C["style"], C["chain"], C["ours"]], alpha=.45, label="B-cubed F1")
    for i, m in enumerate(ms):
        ax.text(i - 0.18, e[m]["ARI"][0] + 0.03, f"{e[m]['ARI'][0]:.2f}", ha="center", fontsize=8, color=INK)
        ax.text(i + 0.18, e[m]["bcubed_F1"][0] + 0.03, f"{e[m]['bcubed_F1'][0]:.2f}", ha="center", fontsize=8, color=MUTED)
    ax.set_xticks(x); ax.set_xticklabels(lb, fontsize=8.5); ax.set_ylim(0, 1.1)
    ax.set_ylabel("score (solid ARI, light B³-F1)"); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig("figures/fig1_linking.png", dpi=200); plt.close(fig)


def e5_scale():
    t = time.time()
    s, names, span, gold, S = prepare(7, n_agents=1200)
    t1 = time.time()
    e = evaluate(constrained_cluster(S, span, theta=THETA), gold)
    R["e5_scale_1200"] = dict(agents=1200, names=len(names), messages=len(s.board), sim_and_features_s=round(t1 - t, 1),
                              linking_s=round(time.time() - t1, 1), **rnd(e))


if __name__ == "__main__":
    import os
    os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)
    steps = [tune, e1_linking, fig1_linking, e3_coordinators, e4_witness, e2_robustness]
    if "--scale" in sys.argv:
        steps = [e5_scale]
    for f in steps:
        t = time.time(); f(); print(f.__name__, f"{time.time()-t:.1f}s", flush=True)
    path = "results/results_scale.json" if "--scale" in sys.argv else "results/results.json"
    json.dump(R, open(path, "w"), indent=1, default=str)
    print(json.dumps(R, indent=1, default=str)[:6000])
