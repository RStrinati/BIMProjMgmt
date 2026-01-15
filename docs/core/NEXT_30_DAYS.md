# Next 30 Days: Execution Plan

## Horizon
Week of January 16 – February 13, 2026

---

## Initiative 1: Core Model Alignment (PHASE 1)
**GitHub Issues**: #104, #105
**Owner**: Copilot / Codex (human verification)
**Verification**: Manual doc review

### Entry 1.1: Align Documentation to Core Model (Option A)
**Issue**: #104

**Goal**  
Update README.md and Copilot/AGENTS instructions to reflect the agreed Core Model (Option A):
- Project → Services → {Reviews, Items}
- Items and Reviews are independent peers
- Tasks are separate

**Acceptance Criteria**
- [ ] README contains "Core Conceptual Model" section with hierarchy diagram
- [ ] Copilot instructions explicitly state "Items are NOT Tasks"
- [ ] No documentation implies Items depend on Reviews
- [ ] Linking priority documented (project → service → review/item)

**Verification**
- Manual review by stakeholder

**Owner**: Copilot
**Timeline**: Jan 16–20

---

### Entry 1.2: Formalise Service / Review / Item Invariants
**Issue**: #105

**Goal**  
Document hard invariants for service ownership of Reviews and Items.

**Acceptance Criteria**
- [ ] Schema invariants documented (service_id required for reviews/items)
- [ ] No Review↔Item dependency stated anywhere
- [ ] Enforcement rules clear to all developers
- [ ] Examples provided (service can have reviews without items, etc.)

**Verification**
- Manual review by stakeholder

**Owner**: Codex
**Timeline**: Jan 21–24

---

## Initiative 2: Import Robustness (PHASE 2)
**GitHub Issue**: #108
**Owner**: Codex
**Verification**: Manual import run + analysis

### Entry 2.1: Health Data Reliability & Linking Review
**Issue**: #108

**Goal**  
Identify why Revit Health imports are less reliable. Document findings and candidate fixes. No code changes yet.

**Acceptance Criteria**
- [ ] Problem statement: Why health imports fail or produce incomplete data
- [ ] Candidate fixes identified (data format issues, mapping gaps, etc.)
- [ ] Linking expectations documented (service-first priority)
- [ ] Report added to `docs/` directory

**Verification**
- Manual import run
- Analysis walkthrough with stakeholder

**Owner**: Codex
**Timeline**: Jan 25–29

---

## Initiative 3: UI Clarity (PHASE 3)
**GitHub Issue**: #107
**Owner**: Human (with Copilot support)
**Verification**: Manual UI check

### Entry 3.1: Linear Workspace Review / Item Peer Display
**Issue**: #107

**Goal**  
Ensure React UI treats Reviews and Items as independent peers under Services. Read-only alignment first.

**Acceptance Criteria**
- [ ] Services render Reviews as one stream
- [ ] Services render Items as separate stream
- [ ] No UI implies Reviews contain Items
- [ ] UI clear and intuitive to end user

**Verification**
- Manual UI check in dev server
- Screenshot walkthrough with stakeholder

**Owner**: Human
**Timeline**: Feb 1–5

---

## Initiative 4: Test Strategy (PHASE 4)
**GitHub Issue**: #106
**Owner**: Codex / Copilot
**Verification**: Manual review

### Entry 4.1: Define Core Playwright Flows
**Issue**: #106

**Goal**  
Document which user flows will get Playwright automation coverage. Establish scope and priority.

**Acceptance Criteria**
- [ ] 5 core flows identified and scoped:
  - Project creation
  - Service application
  - Review creation
  - Item creation
  - Import run summary
- [ ] Test scope documented (manual vs automated)
- [ ] First batch identified for implementation
- [ ] Test infrastructure ready

**Verification**
- Manual review of test plan

**Owner**: Copilot
**Timeline**: Feb 6–10

---

## Deferred (Post-February)
- ❌ Dashboards & analytics layer rewrite (Phase 5+)
- ❌ Bid management refinement (Phase 5+)
- ❌ Billing claims integration (Phase 5+)

These defer to Q2 2026 after foundation work completes.

---

## Weekly Checkpoints

| Week | Checkpoint | Owner |
|------|-----------|-------|
| Jan 16–20 | Entry 1.1 complete; docs aligned | Copilot |
| Jan 21–24 | Entry 1.2 complete; invariants formalized | Codex |
| Jan 25–29 | Entry 2.1 complete; health analysis done | Codex |
| Feb 1–5 | Entry 3.1 complete; UI alignment verified | Human |
| Feb 6–10 | Entry 4.1 complete; test scope defined | Copilot |

---

## Risk & Rollback

| Initiative | Risk | Rollback |
|-----------|------|----------|
| 1 (Docs) | Incomplete alignment | `git revert` of doc commits |
| 2 (Imports) | Analysis incomplete | N/A (no code changes) |
| 3 (UI) | UI refactor required later | Revert component changes |
| 4 (Tests) | Scope creep | Focus on 5 core flows only |

---

## Success = Foundation Ready for Phase 2+

By Feb 13, 2026:
- ✅ Core model is canonical in all docs and code
- ✅ All developers understand invariants
- ✅ Import linking is service-first and reliable
- ✅ UI clearly reflects model structure
- ✅ Test strategy is defined and ready to implement

Last updated: January 16, 2026
