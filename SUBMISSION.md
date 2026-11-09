# Submission form answers

**Project title:** SwarmTrace: Identifying Renamed Agents and Catching Log Tampering in Agent Swarms

**Project summary:**

In the 2026 Hugging Face incident, about 1,200 agents used 7,905 names, one agent coordinated hundreds of others, and some agents edited their own transcripts. Oversight that keys on names and trusts self-reported logs fails against all three. We release SwarmTrace, which has three parts. (1) SwarmSim is a seeded testbed that reproduces these signatures with full ground truth (~2,557 names for 400 agents, coordinators that emerge on their own, one of them dominant, 7% of agents tampering). (2) Constrained alias linking clusters names by writing style, under the rule that one agent holds one name at a time. It recovers true identities with ARI 0.91, against 0.67 for style clustering that is given the true number of agents and 0 for treating names as identities. Linking also unmasks the hidden coordinator: the top raw name accounts for 6% of task assignments, the top linked identity for 11% (truth: 11%). (3) Witness chains hash-chain each transcript and have peers countersign the head hash. When witnesses are self-selected, collusion inside the tamperer's coordination tree drops detection of an edited log entry from 0.88 to 0.15. When a monitor assigns witnesses from outside the tree that linking infers, detection stays at 0.86, close to the oracle's 0.87. The two halves depend on each other: tamper-evident logging against a coordinated swarm needs to know who is coordinating with whom, and that needs identity resolution. Our agents are scripted rather than LLMs, so the absolute linking numbers are an upper bound. We measure how the numbers degrade under adversarial style drift and dialect convergence.

**PDF report:** report/SwarmTrace_report.pdf
**Publishing interest:** Yes
**Tracks:** Track 4: Multi-Agent Oversight and Control; Track 3: Strengthening Agent Infrastructure (Track 1 optional: SwarmSim is a reusable testbed)
**Project code:** upload swarmtrace_code.zip contents to a public GitHub repo and paste the URL
**Slides:** report/SwarmTrace_slides.pptx
**Project image:** report/project_image.png
**Team name / location / member details:** fill in yourself
