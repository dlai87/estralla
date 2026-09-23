# SOLUTION — Exercise 03: Tech-Debt Impact Analysis (Quantum Application)

Reference for the matching learning exercise
[`lessons/mod-310-emerging-tech/exercises/exercise-3.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-3.md).
See also the module-level rationale in [`../SOLUTION.md`](../SOLUTION.md).

## 1. Solution overview

The learning exercise is an applied prompt: pick a quantum-computing
capability (a QPU vendor, a hybrid quantum-classical workflow, a
post-quantum cryptography migration) and treat it as the emerging
technology under consideration. At the architect tier, the concrete
deliverable is the one named in the module SOLUTION as exercise 03:
a **tech-debt impact analysis** — what does this adoption make easier
in two years, what does it make harder, and what is the migration
cost out if the bet is wrong.

A complete submission produces:

1. A **two-year "easier" list** — what capabilities open up if the
   bet lands.
2. A **two-year "harder" list** — what surface area, coupling, or
   operational load the bet adds.
3. A **migration-out cost estimate** — what it takes to unwind the
   adoption if the bet does not land.
4. A **decision recommendation** that weighs (1)–(3) against each
   other.

## 2. Worked answer

### 2a. The "easier" list

The architect names the capabilities that materially change if the
quantum bet lands. For a quantum-classical workload the list might
include: solving a specific optimization or simulation class within a
target budget, or shifting a workflow off classical hardware that is
projected to run out of headroom. Every entry names the workload it
affects — not "we can do quantum things."

For a post-quantum-cryptography migration, "easier" is often "the
organization can honestly claim readiness against a defined threat
model" — not a performance win.

<!-- needs-research: cite the current NIST post-quantum-cryptography standards page and the timeline for algorithm selection once a vetted link is available. -->

### 2b. The "harder" list

Per the module SOLUTION, adoption always adds surface area:

- New vendors, SDKs, and runtimes to maintain compatibility with.
- New failure modes that on-call has to learn.
- New procurement and export-control considerations for specialized
  hardware.
- Talent scarcity — hiring, retention, and knowledge concentration
  risk.

A submission that lists only "easier" without the corresponding
"harder" has not done the impact analysis.

### 2c. Migration-out cost

The module SOLUTION frames migration cost as the load-bearing
question: **what is the cost out if we pick wrong?** For quantum
this is often high because the underlying abstraction (circuits,
hybrid orchestration, cryptographic primitives) leaks into
application code.

The architect estimates migration cost along three axes:

| Axis | What to estimate |
|---|---|
| Code coupling | How many services depend on the quantum-specific SDK / primitives? |
| Data migration | Is state stored in a form that only the emerging stack can read? |
| Operational retraining | How many on-call rotations need to relearn incident response? |

### 2d. Decision recommendation

The recommendation is one of: *adopt*, *pilot* (fold back into
exercise 02), *defer* (revisit next radar cycle), or *decline*. The
recommendation names the deciding factor — usually migration-out
cost weighed against the size of the "easier" wins.

### 2e. Trade-offs the architect should call out

From the module SOLUTION: **conservative architects miss windows;
aggressive ones bet wrong.** The impact analysis is the artifact
that makes that trade-off visible instead of implicit.

## 3. Validation steps

- [ ] "Easier" list is workload-anchored, not capability-anchored.
- [ ] "Harder" list names surface area, operational load, and
      talent / procurement risk.
- [ ] Migration-out cost is broken out along code, data, and
      operational axes.
- [ ] Decision recommendation is one of adopt / pilot / defer /
      decline, with a named deciding factor.
- [ ] Both the "miss the window" and "bet wrong" failure modes are
      acknowledged.

## 4. Rubric

| Criterion (weight) | Excellent | Adequate | Insufficient |
|---|---|---|---|
| Architecture quality (40%) | Easier + harder + migration-out all present; each list tied to concrete workloads and systems. | All three sections present but at least one is generic. | Only "easier" is filled in; adoption reads as a foregone conclusion. |
| Documentation (30%) | Migration-out estimate is broken out per axis; decision cites the deciding factor. | Migration-out estimated as a single number. | Migration-out omitted. |
| Strategic thinking (20%) | "Miss the window vs. bet wrong" is the central frame. | Trade-off mentioned. | Trade-off omitted. |
| Communication (10%) | A leader can read the recommendation, the deciding factor, and the migration-out cost in one page. | Requires reading the whole analysis to extract the recommendation. | No recommendation surfaced. |

## 5. Common mistakes

From the module SOLUTION's "common mistakes graders see":

1. **No follow-through on pilot learnings.** For this exercise, the
   analogue is an impact analysis that ignores what the organization
   has already learned from prior pilots in adjacent emerging tech.
2. Treating the "harder" list as a formality — one line about
   "learning curve" and nothing else.
3. Underestimating migration-out cost because the emerging stack is
   assumed to succeed.
4. Recommending "adopt" without naming the deciding factor, so the
   next architect cannot re-evaluate when facts change.

## 6. References

- Learning exercise: [`lessons/mod-310-emerging-tech/exercises/exercise-3.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-3.md)
- Module-level architect-tier framing: [`../SOLUTION.md`](../SOLUTION.md) §"Tech-debt impact analysis (exercise 03)"
- Companion in this module: [`../exercise-05/SOLUTION.md`](../exercise-05/SOLUTION.md) — the recommendation flows into the multi-year roadmap.

<!-- needs-research: cite the current NIST post-quantum-cryptography standardization page (https://csrc.nist.gov/projects/post-quantum-cryptography) and any authoritative "migration cost out" framing (e.g., published capability-portfolio or option-value analyses) once vetted links are available. -->
