# Usability Validation Plan (Reviews Module)

Audience: 4–6 BIM coordinators + 1 project manager.
Duration: 30–45 minutes per session.
Method: Remote screen-share or in-person, think‑aloud; record with consent.

## Pre-setup
- Environment: Open frontend prototype in browser
- Data: Seed one project with 2 stages and 6 reviews (or use sample API responses)
- Roles: Moderator, note-taker (optional)

## Tasks
1. Select your project and scan the Review schedule overview
   - Success: Correct project chosen, understands cycle counts and dates
2. Create a new stage (name, start/end, 4 reviews) and generate cycles
   - Success: Stage appears; cycles visible; no errors
3. Change a review date and assign a reviewer
   - Success: Update visible without page refresh confusion
4. Attach a folder path to a specific review and confirm contents appear
   - Success: Path stored and file list renders (sample files ok)
5. Filter the reviews by status and cycle
   - Success: Narrowed list matches expectation
6. Switch to Kanban and move a review to Issued
   - Success: Card re-lanes with clear feedback

## Metrics
- Time-on-task per task (min)
- Errors: slips, mistakes, and blocks
- System Usability Scale (SUS) 10-question survey
- Top 3 friction points + suggestions

## Acceptance Criteria
- ≥80% tasks completed without moderator intervention
- ≤1 critical blocker discovered across participants
- SUS ≥ 75
- Clear next-step issues logged with owners
