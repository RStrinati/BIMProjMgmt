# North Star: Governance & Priorities

## Goal

Establish a clear, phase-based development roadmap that prioritizes **core model correctness**, **import robustness**, **UI clarity**, and defers complex analytics work until the foundation is solid.

## Priority Order (Phases)

### Phase 1: Core Model Correctness (NOW)
**Objective**: Align all code and documentation to the Option A core model.

- Project → Services → {Reviews, Items}
- Tasks are project-owned and separate
- Items and Reviews are independent peers under Services
- All developers understand and apply the model consistently

**Done Criteria**:
- ✅ Documentation aligns to core model (README, Copilot instructions)
- ✅ Invariants are explicit and enforced in reasoning
- ✅ No code implies Items belong to Reviews
- ✅ Import linking follows service-first priority

**Issues**: #104, #105

---

### Phase 2: Import Robustness (Next 4 weeks)
**Objective**: Ensure imports (ACC issues, Health data) link reliably and maintain data integrity.

- ACC issue import fully operational and linked to service/review/item as applicable
- Revit Health import analysis complete; reliability improved or documented
- Unmapped imports tracked and visible for later manual assignment
- Import run summaries accurate and transparent

**Done Criteria**:
- ✅ Import run summary shows all issues (mapped + unmapped)
- ✅ Health data reliability report available
- ✅ Service-first linking applied to all imports
- ✅ Import pipeline logs and error handling robust

**Issues**: #108

---

### Phase 3: UI Refinement (Weeks 5–8)
**Objective**: Ensure React UI clearly reflects the core model structure.

- Services display Reviews and Items as independent peers
- No UI implies Items depend on Reviews
- Linear-style workspace supports service-centric navigation
- All dashboards reflect correct hierarchies

**Done Criteria**:
- ✅ UI read-only alignment verified
- ✅ Services → Reviews and Items render separately
- ✅ No user confusion about hierarchy

**Issues**: #107

---

### Phase 4: Testing & Automation (Weeks 9–12)
**Objective**: Define and implement automated test coverage for critical flows.

- Playwright coverage for core flows (project creation, service application, review/item creation, imports)
- Integration tests for model invariants
- Database state verification before and after operations

**Done Criteria**:
- ✅ Core Playwright flows defined and scoped
- ✅ First batch of tests implemented
- ✅ CI/CD integration ready

**Issues**: #106

---

### Phase 5+: Analytics, Bid Management, Billing (DEFERRED)
**Deferred to**: Q2 2026

- Dashboards and analytics layer rewrite
- Bid management refinement
- Billing claims and service billing integration

These require a stable foundation from Phases 1–4.

---

## Success Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| Phase 1 | Code/doc alignment | 100% |
| Phase 2 | Import success rate | >95% |
| Phase 2 | Unmapped issue tracking | All issues visible |
| Phase 3 | UI consistency | No hierarchy confusion |
| Phase 4 | Test coverage (core flows) | 5+ flows automated |

---

## Governance Rules

1. **No model deviation**: All features must align to the core model (Option A)
2. **Invariants are non-negotiable**: `Items.service_id`, `Reviews.service_id`, `Tasks.project_id` are mandatory
3. **Imports preserve fidelity**: Unmapped imports are valid; do not force them into Tasks
4. **Documentation is source of truth**: If code and docs conflict, code is wrong
5. **Phases are sequential**: Phase 2 begins only when Phase 1 is complete

---

## Owner & Communication

- **Owner**: AI Codex / Copilot (with human verification)
- **Verification**: Manual review by project stakeholder before each phase completion
- **Communication**: GitHub Issues and this document are the source of truth

Last updated: January 16, 2026
