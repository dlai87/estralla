# Objective Module Quality Checklist

Use this checklist for generated curriculum updates before opening a PR.

## Structure

- [ ] The solution repo mirrors every paired learning module that is in scope.
- [ ] Every learning exercise has a matching solution directory.
- [ ] Every solution exercise directory contains `SOLUTION.md`.
- [ ] Implementation exercises include runnable or statically valid artifacts
      where feasible.
- [ ] Design exercises include a worked answer and a rubric or review checklist.

## Content Quality

- [ ] The solution answers the stated learning objective.
- [ ] The explanation names assumptions and constraints.
- [ ] The validation steps are executable or explicitly marked as design review.
- [ ] Common mistakes are concrete and tied to the exercise.
- [ ] No placeholder, TODO, `# manual-review`, or `needs-research` markers remain.

## Source Policy

- [ ] Official standards or official project docs back technical claims.
- [ ] Practitioner references are clearly labeled and never used as standards.
- [ ] Unverified facts are removed or marked with `<!-- needs-research: ... -->`.
- [ ] No invented incidents, metrics, benchmarks, or case studies are included.

## Validation

- [ ] `aicg audit --repo <repo>` has been reviewed.
- [ ] `aicg plan --repo <repo>` produces only intended work items.
- [ ] `aicg validate --repo <repo>` passes after content is generated.
- [ ] Target repo CI passes before auto-merge.
