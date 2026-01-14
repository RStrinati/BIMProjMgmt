# Issue Analytics System - Implementation Roadmap

## Executive Summary

This system analyzes construction project issues across multiple data sources (ACC, Revizto) to identify pain points, recurring patterns, and project-specific challenges. By processing issue titles, descriptions, comments, and priorities, the system provides actionable insights segmented by client, project type, discipline, and issue category.

**Data Sources:**
- `acc_data_schema.dbo.vw_issues_expanded_pm` - 2,421 ACC issues across 10 projects
- `ProjectManagement.dbo.vw_ProjectManagement_AllIssues` - Combined view (5,882 total issues)
- Future: Revizto issues (3,461 issues from 1 project)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Issue Analytics System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Data Layer   │  │  Processing  │  │   Analytics        │   │
│  │  - ACC Issues │──│  - Text NLP  │──│   - Aggregation    │   │
│  │  - Revizto    │  │  - Category  │  │   - Trend Analysis │   │
│  │  - Combined   │  │  - Sentiment │  │   - Pain Points    │   │
│  └───────────────┘  └──────────────┘  └────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Presentation Layer (Tkinter UI)                  │  │
│  │  - Dashboards  - Filters  - Visualizations  - Reports    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema Design

### New Tables

#### 1. IssueCategories
Hierarchical taxonomy for issue classification:
```sql
CREATE TABLE IssueCategories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name NVARCHAR(100) NOT NULL,
    parent_category_id INT NULL,
    category_level INT NOT NULL, -- 1: Discipline, 2: Type, 3: Sub-type
    description NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (parent_category_id) REFERENCES IssueCategories(category_id)
);
```

**Category Hierarchy:**
- **Level 1 - Disciplines:** Structural, Mechanical, Electrical, Hydraulic, Civil, Architectural, Fire Protection
- **Level 2 - Issue Types:** Clash/Coordination, Design Error, Missing Information, Code Compliance, Constructability, RFI
- **Level 3 - Sub-types:** Clearance Issues, Penetration Conflicts, Service Routing, etc.

#### 2. IssueCategoryKeywords
Keyword mapping for automated categorization:
```sql
CREATE TABLE IssueCategoryKeywords (
    keyword_id INT IDENTITY(1,1) PRIMARY KEY,
    category_id INT NOT NULL,
    keyword NVARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0, -- For relevance scoring
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (category_id) REFERENCES IssueCategories(category_id)
);
```

**Example Keywords:**
- "clash" → Clash/Coordination (weight: 0.9)
- "clearance" → Clearance Issues (weight: 0.95)
- "hydraulic" → Hydraulic discipline (weight: 1.0)
- "peno", "penetration" → Penetration Conflicts (weight: 0.85)

#### 3. ProcessedIssues
Stores categorized and analyzed issues:
```sql
CREATE TABLE ProcessedIssues (
    processed_issue_id INT IDENTITY(1,1) PRIMARY KEY,
    source NVARCHAR(50) NOT NULL, -- 'ACC' or 'Revizto'
    source_issue_id NVARCHAR(255) NOT NULL,
    project_id INT NOT NULL,
    title NVARCHAR(500),
    description NVARCHAR(MAX),
    status NVARCHAR(50),
    priority NVARCHAR(50),
    assignee NVARCHAR(255),
    created_at DATETIME2,
    closed_at DATETIME2,
    
    -- Categorization
    primary_category_id INT,
    secondary_category_id INT,
    discipline_category_id INT,
    
    -- Text Analysis
    sentiment_score DECIMAL(3,2), -- -1 to +1
    urgency_score DECIMAL(3,2), -- 0 to 1
    complexity_score DECIMAL(3,2), -- 0 to 1
    extracted_keywords NVARCHAR(MAX), -- JSON array
    
    -- Metrics
    resolution_days INT,
    comment_count INT,
    last_activity_date DATETIME2,
    
    -- Processing
    processed_at DATETIME2 DEFAULT GETDATE(),
    processing_version NVARCHAR(20) DEFAULT '1.0',
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (primary_category_id) REFERENCES IssueCategories(category_id),
    FOREIGN KEY (secondary_category_id) REFERENCES IssueCategories(category_id),
    FOREIGN KEY (discipline_category_id) REFERENCES IssueCategories(category_id),
    UNIQUE (source, source_issue_id)
);
```

#### 4. IssuePainPoints
Aggregated pain point analysis:
```sql
CREATE TABLE IssuePainPoints (
    pain_point_id INT IDENTITY(1,1) PRIMARY KEY,
    client_id INT NULL,
    project_type_id INT NULL,
    category_id INT NOT NULL,
    
    -- Metrics
    total_issues INT NOT NULL,
    open_issues INT NOT NULL,
    avg_resolution_days DECIMAL(6,2),
    recurring_issue_count INT,
    
    -- Time windows
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Severity indicators
    critical_count INT DEFAULT 0,
    high_priority_count INT DEFAULT 0,
    
    -- Insights
    common_keywords NVARCHAR(MAX), -- JSON array
    sample_issue_ids NVARCHAR(MAX), -- JSON array of representative issues
    
    calculated_at DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (project_type_id) REFERENCES project_types(project_type_id),
    FOREIGN KEY (category_id) REFERENCES IssueCategories(category_id)
);
```

#### 5. IssueComments
Extracted comments for deeper analysis:
```sql
CREATE TABLE IssueComments (
    comment_id INT IDENTITY(1,1) PRIMARY KEY,
    processed_issue_id INT NOT NULL,
    comment_text NVARCHAR(MAX),
    comment_by NVARCHAR(255),
    comment_at DATETIME2,
    sentiment_score DECIMAL(3,2),
    is_resolution BIT DEFAULT 0, -- Indicates resolution comment
    extracted_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (processed_issue_id) REFERENCES ProcessedIssues(processed_issue_id)
);
```

### Views

#### vw_IssueAnalytics_ByClient
```sql
CREATE VIEW vw_IssueAnalytics_ByClient AS
SELECT 
    c.client_id,
    c.client_name,
    ic.category_name,
    COUNT(pi.processed_issue_id) as total_issues,
    SUM(CASE WHEN pi.status IN ('open', 'in_progress') THEN 1 ELSE 0 END) as open_issues,
    AVG(pi.resolution_days) as avg_resolution_days,
    AVG(pi.urgency_score) as avg_urgency,
    COUNT(DISTINCT pi.project_id) as project_count
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN clients c ON p.client_id = c.client_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id
GROUP BY c.client_id, c.client_name, ic.category_name;
```

#### vw_IssueAnalytics_ByProjectType
```sql
CREATE VIEW vw_IssueAnalytics_ByProjectType AS
SELECT 
    pt.project_type_id,
    pt.project_type_name,
    ic.category_name,
    COUNT(pi.processed_issue_id) as total_issues,
    SUM(CASE WHEN pi.status IN ('open', 'in_progress') THEN 1 ELSE 0 END) as open_issues,
    AVG(pi.resolution_days) as avg_resolution_days,
    AVG(pi.complexity_score) as avg_complexity
FROM ProcessedIssues pi
JOIN projects p ON pi.project_id = p.project_id
JOIN project_types pt ON p.type_id = pt.project_type_id
JOIN IssueCategories ic ON pi.primary_category_id = ic.category_id
GROUP BY pt.project_type_id, pt.project_type_name, ic.category_name;
```

## Text Processing Strategy

### 1. Natural Language Processing (NLP)

#### A. Text Cleaning Pipeline
```python
def clean_issue_text(text):
    """
    1. Remove special characters and normalize whitespace
    2. Convert to lowercase
    3. Remove stopwords (common words like 'the', 'a', 'is')
    4. Tokenize into words
    5. Apply stemming/lemmatization
    """
```

#### B. Keyword Extraction
**Methods:**
- **TF-IDF (Term Frequency-Inverse Document Frequency):** Identify important terms
- **N-grams:** Capture multi-word phrases (e.g., "clearance issue", "peno penetration")
- **Named Entity Recognition:** Extract specific items (equipment names, locations, disciplines)

**Libraries:**
- `nltk` - Natural Language Toolkit for text processing
- `scikit-learn` - TF-IDF vectorization
- `spacy` - Advanced NLP (optional for entity recognition)

#### C. Category Matching Algorithm
```python
def categorize_issue(title, description, comments):
    """
    1. Combine title + description + comments
    2. Extract keywords and phrases
    3. Match against IssueCategoryKeywords table
    4. Calculate weighted scores for each category
    5. Assign top 3 categories (primary, secondary, discipline)
    6. Handle multi-discipline issues
    """
    
    # Example scoring:
    # "Hydraulic pipework clearance to civil drainage <300mm"
    # - Keywords: hydraulic (1.0) + pipework (0.7) + clearance (0.95) + civil (0.8)
    # - Primary: Hydraulic discipline
    # - Secondary: Clearance Issues
    # - Type: Clash/Coordination
```

#### D. Sentiment & Urgency Analysis
```python
def analyze_sentiment(text):
    """
    Positive indicators: "resolved", "clarified", "approved"
    Negative indicators: "critical", "urgent", "blocking", "major issue"
    Neutral: informational updates
    
    Urgency keywords: "asap", "urgent", "critical", "immediate", "blocking"
    """
```

#### E. Complexity Estimation
```python
def estimate_complexity(issue):
    """
    Factors:
    - Number of disciplines involved (multi-discipline = higher)
    - Comment count (high = more complex discussion)
    - Resolution time (longer = more complex)
    - Keywords: "redesign", "significant", "multiple", "coordinated"
    """
```

### 2. Pattern Recognition

#### A. Recurring Issue Detection
```python
def find_recurring_issues(project_id, time_window_days=90):
    """
    1. Group issues by primary category
    2. Calculate text similarity using cosine similarity
    3. Cluster similar issues (threshold: 0.75 similarity)
    4. Flag clusters with 3+ occurrences as recurring
    """
```

#### B. Trend Analysis
```python
def analyze_trends(client_id, project_type_id, category_id):
    """
    - Weekly/monthly issue creation rates
    - Resolution time trends
    - Category distribution over time
    - Discipline involvement patterns
    """
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Deliverables:**
- [ ] Create database schema (tables, views, indexes)
- [ ] Populate IssueCategories with initial taxonomy
- [ ] Build IssueCategoryKeywords with 200+ keywords
- [ ] Create `issue_analytics_service.py` base structure
- [ ] Implement data extraction from source views

**SQL Scripts:**
- `sql/create_issue_analytics_schema.sql`
- `sql/seed_issue_categories.sql`
- `sql/seed_category_keywords.sql`

### Phase 2: Text Processing Engine (Week 3-4)
**Deliverables:**
- [ ] Text cleaning and normalization functions
- [ ] Keyword extraction using TF-IDF
- [ ] Category matching algorithm
- [ ] Sentiment analysis implementation
- [ ] Batch processing for existing issues

**Files:**
- `services/issue_text_processor.py`
- `services/issue_categorizer.py`
- `services/issue_batch_processor.py`

**Testing:**
- Process 100 sample issues manually validate categories
- Measure accuracy (target: 80%+ correct primary category)
- Adjust keyword weights based on results

### Phase 3: Analytics & Aggregation (Week 5-6)
**Deliverables:**
- [ ] Pain point calculation algorithms
- [ ] Recurring issue detection
- [ ] Trend analysis functions
- [ ] Client/project type aggregation
- [ ] Generate IssuePainPoints records

**Files:**
- `services/issue_analytics_aggregator.py`
- `services/recurring_issue_detector.py`
- `services/issue_trend_analyzer.py`

### Phase 4: UI Dashboard (Week 7-8)
**Deliverables:**
- [ ] New Tkinter tab: "Issue Analytics"
- [ ] Filter controls (client, project type, date range, category)
- [ ] Summary cards (total issues, top categories, resolution metrics)
- [ ] Charts using matplotlib:
  - Issues by discipline (bar chart)
  - Trend over time (line chart)
  - Resolution time distribution (histogram)
  - Top pain points (horizontal bar)
- [ ] Export functionality (Excel, CSV)

**Files:**
- `ui/tab_issue_analytics.py`
- `ui/components/issue_analytics_charts.py`
- `ui/components/issue_filters.py`

### Phase 5: Automation & Maintenance (Week 9)
**Deliverables:**
- [ ] Scheduled processing job (daily/weekly)
- [ ] Incremental processing (only new/updated issues)
- [ ] Category performance monitoring
- [ ] Admin interface for keyword management
- [ ] Documentation and training materials

**Files:**
- `services/issue_processing_scheduler.py`
- `ui/tab_category_admin.py`
- `docs/ISSUE_ANALYTICS_USER_GUIDE.md`

## Processing Workflows

### Workflow 1: Initial Bulk Processing
```
1. Extract all issues from vw_ProjectManagement_AllIssues
2. For each issue:
   a. Clean and normalize text
   b. Extract keywords
   c. Match categories
   d. Calculate sentiment/urgency/complexity
   e. Insert into ProcessedIssues
3. Calculate pain points for all clients/project types
4. Update IssuePainPoints table
```

### Workflow 2: Incremental Daily Processing
```
1. Query issues created/updated since last processing
2. Process new issues (same as bulk)
3. Recalculate pain points for affected clients/types
4. Archive old ProcessedIssues (older than 2 years) to history table
```

### Workflow 3: On-Demand Analysis
```
User selects: Client = "ABC Developers", Date Range = Last 6 months
1. Query ProcessedIssues with filters
2. Aggregate by category
3. Calculate metrics (avg resolution time, open %, trends)
4. Identify top pain points
5. Find recurring issues
6. Display in UI dashboard
```

## Category Taxonomy (Detailed)

### Discipline Categories (Level 1)
1. **Structural** - Steel, concrete, foundations
2. **Architectural** - Façade, interiors, finishes
3. **Mechanical (HVAC)** - Ductwork, AHUs, chillers
4. **Electrical** - Power, lighting, low voltage
5. **Hydraulic/Plumbing** - Water, drainage, gas
6. **Fire Protection** - Sprinklers, fire systems
7. **Civil** - Siteworks, earthworks, drainage
8. **Multi-Discipline** - Issues affecting 2+ disciplines

### Issue Type Categories (Level 2)
1. **Clash/Coordination**
   - Hard clashes (physical overlap)
   - Clearance issues (<300mm)
   - Access conflicts
   
2. **Design Issues**
   - Design errors
   - Incomplete design
   - Design changes
   
3. **Information Issues**
   - Missing information
   - RFI required
   - Specification clarification
   
4. **Code Compliance**
   - Building code violations
   - Standard non-compliance
   - Authority requirements
   
5. **Constructability**
   - Cannot build as designed
   - Installation difficulties
   - Sequencing issues
   
6. **Quality Issues**
   - Material defects
   - Workmanship concerns
   - Inspection failures

### Sub-Type Categories (Level 3)
Examples for Clash/Coordination:
- Penetration conflicts
- Service routing issues
- Clearance to structure
- Clearance to services
- Access for maintenance
- Installation space

## Expected Insights & Use Cases

### 1. Client-Specific Pain Points
**Question:** "What issues does Client X consistently face?"
**Analysis:**
- Top 5 issue categories for this client across all projects
- Comparison to industry average
- Trend over time (improving/worsening)
- Recommended preventive measures

**Output:**
```
ABC Developers - Top Pain Points:
1. Hydraulic clearance issues (15% of issues, avg 45 days to resolve)
2. Electrical penetration conflicts (12%, avg 30 days)
3. Structural design changes (8%, avg 60 days)

Insight: Client projects consistently have hydraulic coordination 
         issues. Recommend earlier MEP coordination workshops.
```

### 2. Project Type Predictive Analysis
**Question:** "What issues should we expect in a new school project?"
**Analysis:**
- Historical issue distribution for school projects
- Common categories and typical resolution times
- Risk factors (high-priority recurring issues)

**Output:**
```
School Projects (based on 3 historical projects):
Expected Issues:
- Fire protection compliance (20% of issues, typically 25 days)
- Electrical capacity queries (15%, typically 20 days)
- Acoustic requirements (10%, typically 35 days)

Plan for: Extra fire protection coordination in design phase
```

### 3. Performance Benchmarking
**Question:** "Are we getting better at resolving issues?"
**Analysis:**
- Resolution time trends (this year vs. last year)
- Issue volume trends
- Category shift patterns (more/less coordination issues)

### 4. Resource Planning
**Question:** "Which disciplines need more coordination time?"
**Analysis:**
- Issue count by discipline
- Complexity scores by discipline
- Multi-discipline involvement frequency

### 5. Quality Indicators
**Question:** "Which projects have the most critical issues?"
**Analysis:**
- High urgency + high complexity issues
- Open issue age distribution
- Recurring unresolved issues

## Technical Considerations

### Performance Optimization
1. **Indexing Strategy:**
   ```sql
   CREATE INDEX idx_processed_issues_project_status 
       ON ProcessedIssues(project_id, status) INCLUDE (primary_category_id);
   
   CREATE INDEX idx_processed_issues_dates 
       ON ProcessedIssues(created_at, closed_at);
   ```

2. **Caching:**
   - Cache category keywords in memory
   - Cache aggregated pain points (refresh hourly)

3. **Batch Processing:**
   - Process issues in chunks of 100
   - Use multi-threading for independent operations

### Data Quality
1. **Validation Rules:**
   - Title cannot be null or empty
   - Created_at must be before closed_at
   - Category assignments must be valid

2. **Monitoring:**
   - Track categorization confidence scores
   - Flag issues with low confidence for manual review
   - Log processing errors for investigation

### Integration Points
1. **ACC Import Handler:**
   - Trigger issue processing after ACC import
   - Update ProcessedIssues with latest data

2. **Revizto Integration:**
   - Extract comments from Revizto API
   - Map Revizto categories to system categories

3. **Reporting Export:**
   - Excel exports with charts
   - PDF summaries for client presentations

## Success Metrics

### Quantitative
- 90%+ of issues successfully categorized (primary category)
- Processing time: <1 second per issue
- Pain point calculations: <10 seconds per client/type combination
- User adoption: 70%+ of project managers use analytics monthly

### Qualitative
- Users report improved project planning
- Earlier identification of potential issues
- Better client communication (data-backed insights)
- Reduced time spent on manual issue review

## Future Enhancements (Post-Phase 5)

1. **Machine Learning:**
   - Train classification model on validated issues
   - Improve categorization accuracy over time
   - Predict issue resolution time based on characteristics

2. **Advanced Analytics:**
   - Root cause analysis (why do issues occur?)
   - Impact assessment (cost/schedule impact estimates)
   - Predictive modeling (forecast issues for new projects)

3. **Integration Expansion:**
   - Link to review cycles (issues discovered in which review?)
   - Connect to billing (issue resolution effort tracking)
   - Integration with BIM models (3D visualization of issues)

4. **Collaboration Features:**
   - Issue discussion threads within app
   - Assignment and tracking workflows
   - Notification system for critical issues

5. **AI Assistant:**
   - Natural language queries: "Show me hydraulic issues in Q2"
   - Automated report generation
   - Suggested actions based on patterns

## Appendix

### A. Sample Keywords by Category

**Hydraulic:**
- hydraulic, plumbing, pipework, drainage, water, sanitary, sewer, pump

**Electrical:**
- electrical, power, lighting, cable, conduit, switchboard, distribution

**Clash/Coordination:**
- clash, conflict, overlap, clearance, coordination, interference

**Clearance Issues:**
- clearance, <300mm, insufficient space, too close, tight

**Penetration:**
- penetration, peno, core, hole, sleeve, pass-through

### B. Reference Documents
- ACC API Documentation: Issue field mappings
- Revizto API Documentation: Issue and comment structures
- NLTK Documentation: Text processing functions
- Scikit-learn TF-IDF: Keyword extraction

### C. Testing Datasets
- Sample issues for each category (20 per category)
- Edge cases (multi-discipline, unclear issues)
- Historical issues with known categories for validation

---

**Document Version:** 1.0  
**Last Updated:** October 2, 2025  
**Author:** AI Assistant  
**Status:** Draft for Review
