# Issue Analytics System - Quick Start Guide

## Overview

A comprehensive system for analyzing construction project issues across ACC and Revizto data sources. Provides automated categorization, pain point identification, and trend analysis by client, project type, and discipline.

**Current Data:**
- 2,421 ACC issues across 10 projects
- 3,461 Revizto issues from 1 project
- 5,882 total issues in combined view

## What Has Been Created

### 1. Documentation
✅ **`docs/ISSUE_ANALYTICS_ROADMAP.md`** - Complete implementation roadmap with:
- Architecture overview
- Database schema design (6 tables, 5 views)
- Text processing strategies
- Category taxonomy (200+ categories across 3 levels)
- Implementation phases (9-week timeline)
- Expected insights and use cases

### 2. Database Schema (`sql/`)
✅ **`create_issue_analytics_schema.sql`** - Creates:
- **IssueCategories** - Hierarchical taxonomy (disciplines, types, sub-types)
- **IssueCategoryKeywords** - 200+ keywords for automated matching
- **ProcessedIssues** - Stores categorized issues with analysis
- **IssuePainPoints** - Aggregated pain points by client/project type
- **IssueComments** - Comment-level analysis
- **IssueProcessingLog** - Batch processing tracking
- 5 analytics views for reporting

✅ **`seed_issue_categories.sql`** - Populates:
- 9 discipline categories (Level 1)
- 48 issue type categories (Level 2)
- 100+ sub-type categories (Level 3)
- Total: ~160 categories

✅ **`seed_category_keywords.sql`** - Populates:
- 200+ keywords mapped to categories
- Weighted scoring (0.0 to 1.0)
- Discipline-specific keywords
- Issue type indicators

### 3. Python Services (`services/`)
✅ **`issue_text_processor.py`** - NLP engine with:
- Text cleaning and normalization
- Keyword extraction (frequency + TF-IDF)
- Sentiment analysis (-1.0 to +1.0)
- Urgency scoring (0.0 to 1.0)
- Complexity scoring (0.0 to 1.0)
- N-gram extraction (1-3 words)

✅ **`issue_categorizer.py`** - Categorization engine with:
- Keyword-based category matching
- Multi-level categorization (discipline → type → sub-type)
- Confidence scoring
- Batch processing capability
- Category hierarchy navigation

### 4. Dependencies
✅ Updated **`requirements.txt`** with:
- nltk >= 3.8 (natural language processing)
- scikit-learn >= 1.3.0 (TF-IDF, machine learning)
- matplotlib >= 3.7.0 (visualizations)

## Category Taxonomy

### Level 1: Disciplines (9 categories)
- Structural
- Architectural
- Mechanical (HVAC)
- Electrical
- Hydraulic/Plumbing
- Fire Protection
- Civil
- Multi-Discipline
- Other/General

### Level 2: Issue Types (6 types per discipline = 48 total)
- Clash/Coordination
- Design Issue
- Information Issue
- Code Compliance
- Constructability
- Quality Issue

### Level 3: Sub-Types (examples)
**Clash/Coordination:**
- Hard Clash
- Clearance Issue
- Penetration Conflict
- Access Conflict
- Service Routing

**Design Issue:**
- Design Error
- Incomplete Design
- Design Change
- Design Optimization

## Installation Steps

### 1. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Download NLTK Data
```powershell
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
```

Or run the text processor test:
```powershell
python services\issue_text_processor.py
```

### 3. Create Database Schema
```powershell
# Connect to SQL Server and run:
sqlcmd -S YOUR_SERVER -d ProjectManagement -i sql\create_issue_analytics_schema.sql
sqlcmd -S YOUR_SERVER -d ProjectManagement -i sql\seed_issue_categories.sql
sqlcmd -S YOUR_SERVER -d ProjectManagement -i sql\seed_category_keywords.sql
```

Or use SQL Server Management Studio to run the scripts manually.

### 4. Verify Installation
```powershell
python -c "from services.issue_categorizer import IssueCategorizer; cat = IssueCategorizer(); print(f'Categories: {len(cat.categories)}, Keywords: {len(cat.keywords)}')"
```

Expected output:
```
✓ Loaded 160+ categories
✓ Loaded 200+ unique keywords
Categories: 160, Keywords: 200
```

## Testing the System

### Test Text Processor
```powershell
python services\issue_text_processor.py
```

Processes 3 sample issues and shows:
- Extracted keywords
- Sentiment scores
- Urgency scores
- Complexity scores

### Test Categorizer
```powershell
python services\issue_categorizer.py
```

Categorizes 5 sample issues and shows:
- Discipline category
- Primary type
- Secondary type
- Confidence scores
- Keyword matches

### Example Output
```
Issue 1: Hydraulic Issue - Hydraulic pipework clearance to civil drainage <300mm
----------------------------------------------------------------------
Discipline: Hydraulic/Plumbing
Primary Type: Clash/Coordination
Secondary Type: Clearance Issue
Confidence: 0.85
Top Scores: hydraulic(2.95), clearance(1.90), civil(0.80), pipework(0.95)
Extracted Keywords: hydraulic, pipework, clearance, civil, drainage
```

## Next Steps

### Phase 2: Analytics Service (Not Yet Implemented)
Create `services/issue_analytics_service.py` to:
- Extract issues from `vw_ProjectManagement_AllIssues`
- Process and categorize all issues
- Calculate pain points by client/project type
- Detect recurring issues
- Generate trend analyses

### Phase 3: Batch Processing (Not Yet Implemented)
Create `services/issue_batch_processor.py` to:
- Process all existing issues (5,882 issues)
- Insert into ProcessedIssues table
- Calculate aggregate metrics
- Populate IssuePainPoints table

### Phase 4: UI Dashboard (Not Yet Implemented)
Create `ui/tab_issue_analytics.py` to:
- Display issue analytics dashboard
- Filter by client, project type, date range
- Show charts and visualizations
- Export reports

## Database Views for Queries

### View: vw_IssueAnalytics_ByClient
Get issues by client and category:
```sql
SELECT 
    client_name,
    category_name,
    total_issues,
    open_issues,
    avg_resolution_days,
    avg_urgency
FROM vw_IssueAnalytics_ByClient
WHERE client_name = 'ABC Developers'
ORDER BY total_issues DESC;
```

### View: vw_IssueAnalytics_ByProjectType
Get issues by project type:
```sql
SELECT 
    project_type_name,
    category_name,
    total_issues,
    recurring_count,
    avg_complexity
FROM vw_IssueAnalytics_ByProjectType
ORDER BY total_issues DESC;
```

### View: vw_TopPainPoints
Get top pain points:
```sql
SELECT TOP 20
    category_name,
    client_name,
    total_issues,
    avg_resolution_days,
    trend_direction
FROM vw_TopPainPoints
ORDER BY total_issues DESC;
```

## Example Use Cases

### Use Case 1: Client Pain Point Analysis
**Question:** "What are ABC Developers' top 5 recurring issues?"

**Query:**
```sql
SELECT 
    ic.category_name,
    COUNT(pi.processed_issue_id) as issue_count,
    AVG(pi.resolution_days) as avg_days,
    SUM(CASE WHEN pi.is_recurring = 1 THEN 1 ELSE 0 END) as recurring_count
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN clients c ON p.client_id = c.client_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id
WHERE c.client_name = 'ABC Developers'
GROUP BY ic.category_name
ORDER BY issue_count DESC;
```

### Use Case 2: Project Type Predictions
**Question:** "What should we expect in a new school project?"

**Analysis:** Query historical school projects for:
- Common issue categories (top 10)
- Average resolution times
- High-priority issue frequency
- Recurring problems

### Use Case 3: Discipline Workload
**Question:** "Which disciplines need more coordination time?"

**Query:**
```sql
SELECT 
    ic.category_name as discipline,
    COUNT(pi.processed_issue_id) as issue_count,
    AVG(pi.complexity_score) as avg_complexity,
    AVG(pi.urgency_score) as avg_urgency
FROM ProcessedIssues pi
JOIN IssueCategories ic ON pi.discipline_category_id = ic.category_id
WHERE ic.category_level = 1
GROUP BY ic.category_name
ORDER BY issue_count DESC;
```

## Keyword Examples

### Hydraulic Keywords (weight)
- hydraulic (1.0)
- plumbing (1.0)
- pipework (0.95)
- drainage (0.95)
- water (0.85)
- sanitary (0.90)

### Clash Keywords (weight)
- clash (0.95)
- conflict (0.90)
- overlap (0.90)
- clearance (0.85)
- coordination (0.85)

### Clearance Keywords (weight)
- clearance (0.95)
- <300mm (1.0)
- insufficient space (0.90)
- too close (0.90)

## Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Extract Issues from vw_ProjectManagement_AllIssues     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Text Processing                                          │
│    - Clean text                                             │
│    - Extract keywords                                       │
│    - Calculate sentiment/urgency/complexity                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Categorization                                           │
│    - Match keywords to categories                           │
│    - Assign discipline, type, sub-type                      │
│    - Calculate confidence                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Insert into ProcessedIssues Table                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Calculate Pain Points                                    │
│    - Aggregate by client/project type/category             │
│    - Calculate trends                                       │
│    - Identify recurring issues                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Display in UI Dashboard                                  │
└─────────────────────────────────────────────────────────────┘
```

## Performance Expectations

- **Text Processing:** ~1 second per issue
- **Categorization:** ~0.5 seconds per issue
- **Batch Processing (5,000 issues):** ~15-20 minutes
- **Pain Point Calculation:** <10 seconds per client/type
- **Database Query Response:** <2 seconds for most views

## Troubleshooting

### Issue: NLTK data not found
```
LookupError: Resource stopwords not found
```
**Solution:**
```powershell
python -m nltk.downloader stopwords punkt
```

### Issue: scikit-learn not installed
```
ImportError: No module named 'sklearn'
```
**Solution:**
```powershell
pip install scikit-learn
```

### Issue: Categories not loading
```
❌ Failed to connect to database
```
**Solution:**
- Verify database connection in `config.py`
- Ensure SQL scripts have been run
- Check that IssueCategories table exists

### Issue: No keyword matches
```
Confidence: 0.0, No matches found
```
**Solution:**
- Run `seed_category_keywords.sql` script
- Verify keywords loaded: `SELECT COUNT(*) FROM IssueCategoryKeywords`
- Check if keywords are active: `WHERE is_active = 1`

## File Structure

```
BIMProjMngmt/
├── docs/
│   ├── ISSUE_ANALYTICS_ROADMAP.md          # Full implementation plan
│   └── ISSUE_ANALYTICS_QUICKSTART.md       # This file
├── sql/
│   ├── create_issue_analytics_schema.sql   # Database tables & views
│   ├── seed_issue_categories.sql           # Category taxonomy
│   └── seed_category_keywords.sql          # Keyword mappings
├── services/
│   ├── issue_text_processor.py             # NLP engine
│   ├── issue_categorizer.py                # Categorization engine
│   ├── issue_analytics_service.py          # [TODO] Analytics
│   └── issue_batch_processor.py            # [TODO] Batch processing
└── ui/
    └── tab_issue_analytics.py              # [TODO] UI dashboard
```

## Contact & Support

For questions or issues:
1. Review `docs/ISSUE_ANALYTICS_ROADMAP.md` for detailed documentation
2. Test individual components using the test scripts
3. Check database views for data availability

---

**Status:** Foundation Complete (Phases 1-2)  
**Next Phase:** Analytics Service Implementation  
**Last Updated:** October 2, 2025
