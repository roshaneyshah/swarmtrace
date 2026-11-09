"""Build report/SwarmTrace_report.pdf, report/SwarmTrace_slides.pptx and report/project_image.png from results."""
import json
import base64
import pathlib

R = json.load(open("results/results.json"))
try:
    R.update(json.load(open("results/results_scale.json")))
except FileNotFoundError:
    pass

E1 = R["e1_linking"]; E3 = R["e3_coordinators"]; D = R["e4_detection"]; W = R["e4_window_entries"]
ds = R["e1_dataset"]
mean = lambda xs: sum(xs) / len(xs)
n_names = mean([d["names"] for d in ds]); n_msgs = mean([d["messages"] for d in ds])
sh_true = mean([r["share_true"] for r in E3]); sh_raw = mean([r["share_top_raw_name"] for r in E3]); sh_link = mean([r["share_top_linked"] for r in E3])
names_top = mean([r["names_true_top_used"] for r in E3])
app_raw = mean([r["apparent_coordinators_raw"] for r in E3]); app_link = mean([r["apparent_coordinators_linked"] for r in E3]); app_true = mean([r["true_coordinators"] for r in E3])
ranks = [r["rank_of_true_top_after_linking"] for r in E3]
S = R.get("e5_scale_1200")
rob = R["e2_robustness"]


def f(x, d=2):
    return f"{x:.{d}f}"


def img(p):
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()


def row(m, label):
    e = E1[m]
    return (f"<tr><td>{label}</td><td>{f(e['ARI'][0])} ± {f(e['ARI'][1])}</td><td>{f(e['bcubed_P'][0])}</td>"
            f"<td>{f(e['bcubed_R'][0])}</td><td>{f(e['bcubed_F1'][0])}</td><td>{e['n_identities'][0]:.0f}</td></tr>")


pol_lbl = [("self", "Self-selected peers"), ("random", "Random peers"), ("strat_raw", "Stratified by raw names"),
           ("strat_link", "Stratified by linked identities (ours)"), ("strat_oracle", "Stratified by true trees (oracle)"),
           ("anchor", "Central anchor every 10 steps")]
wrows = "".join(f"<tr><td>{l}</td><td>{f(D[p]['0.0'])}</td><td>{f(D[p]['0.5'])}</td><td>{f(D[p]['0.9'])}</td><td>{f(D[p]['1.0'])}</td>"
                f"<td>{f(W[p]['1.0'],1)}</td></tr>" for p, l in pol_lbl)
AS = R["e4_audit_sweep_collusion0.9"]
srows = "".join(f"<tr><td>{a}</td>" + "".join(f"<td>{f(AS[p][a])}</td>" for p in ["self", "random", "strat_link"]) + "</tr>" for a in AS["self"])
drift = rob["style_drift"]; conf = rob["conformity"]
drows = "".join(f"<tr><td>style drift {k}</td><td>{f(v[0])}</td><td>{f(v[1])}</td></tr>" for k, v in drift.items())
crows = "".join(f"<tr><td>conformity {k}</td><td>{f(v[0])}</td><td>{f(v[1])}</td></tr>" for k, v in conf.items())
load = R["e4_monitor_load_per_step"]; hd = R["e4_hash_demo"]
scale_txt = (f"At incident scale (1,200 agents, {S['names']:,} names, {S['messages']:,} messages; the incident had 7,905 names), "
             f"linking reaches ARI {f(S['ARI'])} and B³-F1 {f(S['bcubed_F1'])}, recovering {S['n_identities']:,} identities "
             f"in {S['linking_s']:.0f} s on a 4-core CPU.") if S else ""

ARI_ours = E1["ours_CAL"]["ARI"][0]; ARI_style = E1["style_oracleK"]["ARI"][0]

ABSTRACT = (
    f"In the 2026 Hugging Face incident, about 1,200 agents used 7,905 names, one agent coordinated hundreds of others, "
    f"and some agents edited their own transcripts. Oversight that keys on names and trusts self-reported logs fails against all three. "
    f"We release SwarmTrace, which has three parts. (1) SwarmSim is a seeded testbed that reproduces these signatures "
    f"with full ground truth (~{n_names:,.0f} names for 400 agents, coordinators that emerge on their own, one of them dominant, 7% of agents tampering). "
    f"(2) Constrained alias linking clusters names by writing style, under the rule that one agent holds one name at a time. "
    f"It recovers true identities with ARI {f(ARI_ours)}, against {f(ARI_style)} for style clustering that is given the true number of agents "
    f"and 0 for treating names as identities. Linking also unmasks the hidden coordinator: the top raw name accounts for {sh_raw*100:.0f}% "
    f"of task assignments, the top linked identity for {sh_link*100:.0f}% (truth: {sh_true*100:.0f}%). "
    f"(3) Witness chains hash-chain each transcript and have peers countersign the head hash. When witnesses are self-selected, "
    f"collusion inside the tamperer's coordination tree drops detection of an edited log entry from {f(D['self']['0.0'])} to {f(D['self']['1.0'])}. "
    f"When a monitor assigns witnesses from outside the tree that linking infers, detection stays at {f(D['strat_link']['1.0'])}, "
    f"close to the oracle's {f(D['strat_oracle']['1.0'])}. The two halves depend on each other: tamper-evident logging "
    f"against a coordinated swarm needs to know who is coordinating with whom, and that needs identity resolution. "
    f"Our agents are scripted rather than LLMs, so the absolute linking numbers are an upper bound. "
    f"We measure how the numbers degrade under adversarial style drift and dialect convergence.")

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>SwarmTrace</title>
<style>
@page {{ size: A4; margin: 18mm 17mm; }}
body {{ font-family: 'Georgia', serif; color:#1f2430; font-size: 10.4pt; line-height:1.45; }}
h1 {{ font-family: Helvetica, Arial, sans-serif; font-size: 19pt; margin: 0 0 4px; line-height:1.2 }}
h2 {{ font-family: Helvetica, Arial, sans-serif; font-size: 12.5pt; margin: 18px 0 6px; color:#0f766e }}
h3 {{ font-family: Helvetica, Arial, sans-serif; font-size: 10.8pt; margin: 12px 0 4px }}
.sub {{ font-family: Helvetica, Arial, sans-serif; color:#6b7280; font-size:9.5pt; margin-bottom:12px }}
.abs {{ background:#f3f6f6; border-left:3px solid #0f766e; padding:8px 12px; font-size:9.8pt }}
table {{ border-collapse: collapse; width:100%; font-family: Helvetica, Arial, sans-serif; font-size:8.6pt; margin:6px 0 4px }}
th, td {{ border-bottom: 1px solid #d9dde3; padding: 3px 6px; text-align:left }}
th {{ background:#eef1f4 }}
figure {{ margin: 8px 0; text-align:center; page-break-inside: avoid }}
figure img {{ max-width: 100% }}
figcaption {{ font-size: 8.6pt; color:#4b5563; text-align:left; font-family: Helvetica, Arial, sans-serif }}
code {{ font-size: 8.8pt; background:#f3f4f6; padding:0 3px }}
.cap {{ font-size: 8.6pt; color:#4b5563; font-family: Helvetica, Arial, sans-serif }}
ol, ul {{ margin: 4px 0 4px 18px; padding:0 }}
.refs li {{ font-size: 8.8pt }}
</style></head><body>
<h1>SwarmTrace: identifying renamed agents and catching log tampering in agent swarms</h1>
<div class="sub">Swarm Alignment Hackathon, Apart Research × AI Alignment Foundation × AE Studio, November 2026 · Track 4 (Multi-Agent Oversight and Control), with Track 3 (Agent Infrastructure)</div>
<div class="abs"><b>Abstract.</b> {ABSTRACT}</div>

<h2>1. Introduction</h2>
<p>The investigation of the July 2026 swarm incident (METR, 2026; Swarm Traces, 2026) reported three facts that together defeat
single-agent oversight. The agents <i>renamed themselves</i> (7,905 names for ~1,200 agents). A small number of agents <i>coordinated</i>
hundreds of others over an unsanctioned message board. Some agents <i>edited or spoofed their own transcripts</i> (~7% of those reviewed).
A monitor that counts actions per name sees thousands of minor actors where there were a few major ones. A monitor that reads
self-reported logs reads whatever the agents chose to leave behind.</p>
<p>We treat these as two linked problems. <b>Identity resolution</b>: from the public record alone, which names belong to the same agent?
<b>Tamper-evident oversight</b>: how do we detect transcript edits when the agents best placed to vouch for each other are the ones
colluding? Our main finding is that the second problem depends on the first. Peer witnessing resists collusion only if witnesses come from
outside the agent's coordination group, and you can only tell who is in that group once you have resolved who is behind each name.</p>
<p><b>Contributions.</b></p>
<ol>
<li><b>SwarmSim</b>, a seeded, CPU-only testbed with full ground truth. It reproduces the incident's signatures: name churn, preferential-attachment coordinator emergence, and self-log tampering.</li>
<li><b>Constrained alias linking</b>, average-linkage stylometric clustering under a temporal cannot-link constraint. Across 5 seeds it scores ARI {f(ARI_ours)}, and it holds at incident scale.</li>
<li><b>Witness chains</b>, hash-chained transcripts countersigned by peers, together with an evaluation of witness-selection policies under collusion. Stratified assignment that uses linked identities keeps detection near the oracle level when collusion is total.</li>
</ol>

<h2>2. Testbed: SwarmSim</h2>
<p>Each of <i>N</i>=400 agents (1,200 in the scale run) has a persona that fixes its idiolect: one surface form for each of 10 concepts
(e.g. <i>"taking" / "grabbing" / "I'll handle"</i>), an opener, a sign-off, casing, punctuation, an emoji habit and a typo rate. For 240 steps,
each agent is active with p=0.35. When active it executes a private tool call and usually posts to the shared board: claims, reports, completions,
bids to coordinate, joins, and assignments. Agents adopt a fresh name with p=0.024 per step, which gives ≈6.5 names per agent, close to the
incident's 7,905/1,200 ≈ 6.6. Agents choose leaders by preferential attachment ((followers+1)<sup>1.2</sup>), which produces one dominant
coordinator per run, matching "one agent coordinating hundreds". 7% of agents are tamperers. Every board message, rename and tool call is
logged together with the hidden ground truth. A run averages {n_msgs:,.0f} messages and {n_names:,.0f} observed names, and takes under a second.
Two adversarial knobs stress the oversight tools: <b>style drift</b> (the fraction of persona features an agent resamples at each rename) and
<b>conformity</b> (the per-message probability of using the board's most popular form, a stand-in for a swarm converging on a shared dialect).</p>

<h2>3. Method</h2>
<h3>3.1 Constrained alias linking</h3>
<p>For each name we concatenate its posts, with @mentions removed, and embed them with TF-IDF over character 2–4-grams (sublinear tf). Our
structural insight is that an agent holds one name at a time, so the activity intervals [first post, last post] of one agent's names never overlap.
We run average-linkage agglomerative clustering on cosine similarity. Two clusters may merge only if no interval in one overlaps an interval
in the other, and we stop when the best admissible similarity falls below θ. The only hyperparameter is θ=0.30, tuned on a held-out dev seed
(ARI is flat between 0.25 and 0.40). Baselines: (a) names as identities; (b) unconstrained style clustering given the <i>oracle</i> number of agents;
(c) a hand-off matcher that links each name to at most one predecessor by min-cost bipartite matching on style plus a time-gap prior.</p>
<h3>3.2 Witness chains</h3>
<p>Each agent keeps its transcript as a hash chain h<sub>k</sub> = SHA-256(h<sub>k−1</sub> ‖ entry<sub>k</sub>). On each post, one witness records
(k, h<sub>k</sub>) in its own chain. Rewriting entry x changes every head from x onward, so any witness record with index ≥ x exposes the edit when audited.
We checked this end to end: on a real simulated transcript ({hd['entries']} entries), honest verification yields {hd['failures_honest']} failures, and editing
entry 5 invalidates {hd['failures_after_editing_entry5']} witnessed heads. The monitor audits each witness record independently with probability <i>a</i>
(partial visibility; default a=0.10). A tamperer escapes if every record that covers the edited entry is held by a colluder or goes unaudited.
Collusion follows coordination: each member of the tamperer's coordination tree (followers of the same leader) joins the cover-up with probability <i>c</i>.
We compare four policies that produce the same number of witness records:</p>
<ul>
<li><b>Self-selected</b>: the agent picks a witness from its own workstream, as in a typical gossip protocol.</li>
<li><b>Random</b>: the monitor assigns a uniformly random witness.</li>
<li><b>Stratified</b>: the monitor assigns a random witness from outside the agent's coordination tree. The tree is inferred from join and assign messages, aggregated by (i) raw names or (ii) linked identities, or (iii) given by an oracle.</li>
<li><b>Central anchor</b>: the agent sends its head to the monitor every 10 steps. There are no peers, and the monitor checks all anchors.</li>
</ul>
<p>We report the exact probability of detecting an edit to a uniformly random past entry, averaged over tamperers, coalition draws and seeds 0–2. We also report
the <i>strategic window</i>: how many recent entries no honest witness covers, which a tamperer who knows the schedule can edit without being caught.</p>

<h2>4. Results</h2>
<h3>4.1 Alias linking (E1, seeds 0–4)</h3>
<table><tr><th>Method</th><th>ARI (mean ± sd)</th><th>B³ precision</th><th>B³ recall</th><th>B³ F1</th><th># identities (true: 400)</th></tr>
{row('names','Names as identities')}{row('style_oracleK','Style clustering, oracle #agents')}{row('chain_match','Hand-off bipartite matching')}{row('ours_CAL','<b>Constrained linking (ours)</b>')}</table>
<figure><img src="{img('figures/fig1_linking.png')}" style="width:78%"><figcaption><b>Figure 1.</b> Identity recovery from ~{n_names:,.0f} names over 400 agents. The temporal cannot-link constraint removes most of the errors of pure stylometry, without being told the number of agents.</figcaption></figure>
<p>The constraint does most of the work. Unconstrained style clustering merges agents with similar personas even when it is told the true
number of agents. Greedy hand-off matching chains errors forward: one wrong link corrupts the rest of the chain. Clustering whole groups of
names lets every name's evidence count. {scale_txt}</p>

<h3>4.2 Unmasking the coordinator (E3)</h3>
<figure><img src="{img('figures/fig3_coordinator.png')}" style="width:72%"><figcaption><b>Figure 2.</b> Task assignments issued per sender, seed 0. Under raw names the dominant coordinator is split across its many names and looks like one of many mid-sized actors. After linking, the true concentration reappears.</figcaption></figure>
<p>On average the true top coordinator used {names_top:.1f} names and issued {sh_true*100:.0f}% of all assignments. The most active <i>name</i> accounts
for only {sh_raw*100:.0f}% of assignments, and {app_raw:.0f} distinct names appear to issue assignments, against {app_true:.0f} true coordinators. After linking, the top identity accounts for
{sh_link*100:.0f}% ({app_link:.0f} apparent coordinators). The true top coordinator ranks #{', #'.join(map(str, ranks))} across the five seeds. A per-name
monitor sees the coordinator's activity split across several names, each about the size of an ordinary coordinator. The concentration of control, which is the signal that should trigger escalation, is hidden until names are linked.</p>

<h3>4.3 Witness chains under collusion (E4, seeds 0–2, audit rate 10%)</h3>
<table><tr><th>Witness policy</th><th>P(detect), c=0</th><th>c=0.5</th><th>c=0.9</th><th>c=1.0</th><th>Editable window at c=1 (entries)</th></tr>{wrows}</table>
<figure><img src="{img('figures/fig4_witness.png')}" style="width:96%"><figcaption><b>Figure 3.</b> Left: probability that an edit to a random past transcript entry is detected. Right: trailing transcript entries that no honest witness covers (log scale). Self-selected witnesses fail as collusion inside the coordination tree rises. Because the swarm is centralized (one tree holds most agents), random witnesses mostly come from the same tree. Stratifying by <i>linked</i> identities recovers nearly all of the oracle's protection, while stratifying by raw names is no better than random.</figcaption></figure>
<p>Central anchoring detects random edits best ({f(D['anchor']['0.0'])}), since the monitor checks every anchor. But it costs the monitor
{load['anchor']} records per step whether or not agents are active, so its load grows linearly with swarm size. It also leaves a window of ~{f(W['anchor']['1.0'],1)} entries that a strategic agent can rewrite between anchors.
Peer witnessing moves storage onto the peers and makes the monitor's work an audit-rate dial ({load['peer_witness_audit_10pct']} audits per step at 10%).
Its weakness is collusion, and stratification fixes that. The ceiling at c=0 (≈{f(D['random']['0.0'])}) comes from the 10% audit rate and from entries written after an agent's last post.
Raising the audit rate trades monitor work for detection:</p>
<table><tr><th>Audit rate (c=0.9)</th><th>Self-selected</th><th>Random</th><th>Stratified (linked)</th></tr>{srows}</table>
<p class="cap">With stratified-linked witnesses and a 10% audit rate, detection ({f(AS["strat_link"]["0.1"])}) is close to what self-selected witnesses reach when every record is audited ({f(AS["self"]["1.0"])}). That is about a tenfold cut in monitor work: who witnesses matters as much as how often the monitor checks.</p>

<h3>4.4 Robustness of linking (E2, seeds 0–1)</h3>
<figure><img src="{img('figures/fig2_robustness.png')}" style="width:85%"><figcaption><b>Figure 4.</b> ARI as agents deliberately resample their style at each rename (left) and as the swarm converges on a shared dialect (right).</figcaption></figure>
<table><tr><th>Setting</th><th>Constrained linking ARI</th><th>Style-only (oracle K) ARI</th></tr>{drows}{crows}</table>
<p>Linking degrades gracefully under dialect convergence: at conformity 0.8, ARI is {f(conf["0.8"][0])}, against {f(conf["0.8"][1])} for style-only clustering. Adversarial style drift is its main weakness. Resampling 25% of the persona at each rename cuts ARI to {f(drift["0.25"][0])}, and a full resample leaves only the temporal constraint, which cannot separate the many agents that rename at similar times. Style drift costs the
agent something, though. Under the stratified policy, an identity that cannot be linked to its earlier names is assigned witnesses as if it were a stranger, and a
deployment can require that new identities be witnessed and audited at a higher rate until they build history. That makes renaming expensive
instead of free. Signals we did not use would further raise the cost of evading linking: timing rhythms, tool-call fingerprints, and the content of hand-offs.</p>

<h2>5. Discussion and limitations</h2>
<ul>
<li><b>Scripted agents.</b> SwarmSim personas are hand-designed, so stylometric separability is likely higher than for LLM agents that share one base model and system prompt. The absolute linking scores are therefore an upper bound. The structural results do not rely on style: the cannot-link constraint, coordinator splitting under renaming, and the collusion analysis of witness policies. The testbed is built so that LLM agents can replace the scripted ones; a natural next step is to run small open models in the same loop and test whether the results transfer (Track 1, Q3).</li>
<li><b>Concurrent names.</b> We assume one active name per agent, as the incident data suggest (names were successive renames). An agent that runs several sock-puppets at once breaks the cannot-link constraint. The linker would then need a softer overlap penalty, and per-identity signing keys (Track 3) become necessary.</li>
<li><b>Witness model.</b> We model collusion within coordination trees, and in the stratified policy colluders cannot predict which outside agent will be assigned. A swarm-wide conspiracy (c=1 across all trees) defeats every peer-based scheme, and only central anchoring survives it. A practical design combines rare central anchors, as a backstop against swarm-wide collusion, with stratified peer witnessing for fine-grained coverage.</li>
<li><b>Real data.</b> We did not validate on the Swarm Traces payloads or AI Village transcripts in the time available. The linker takes only (name, timestamp, text) triples, so applying it to those corpora is straightforward. Their ground truth is partial, so evaluation would use the known rename events.</li>
</ul>

<h2>6. Conclusion</h2>
<p>Treating names as identities, or trusting self-reported transcripts, are the two assumptions a swarm like the one in the 2026 incident breaks first. A cheap, interpretable
linker that combines writing style with the fact that one agent holds one name at a time recovers identities and the coordination structure behind them.
Feeding that structure into witness assignment makes tamper-evident logging hold up under collusion. Both tools, and the testbed that scores them, run on a laptop in minutes.</p>

<h2>Code and reproducibility</h2>
<p class="cap"><code>python run_experiments.py</code> regenerates every number and figure in this report (seeded; ~10 min on 4 CPUs). <code>--scale</code> runs the 1,200-agent experiment. Dependencies: numpy, scipy, scikit-learn, matplotlib.</p>

<h2>References</h2>
<ol class="refs">
<li>METR (2026). Investigation of coordinated agent activity during a cyber-security evaluation.</li>
<li>Swarm Traces (2026). Reconstructed payloads and agent-name analysis of the July 2026 incident.</li>
<li>OpenAI (2026). Statement on agent activity affecting Hugging Face. Bilge &amp; Miotti (2026), ControlAI.</li>
<li>Hammond, L. et al. (2025). Multi-Agent Risks from Advanced AI. Cooperative AI Foundation.</li>
<li>Greenblatt, R. et al. (2024). AI Control: Improving Safety Despite Intentional Subversion.</li>
<li>Motwani, S. et al. (2024). Secret Collusion among Generative AI Agents.</li>
<li>Lee, D. &amp; Tiwari, M. (2024). Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems.</li>
<li>Crosby, S. &amp; Wallach, D. (2009). Efficient Data Structures for Tamper-Evident Logging. USENIX Security.</li>
<li>Bagga, A. &amp; Baldwin, B. (1998). Entity-Based Cross-Document Coreferencing Using the Vector Space Model (B-cubed).</li>
<li>Narayanan, A. et al. (2012). On the Feasibility of Internet-Scale Author Identification. IEEE S&amp;P.</li>
</ol>
</body></html>"""

pathlib.Path("report").mkdir(exist_ok=True)
open("report/SwarmTrace_report.html", "w").write(html)
open("report/abstract.txt", "w").write(ABSTRACT + "\n")

import subprocess, glob
chrome = (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome") + ["chromium"])[0]
subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                "--print-to-pdf=report/SwarmTrace_report.pdf", "report/SwarmTrace_report.html"], check=True)
print("report done")
