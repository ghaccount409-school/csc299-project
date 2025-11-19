## Speckit Technical Constitution

A compact set of principles and governance rules to guide technical decisions, implementation choices, reviews, and maintenance. Focus areas: code clarity & simplicity, code quality, testing standards, and consistent user experience.

### Contract
- Inputs: proposed code changes, design changes, or architectural proposals.
- Outputs: production-ready changes that are readable, well-tested, accessible, and consistent with product UX.
- Error modes: regressions, unclear/fragile code, UX regressions, missed security/performance constraints.
- Success criteria: CI green, PR approved against checklist, automated quality gates passed, and maintainable code (key flows understandable in <30 minutes).

## Core Principles

1. Clarity & Simplicity
   - Prefer explicit, easy-to-read code over cleverness. Readability beats micro-optimizations except in measured hotspots.
   - Keep functions small and single-responsibility. Use descriptive names and avoid deep nesting.
   - Code should self-explain where possible; document non-obvious invariants near the code.

2. High Code Quality & Safety
   - Enforce static typing when available. Use linters, formatters, and type checks before merges.
   - Treat error handling as first-class; handle and test failure paths explicitly.
   - Prefer small, well-maintained dependencies. Minimize public surface area.

3. Robust Testing Standards
   - Tests are part of design: unit tests for logic, integration tests for interactions, E2E for user journeys.
   - Every PR must include tests for new logic and regression tests for fixed bugs.
   - Tests must be deterministic and fast enough for CI; slow tests move to scheduled suites.

4. Consistent User Experience & Accessibility
   - Follow shared design patterns and tokens. Accessibility is non-optional; include a11y checks.
   - Monitor performance budgets and avoid UX regressions.

5. Pragmatic Simplicity (KISS + YAGNI)
   - Implement the smallest change that solves the problem. Defer complexity until justified by metrics or product need.

6. Use Emojis in Output
   - Add emojis in program output when possible. Be happy!

## Implementation Guidance & Rules

- Naming and structure: use meaningful names; public APIs must include short doc comments describing inputs, outputs, side effects, and errors.
- Function size & complexity: prefer short functions; enforce complexity limits via tooling. If complex, split responsibilities and add tests.
- Error handling: fail early in development; sanitize and log errors in production with contextual metadata. Tests must exercise negative paths.
- Dependencies: add major dependencies only with a short justification. Prefer proven community libraries.
- Performance: optimize only after measurement; mark hotspots and include micro-benchmarks for critical paths.
- Documentation: user-facing documentation (user guides, README updates, changelog entries, or docs site updates) must be created or updated in the same PR as the change or in a linked follow-up that is merged to `master` together with the implementation. Documentation should be accurate, discoverable, and include any migration steps or user impact notes.

## Testing Standards (Concrete)

- Unit tests: fast, isolated, deterministic. Mock external services and cover error branches.
- Integration tests: validate interactions between modules and with controlled test doubles.
- End-to-end tests: automate critical user journeys; keep E2E narrow and stable.
- Naming: "should <expected behavior> when <context>". Quarantine and fix flaky tests within 48 hours.

## UX Consistency Rules

- Use a shared component system and design tokens. Document behavioral patterns (modals, forms, errors).
- Include automated accessibility checks in CI and at least one manual accessibility pass for feature-complete pages.
- Any deviation from patterns requires visual/design approval and a migration plan.

## Governance: How Principles Guide Decisions

1. PR Checklist (required)
   - Types/lints/format pass.
   - Tests added/updated; CI green.
   - Integration/E2E added if behavior crosses module boundaries.
   - UX/Design owner informed for UI changes.
   - Accessibility checks completed.
   - User documentation created/updated and included in the PR (or linked PR) and merged to `master` together with the change.
   - ADR created if architectural impact.

2. Review & Approval
   - Small changes: 1 reviewer + CI green.
   - Significant changes: 2+ reviewers including domain owner (security/UX/perf).
   - Breaking API changes require an ADR and migration plan.

3. Exceptions & Hotfixes
   - Hotfixes allowed with post-facto PR documenting the fix, risk assessment, and rollback plan.
   - Time-limited approvals for exceptions with remediation plans.

4. ADRs
   - Document problem, options considered, decision, trade-offs, and migration path. Link ADRs from implementing PRs.

5. Metrics & Compliance
   - Track CI pass rate, test coverage trends, production incidents from code quality, and UX regressions.
   - Periodic audits (monthly/quarterly) to evaluate adherence.

6. Enforcement & Tooling
   - Automate checks: linters, type checks, security scanners, a11y checks, CI gating.
   - Use code owners and protected branches for required reviewers.

## Decision Flow (short)
1. What user need or bug does this address?
2. Can a minimal, well-tested change solve it? Prefer that.
3. Does this touch shared/public APIs? If yes, ADR or migration required.
4. Accessibility or performance impacts? Add tests/benchmarks and notify owners.
5. Can this be enforced with automated checks? Add to CI if so.
6. If deviating, document trade-offs and seek approval.

## Edge Cases & Legacy
- Legacy code: prefer small, localized fixes and tests. Schedule refactors in small increments.
- Platform limits: document constraints and provide compensating controls.
- Third-party failures: use retries, circuit-breakers, and simulate failures in integration tests.

## PR Author Quick Checklist
- [ ] Types/lints/format pass
- [ ] Unit tests added/updated; CI green
- [ ] Integration/E2E added if needed
- [ ] UX/Design owner review requested (UI changes)
- [ ] Accessibility checks completed
- [ ] ADR created if architectural impact
- [ ] Short rationale & trade-offs in PR description

## Roles & Cadence
- Weekly triage for urgent items.
- Monthly architecture sync for ADRs and exceptions.
- Quarterly audit of CI health, coverage, and incidents.
- Roles: domain owner, architecture steward, release owner.

## Measurement & Improvement
- Track PR cycle time, CI pass rate, coverage trends, rollbacks, and post-release accessibility issues.
- Post-mortems and retro learning feed a backlog of constitution-driven improvements.
- Review and update this document annually or sooner when systemic issues arise.

## Templates & Examples
- PR template: summary, why, changes, tests, migration notes, perf/a11y notes.
- ADR template: title, status, context, decision, consequences, alternatives, migration plan.

---

Treat this document as the default decision guide. Automate enforcement where possible and use human review for nuance. When in doubt: prefer clarity, tests, accessibility, and the minimal change that meets product needs.
