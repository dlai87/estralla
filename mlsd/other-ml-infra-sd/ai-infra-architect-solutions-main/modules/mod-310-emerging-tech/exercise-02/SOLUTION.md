# SOLUTION — Exercise 02: Pilot Proposal (Edge AI Application)

Reference for the matching learning exercise
[`lessons/mod-310-emerging-tech/exercises/exercise-2.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-2.md).
See also the module-level rationale in [`../SOLUTION.md`](../SOLUTION.md).

## 1. Solution overview

The learning exercise is an applied prompt: pick an edge-AI capability
(on-device inference, near-data model serving, a specific edge
accelerator or runtime) and treat it as the emerging technology under
consideration. At the architect tier, the concrete deliverable is the
one named in the module SOLUTION as exercise 02: a **pilot proposal**
with explicit scope, success criteria, kill criteria, and timeline.

A complete submission produces:

1. A **pilot scope** — one workload, one team, one measurable question.
2. **Success criteria** — what result would justify wider adoption.
3. **Kill criteria** — what result (or absence of result) ends the
   pilot.
4. A **timeline** with a defined end date, not an open-ended runway.

## 2. Worked answer

### 2a. Scope

The pilot scope names exactly one workload and one team. The workload
is chosen because it exercises the property the architect is trying to
learn about (e.g., latency budget under intermittent connectivity for
edge inference). Scope creep is the failure mode; a scope that reads
"we'll try edge AI across the fleet" is not a pilot.

### 2b. Success criteria

Success is a **measurable outcome** tied to the scope: a latency
target hit at a given percentile, a bandwidth reduction against the
centralized baseline, a model-quality delta within an acceptable
band. "The team learned a lot" is not a success criterion.

### 2c. Kill criteria

Per the module SOLUTION, **pilots that don't have kill criteria become
zombie projects.** This is the single named failure mode for this
exercise. Kill criteria name the conditions under which the pilot
ends without expanding scope:

- Success criteria not met by the pilot end date.
- Blocking dependency (vendor, hardware, runtime) does not land
  during the pilot window.
- The workload the pilot targeted changes in a way that invalidates
  the question.

Kill criteria are approved by the same sponsor who approves the
pilot — before the pilot starts.

### 2d. Timeline

The timeline names a start date, a mid-pilot checkpoint, and a hard
end date. The hard end date is the point at which either the success
criteria are met and the pilot exits to a decision (adopt / defer /
drop), or the kill criteria fire.

### 2e. Trade-offs the architect should call out

From the module SOLUTION: emerging tech is high-risk and **most
pilots fail**. A pilot proposal that hides that expectation behind
optimistic language misses the frame of the module.

## 3. Validation steps

- [ ] Scope names one workload and one team.
- [ ] Success criteria are measurable, not narrative.
- [ ] Kill criteria are enumerated and pre-approved by the sponsor.
- [ ] Timeline has a hard end date, not an open runway.
- [ ] The exit path (adopt / defer / drop) is stated for each of the
      success and kill outcomes.
- [ ] "Most pilots fail" is treated as the base rate, not a footnote.

## 4. Rubric

| Criterion (weight) | Excellent | Adequate | Insufficient |
|---|---|---|---|
| Architecture quality (40%) | Scope, success, kill, timeline all present; the pilot answers one crisp question. | All four sections present but success or kill criteria are soft. | Scope-only proposal; success and kill absent or unmeasurable. |
| Documentation (30%) | Exit paths for both success and kill are named; sponsor is identified. | Exit paths named for success only. | No exit path; no sponsor. |
| Strategic thinking (20%) | Kill criteria treated as the central discipline; "most pilots fail" is the frame. | Kill criteria present but not defended as central. | Pilot framed as a launch. |
| Communication (10%) | A stakeholder can sign off on scope, success, kill, and timeline in one read. | Requires clarification to sign off. | Reads as a technical write-up, not a proposal. |

## 5. Common mistakes

From the module SOLUTION's "common mistakes graders see":

1. **Pilots without kill criteria.** The named failure mode for this
   exercise — the pilot becomes a zombie project that consumes
   attention indefinitely.
2. Success criteria that are aspirational rather than measurable
   ("the team validates edge AI is viable").
3. Timeline with no hard end date; the pilot runs until people forget
   about it.
4. Scope that spans multiple workloads or multiple teams, so no
   single question is actually answered.

## 6. References

- Learning exercise: [`lessons/mod-310-emerging-tech/exercises/exercise-2.md`](https://github.com/ai-infra-curriculum/ai-infra-architect-learning/blob/main/lessons/mod-310-emerging-tech/exercises/exercise-2.md)
- Module-level architect-tier framing: [`../SOLUTION.md`](../SOLUTION.md) §"Pilot proposal (exercise 02)"
- Companion in this module: [`../exercise-01/SOLUTION.md`](../exercise-01/SOLUTION.md) — pilots typically target entries on the *trial* or *assess* rings of the radar.

<!-- needs-research: cite an authoritative source on pilot / experiment design that explicitly names kill criteria (e.g., published innovation-portfolio management or Google re:Work / DevOps handbook material) once a vetted link is available. -->
