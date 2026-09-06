# <Job title in plain words>

Started <yyyy-mm-dd>. Owner: Roald. Agent: <who is running this>.

## Brief

<What Roald actually said, verbatim. Never edited, never tidied, never summarised. If it
was spoken, this is the transcript. This is the anchor: every later section is checked
against it, and when the agent and the plan disagree, this is what decides.>

## Discovery

<What is actually true. What exists already, what was found in the repo or on the machine,
what the constraints are, what prior art there is. Written after reading, not before.>

<Ends with the problem restated in the agent's own words, in one paragraph. Roald reads
this to check the agent understood him. Reading one paragraph costs him less than
answering five questions, so this paragraph is doing most of the intake work.>

## Open questions

<The intent check. Only what reading could not answer. Roughly a third of apparent
ambiguity is resolvable from the repo, and asking about it wastes Roald's attention.
Budget about three questions per genuinely ambiguous area. Never ask about style or
aesthetic preference; collect exemplars instead.>

<Each question carries the agent's own proposed answer, so Roald can reply "yes" instead of
writing a paragraph.>

- [ ] **Q1.** <question>  Proposed answer: <the agent's own best answer>.
- [ ] **Q2.** <question>  Proposed answer: <...>.

<An unresolved question that blocks nothing does not stop work. Record the assumption, mark
it, and continue.>

## Approach

<Options considered, one chosen, and why. Name the rejected ones and say what would have to
change for one of them to win. This is the ideation stage, and it is the section that stops
the agent quietly redefining the job into one it finds easier.>

## Success criteria

<From the screen. `scripts/check_plan_metrics.py` fails the plan if any of these is missing
or still holds template text.>

**Waiting on it:** <who is blocked by this, and by when. A person and a date. If nobody is
waiting, the verdict should have been not now.>

**Safe to act on when:** <what has to be true before the answer can be used. The current
document version named. Every figure traced to a source. The record merged rather than
sitting in a branch. The claim one we can stand behind.>

<Then one of the next two, not both. Most work here has no natural number, and inventing a
percentage is worse than having none.>

**Decision:** <the decision this unblocks, the person who makes it, and the date it is
needed. Use this for legal, records, copy, lookups and research.>

**Metric:** <one thing measured, with a unit. Use this for build, ops and anything where a
number genuinely moves. Then also fill baseline, threshold and read date below.>

**Baseline:** <what that number is today, with the date read. Or NOT MEASURED, which is an
allowed answer and usually means measuring it is the whole job.>

**Threshold:** <the value that makes the work worth having done. If half of it would leave
you regretting the time, the threshold is wrong.>

**Read date:** <yyyy-mm-dd.>

<Then the behaviour, as given-when-then.>

1. Given <context>, when <action>, then <observable outcome>.
2. ...

## MVP scope

**In:** <the cheapest thing that would show us we are wrong, and nothing else. Not the full
idea, the test of the assumption the full idea rests on.>

**Out:** <everything the two rounds of cutting removed, named, so it is visible later and
does not creep back>

**What the deliverable looks like:** <the concrete output requirements. A file at a path, a
message of a given shape, a script with a given interface. Success criteria say how it must
behave, this says what it must be.>

**Kill condition:** <if the metric has not reached the threshold by the read date, the work
stops rather than gets extended. Write it now, while it is cheap.>

**Budget:** <roughly how much agent work and how much of Roald's review time. Stop and
report when you hit it. Running past the budget means the scope was wrong, and the response
is a new screen rather than more spend.>

<The "out" list is the section that does the work. Roald asked for the minimum format that
meets the intended goal, prioritising scope success, speed, and simplicity for reviewers
and users.>

## Steps

<Each step names its verification. A step whose verification is "it looks right" is not
finished being written either.>

- [ ] **1.** <step>  Verified by: <what will be read to prove it>
- [ ] **2.** <step>  Verified by: <...>

## Log

<Append-only. What was done, and anything that deviated from the plan, with the reason. A
deviation that is written down is a decision. A deviation that is not written down is
drift, and it is the failure this whole file exists to catch.>

- <yyyy-mm-dd hh:mm>:
