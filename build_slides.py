"""Build report/SwarmTrace_slides.pptx and report/project_image.png from results + figures."""
import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("results/results.json"))
try:
    R.update(json.load(open("results/results_scale.json")))
except FileNotFoundError:
    pass
E1, E3, D = R["e1_linking"], R["e3_coordinators"], R["e4_detection"]
mean = lambda xs: sum(xs) / len(xs)
sh_true = mean([r["share_true"] for r in E3]); sh_raw = mean([r["share_top_raw_name"] for r in E3]); sh_link = mean([r["share_top_linked"] for r in E3])
n_names = mean([d["names"] for d in R["e1_dataset"]])
INK = RGBColor(0x1f, 0x24, 0x30); TEAL = RGBColor(0x0f, 0x76, 0x6e); MUTED = RGBColor(0x6b, 0x72, 0x80)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def slide(title, bullets=(), image=None, img_w=7.2, sub=None):
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12), Inches(1.0)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]; p.text = title; p.font.size = Pt(32); p.font.bold = True; p.font.color.rgb = INK
    if sub:
        q = tb.add_paragraph(); q.text = sub; q.font.size = Pt(16); q.font.color.rgb = MUTED
    left_w = 12 if image is None else 12.2 - img_w - 0.3
    if bullets:
        bt = s.shapes.add_textbox(Inches(0.6), Inches(1.7), Inches(left_w), Inches(5.3)).text_frame
        bt.word_wrap = True
        for i, b in enumerate(bullets):
            p = bt.paragraphs[0] if i == 0 else bt.add_paragraph()
            p.text = b; p.font.size = Pt(18); p.font.color.rgb = INK; p.space_after = Pt(12)
    if image:
        s.shapes.add_picture(image, Inches(13.333 - img_w - 0.5), Inches(1.8), width=Inches(img_w))
    return s


slide("SwarmTrace", [
    "Problem: in the 2026 incident, ~1,200 agents used 7,905 names, one agent directed hundreds of others, "
    "and some agents edited their own transcripts.",
    "Oversight that treats names as identities and trusts self-reported logs fails against all three.",
    "We built a testbed with ground truth, a linker that recovers identities, and a witness protocol that resists collusion.",
    "Track 4 (Oversight & Control), with Track 3 (Agent Infrastructure)."],
    sub="Identifying renamed agents and catching log tampering in agent swarms")
slide("SwarmSim: a testbed with ground truth", [
    f"400 agents with scripted personas, a shared board, and 240 steps. Each run takes under a second.",
    f"Calibrated to the incident: ~{n_names:,.0f} names (≈6.5 per agent), one dominant coordinator via preferential attachment, 7% tamperers.",
    "Adversarial knobs: style drift on rename and dialect conformity.",
    "Logs everything: board messages, renames, private tool calls, and the hidden identities and roles."])
slide("Constrained alias linking", [
    "Insight: an agent holds one name at a time, so the activity intervals of its names never overlap.",
    "Character n-gram stylometry + average-linkage clustering, with merges allowed only when intervals don't overlap.",
    f"ARI {E1['ours_CAL']['ARI'][0]:.2f}, against {E1['style_oracleK']['ARI'][0]:.2f} for style-only clustering given the true #agents, and 0 for names as identities.",
    (f"At incident scale (1,200 agents, {R['e5_scale_1200']['names']:,} names): ARI {R['e5_scale_1200']['ARI']:.2f}." if "e5_scale_1200" in R else "")],
    image="figures/fig1_linking.png", img_w=6.4)
slide("Renaming hides the coordinator; linking reveals it", [
    f"The true top coordinator issued {sh_true*100:.0f}% of all task assignments.",
    f"Looking at raw names, the most active name accounts for only {sh_raw*100:.0f}%.",
    f"After linking, the top identity accounts for {sh_link*100:.0f}%.",
    "A per-name monitor would see a crowd of small actors and miss the one agent directing them."],
    image="figures/fig3_coordinator.png", img_w=6.6)
slide("Witness chains: tamper-evident transcripts", [
    "Each transcript is a hash chain. On every post, a peer countersigns the current head hash.",
    "Editing an entry breaks every later witnessed head, so any honest, audited witness catches the edit.",
    f"Self-selected witnesses fail when the agent's team colludes: detection falls from {D['self']['0.0']:.2f} to {D['self']['1.0']:.2f}.",
    f"With monitor-assigned witnesses from outside the coordination tree inferred from linked identities, detection is {D['strat_link']['1.0']:.2f} "
    f"(oracle {D['strat_oracle']['1.0']:.2f}; raw names {D['strat_raw']['1.0']:.2f})."],
    image="figures/fig4_witness.png", img_w=7.0)
slide("Limits and next steps", [
    "Agents are scripted, so the linking numbers are an upper bound for LLM agents that share one base model.",
    "Adversarial style drift is the linker's weak point (see report Fig. 4). Mitigation: put unlinked new identities on higher audit and stratified witnesses, so renaming costs something.",
    "Swarm-wide collusion defeats any peer-based scheme. Combine rare central anchors with stratified peer witnessing.",
    "Next: run small LLM agents in SwarmSim, and apply the linker to the Swarm Traces and AI Village logs."],
    image="figures/fig2_robustness.png", img_w=6.2)
prs.save("report/SwarmTrace_slides.pptx")

# project image: 3-panel hero
fig = plt.figure(figsize=(12, 6.3), facecolor="#0f1720")
fig.text(0.04, 0.88, "SwarmTrace", color="white", fontsize=40, weight="bold", family="DejaVu Sans")
fig.text(0.04, 0.80, "Identifying renamed agents and catching log tampering in agent swarms", color="#9fb3c8", fontsize=17)
stats = [(f"{E1['ours_CAL']['ARI'][0]:.2f}", "ARI recovering true agents\nfrom ~6.5 names each"),
         (f"{sh_raw*100:.0f}% → {sh_link*100:.0f}%", "hidden coordinator's share of\nassignments, raw names → linked"),
         (f"{D['self']['1.0']:.2f} → {D['strat_link']['1.0']:.2f}", "tamper detection under full\ncollusion, self → stratified witnesses")]
for i, (big, small) in enumerate(stats):
    x = 0.04 + i * 0.32
    fig.text(x, 0.45, big, color="#5eead4", fontsize=38, weight="bold")
    fig.text(x, 0.28, small, color="#d1dae3", fontsize=14, va="top")
fig.text(0.04, 0.06, "Swarm Alignment Hackathon 2026 · Track 4 Oversight & Control + Track 3 Agent Infrastructure", color="#6b7f93", fontsize=12)
fig.savefig("report/project_image.png", dpi=150, facecolor=fig.get_facecolor())
print("slides + image done")
