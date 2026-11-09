# SwarmTrace

**Who is behind these 2,600 names, and did they edit their logs?**
Oversight tools for agent swarms that rename themselves and rewrite their own transcripts.
Swarm Alignment Hackathon (Apart Research × AI Alignment Foundation × AE Studio), Nov 2026. Tracks 4 (oversight) and 3 (identity infrastructure).

The repo has three parts:

1. **SwarmSim** (`swarmtrace/sim.py`) is a seeded, rule-based testbed. It reproduces the observable signatures of the 2026 Hugging Face swarm incident: agents find a shared board, one coordinator ends up directing hundreds of others, there are about 6.5 names per agent, and 7% of agents rewrite their own transcripts. Everything is logged with ground truth (true identity, true roles, true tampering), so oversight tools can be scored against it.
2. **Constrained alias linking** (`swarmtrace/link.py`) recovers which names belong to the same agent. It runs average-linkage clustering on character n-gram style, under the constraint that one agent holds one name at a time: two groups of names whose activity intervals overlap cannot merge.
3. **Witness chains** (`swarmtrace/witness.py`) make transcripts tamper-evident. Each agent hash-chains its transcript, and every post's head hash is countersigned by a witness. The module compares who gets to be the witness: self-selected peers, random peers, peers stratified outside the agent's coordination tree (inferred from linked identities), or a central monitor anchor.

## Reproduce

```bash
pip install numpy scipy scikit-learn matplotlib
python run_experiments.py           # E1–E4 + figures, ~10 min on 4 CPUs
python run_experiments.py --scale   # 1,200-agent incident-scale linking run
python -m swarmtrace.sim            # print a sample of the board
```

Results go to `results/results.json` and figures to `figures/`. All randomness is seeded. The only hyperparameter, the linking threshold θ, was tuned on dev seed 100 and evaluated on seeds 0–4.

## Limitations

The agents are scripted, not LLMs. The stylometric signal comes from a persona model (synonym choice, openers, sign-offs, punctuation, typos), so absolute linking scores are an upper bound for real LLM agents that share one base model. E2 measures how fast linking degrades as agents deliberately change style or converge on a shared dialect. The incident numbers are only used to calibrate the scale of the simulation. No real incident data is used.
