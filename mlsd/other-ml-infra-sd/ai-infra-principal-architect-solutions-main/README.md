# AI Infrastructure Principal Architect — Solutions Repository

<!-- aicg:site-banner -->
> 🎓 Part of the free, open-source **AI Career Curriculum** ecosystem — [Infrastructure](https://github.com/ai-infra-curriculum) · [ML Engineering](https://github.com/ml-engineering-curriculum) · [AI Engineering](https://github.com/ai-engineering-curriculum) · [Governance](https://github.com/ai-governance-curriculum). Live cohorts &amp; team programs: **[ai-infra-curriculum.github.io](https://ai-infra-curriculum.github.io/)**.
<!-- /aicg:site-banner -->

<!-- aicg:sponsor -->
> 💜 **[Sponsor this curriculum](https://github.com/sponsors/AI-Infra-Curriculum)** — sponsorships keep the whole open-source AI Career Curriculum free and moving.
<!-- /aicg:sponsor -->

Reference solutions for [`ai-infra-principal-architect-learning`](https://github.com/ai-infra-curriculum/ai-infra-principal-architect-learning).

This repository is the answer key for an unusual kind of curriculum.
A principal architect operates above the level where solutions look
like code. The deliverables here are **investment theses, coalition
plans, standards positions, and modernization sequences** — written
artifacts a senior leader would defend in an executive review or an
industry working group.

If you came looking for runnable code, see the architect or senior-
architect tracks. This one is deliberately upstream of those.

## What's new — 2026-05-27

Module-level `SOLUTION.md` design-rationale docs for all 5 modules (mod-601 org-wide-architecture, mod-602 industry-standards, mod-603 multi-year-investment, mod-604 stakeholder-coalition, mod-605 tech-debt-modernization). Each doc explains what the strategic deliverables (case study, strategy memo, stakeholder map, roadmap, presentation) should actually look like at the principal-architect level, with common failure modes and the *why* behind the rubric. Audit score: 45 → 55.

## Track Overview

| Track Tier | Level | Repo |
|---|---|---|
| Principal Architect | 6 (industry-shaping) | this repo |
| Senior Architect | 5 (enterprise transformation) | [`ai-infra-senior-architect-solutions`](https://github.com/ai-infra-curriculum/ai-infra-senior-architect-solutions) |
| Architect | 4 (org-wide systems) | [`ai-infra-architect-solutions`](https://github.com/ai-infra-curriculum/ai-infra-architect-solutions) |

## Repository Structure

```
ai-infra-principal-architect-solutions/
├── README.md                    # this file
├── SOLUTION_OVERVIEW.md         # design philosophy across the track
├── SOLUTIONS_INDEX.md           # quick navigation
├── LEARNING_GUIDE.md            # how to read these solutions
├── CURRICULUM.md
├── CONTRIBUTING.md
├── modules/
│   ├── mod-601-org-wide-architecture/
│   ├── mod-602-industry-standards/
│   ├── mod-603-multi-year-investment/
│   ├── mod-604-stakeholder-coalition/
│   └── mod-605-tech-debt-modernization/
├── projects/                    # capstone-level strategic exercises
├── guides/                      # cross-module strategic frameworks
└── resources/
```

## Modules

| Module | Discipline |
|---|---|
| [mod-601-org-wide-architecture](modules/mod-601-org-wide-architecture) | Architecture that survives across business units and through reorganizations. |
| [mod-602-industry-standards](modules/mod-602-industry-standards) | Engaging with — and shaping — standards bodies, open-source consortia, and regulatory dialogue. |
| [mod-603-multi-year-investment](modules/mod-603-multi-year-investment) | Capital-allocation reasoning for technology investments with 3-10 year arcs. |
| [mod-604-stakeholder-coalition](modules/mod-604-stakeholder-coalition) | Building and sustaining the cross-functional coalitions that turn strategy into adoption. |
| [mod-605-tech-debt-modernization](modules/mod-605-tech-debt-modernization) | Sequencing the modernization of legacy systems without crashing the business. |

Each module contains five exercise-level solutions. The shape of a
"solution" here is a strategic position document, a decision rationale,
an influence plan, a failure-mode analysis, or a success-criteria
scorecard — see [`SOLUTION_OVERVIEW.md`](SOLUTION_OVERVIEW.md).

## Cross-Cutting Principles

These are the load-bearing ideas the track returns to repeatedly:

1. **Strategy is what survives stakeholder rotation.** A strategy that
   depends on a specific executive sponsor is not a strategy; it is
   a project. Deliverables are written to outlive the people who
   commissioned them.
2. **Standards engagement is leverage, not vanity.** Influencing
   industry standards (CNCF, MLCommons, NIST AI RMF) shifts the
   playing field for every competitor.
3. **Tech-debt modernization is sequenced by blast radius.** The job
   is not "rip and replace"; it is sequencing — what can change first
   because it fails small, what must change later because it fails
   large.

## How to Read This Repo

- **Aspiring to the role**: read in module order; spend the most time
  in `mod-603` and `mod-604`.
- **Already a principal architect**: skim and steal the templates;
  the value is concentrated in the anti-pattern sections.
- **Executive evaluating "do we need a principal architect?"**: read
  `mod-601` and `mod-603` only. If your org has neither of those
  disciplines staffed elsewhere, you need a principal architect.

See [`LEARNING_GUIDE.md`](LEARNING_GUIDE.md) for a structured reading
plan.

## Prerequisites

- [Senior Architect track](https://github.com/ai-infra-curriculum/ai-infra-senior-architect-learning) (recommended).
- Alternative path: [Principal Engineer track](https://github.com/ai-infra-curriculum/ai-infra-principal-engineer-learning) for technical principals.

## Example Deliverables

The track produces artifacts of this shape:

- Three- to five-year AI infrastructure investment thesis aligned to
  a measurable business strategy.
- Technology evaluation framework adopted as a standard across an
  engineering org.
- Architecture governance model (review boards, ADRs, technical
  standards) for an enterprise.
- Executive-level technical strategy briefings.
- Multi-million-dollar cost-optimization programs.
- Organization-wide technology migrations executed with zero
  business disruption.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). This repo accepts
contributions in the form of additional case studies, alternative
templates, and corrections — but not "runnable code" PRs (wrong
track).

## License

See [`LICENSE`](LICENSE).

---

<!-- aicg:maintained-by -->
Maintained by [VeriSwarm.ai](https://veriswarm.ai)
