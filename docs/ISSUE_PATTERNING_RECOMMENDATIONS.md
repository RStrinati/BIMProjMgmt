# Issue Patterning Enhancements

## Current Workflow Overview
- `IssueAnalyticsService.calculate_pain_points_by_project()` and `.calculate_pain_points_by_discipline()` aggregate urgency, complexity, and open issue ratios into a weighted pain point score to surface hotspots at the project and discipline levels.【F:services/issue_analytics_service.py†L46-L140】【F:services/issue_analytics_service.py†L142-L225】
- `IssueAnalyticsService.identify_recurring_patterns()` clusters issues when their extracted keyword sets share a Jaccard similarity of ≥0.8 and reports aggregate metrics for clusters with at least three issues.【F:services/issue_analytics_service.py†L233-L343】
- The Issue Analytics Dashboard renders the resulting patterns tab, coloring rows by occurrence and highlighting keyword-driven clusters for checklist creation.【F:docs/ANALYTICS_DASHBOARD_QUICK_REF.md†L112-L151】

## Limitations of Pain Point-Centric Detection
- Pain point scores emphasize severity (urgency, complexity, unresolved ratio) but do not measure semantic similarity between issues, so they can miss systemic patterns where individual items are quickly resolved yet highly repetitive.【F:services/issue_analytics_service.py†L119-L214】
- Aggregations occur primarily at project and discipline levels, limiting visibility into client-wide or source-specific trends that span multiple portfolios (ACC vs. Revizto).【F:services/issue_analytics_service.py†L46-L214】【F:docs/ISSUE_ANALYTICS_ROADMAP.md†L173-L208】
- Current pattern clustering relies on literal keyword overlap, making it sensitive to vocabulary drift (e.g., "duct clash" vs. "service collision") and unable to group contextually similar issues with different phrasing.【F:services/issue_analytics_service.py†L281-L343】

## Recommendations to Enhance Pattern Recognition
1. **Semantic Clustering Layer**
   - Introduce sentence-embedding similarity (e.g., SBERT) on titles/descriptions before keyword Jaccard filtering to capture synonymous phrasing and domain-specific terminology shifts.
   - Combine embedding scores with existing keyword overlap to maintain interpretability while broadening match recall.

2. **Client and Source Segmentation**
   - Extend the analytics views to provide side-by-side matrices by client, project type, and source (ACC vs. Revizto) so recurring patterns that traverse organizations become visible.【F:docs/ISSUE_ANALYTICS_ROADMAP.md†L173-L208】
   - Surface deltas in the dashboard (e.g., pattern frequency per client) to prioritize cross-portfolio standardization.

3. **Temporal Recurrence Signals**
   - Track rolling frequency, time-to-recurrence, and reopened rates to separate chronic patterns from one-off spikes.
   - Add seasonality trendlines that correlate pattern emergence with project milestones or coordination cycles.

4. **Root Cause Enrichment**
   - Map patterns to taxonomy attributes (discipline, issue type, phase) already captured in `ProcessedIssues` to auto-suggest remediation checklists and responsible teams.【F:services/issue_analytics_service.py†L251-L343】
   - Annotate clusters with representative comments or resolution steps to contextualize remediation impact.

5. **Actionability Scoring**
   - Layer a priority index that combines recurrence, severity, and breadth (projects/clients affected) so stakeholders can rank systemic issues beyond simple pain scores.
   - Integrate into the dashboard recommendations tab to trigger targeted workflows.【F:docs/ANALYTICS_DASHBOARD_QUICK_REF.md†L153-L176】

By complementing severity-driven pain points with richer semantic, temporal, and organizational lenses, the analytics suite can elevate latent patterns across ACC and Revizto portfolios and guide higher-impact process improvements.

## Implementation Status

- Implemented a hybrid semantic and keyword clustering workflow that combines transformer or TF-IDF embeddings with Jaccard overlap, allowing synonymous issues to form a single pattern cluster when similarity exceeds the blended threshold.【F:services/issue_analytics_service.py†L237-L461】
- Expanded each recurring pattern with client, source, and taxonomy breakdowns (discipline, issue type, phase) plus representative project names to surface cross-portfolio context for remediation planning.【F:services/issue_analytics_service.py†L470-L599】
- Added temporal recurrence analytics and composite actionability scoring so patterns now expose first/last seen dates, recency, cycle times, and a prioritized index blending recurrence, severity, and breadth for dashboard consumption.【F:services/issue_analytics_service.py†L540-L606】
