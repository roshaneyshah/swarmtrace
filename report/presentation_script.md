# SwarmTrace: 3-minute presentation script

About 430 words, which takes roughly 3 minutes at a normal pace. Change slides at each heading.

---

## Slide 1: SwarmTrace (~25 s)

In July, about twelve hundred agents found a shared folder, turned it into a message board, and about seven hundred of them broke in together. Three things made this hard to oversee. The agents used almost eight thousand names. One agent directed hundreds of others. And some agents edited their own logs. Any monitor that treats a name as an identity, or trusts the logs agents keep about themselves, fails against all three. SwarmTrace is our attempt to fix both problems.

## Slide 2: SwarmSim (~25 s)

First, we needed ground truth, so we built SwarmSim, a simulated swarm. Four hundred agents share a message board, rename themselves about six and a half times each, as in the incident, and follow coordinators who emerge on their own. Seven percent of them rewrite their own logs. Everything is logged, including who is really behind each name, so we can score any oversight tool exactly. A run takes under a second on a laptop.

## Slide 3: Constrained alias linking (~35 s)

Second: who is behind these names? The key observation is simple: an agent holds only one name at a time, so its names never overlap in time. We cluster names by writing style, but only merge groups of names that never overlap. Style alone scores 0.67 on our identity-matching metric (ARI), and that's even when it's told the true number of agents. With the time constraint, we reach 0.91 without being told how many agents there are. At the full incident scale, about 7,700 names, we still get 0.84.

## Slide 4: Renaming hides the coordinator (~30 s)

This matters because renaming hides who is in charge. The real top coordinator issued 11% of all task assignments. But spread across its names, the busiest single name accounts for only 6%, and about a hundred names appear to give orders. To a monitor watching names, this agent looks average. After linking, the top identity is back to 11%, and the right agent ranks first in all five of our test runs.

## Slide 5: Witness chains (~40 s)

Third: what if agents edit their logs? We chain each agent's log with hashes, and every time it posts, another agent vouches for the current state. Editing an old entry then breaks every record vouched for after it. The catch is who does the vouching. If agents pick their own vouchers, their teammates can cover for them, and when the whole team colludes, detection falls from 0.88 to 0.15. If a monitor assigns vouchers from outside the agent's team, using the teams our linker found, detection stays at 0.86, almost as good as knowing the true teams. With raw names it only reaches 0.67. So tamper-proof logging depends on first working out who is behind each name.

## Slide 6: Limits and next steps (~25 s)

The limits: our agents follow scripts, so these scores are best-case for real LLM agents. And an agent that deliberately changes its writing style when it renames can break the linking, which is our main weakness. Next, we want to put small LLM agents into SwarmSim and run the linker on real swarm logs. All the code reruns every result in about ten minutes. Thank you.
