"""
Issue Analytics Service - Phase 4
Aggregates processed issues to identify pain points by client and project type

This service provides insights into:
- Main pain points by client
- Expected issues by project type
- Recurring issue patterns
- Trend analysis

Author: BIM Project Management System
Created: 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from config import Config
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueAnalyticsService:
    """
    Service for aggregating issue analytics to identify pain points
    and patterns by client and project type.
    """
    
    def __init__(self, db_name: str = None):
        """
        Initialize the analytics service.
        
        Args:
            db_name: Database name to connect to (default: ProjectManagement)
        """
        self.db_name = db_name or Config.PROJECT_MGMT_DB
        logger.info(f"Initialized IssueAnalyticsService for database: {self.db_name}")
    
    def calculate_pain_points_by_project(self) -> List[Dict]:
        """
        Calculate pain points aggregated by project.
        
        Returns:
            List of dictionaries with project pain point metrics
        """
        conn = connect_to_db(self.db_name)
        if conn is None:
            logger.error("Failed to connect to database")
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ai.project_name,
                    ai.source,
                    -- Issue counts
                    COUNT(DISTINCT pi.processed_issue_id) as total_issues,
                    COUNT(DISTINCT CASE WHEN pi.status = 'open' THEN pi.processed_issue_id END) as open_issues,
                    COUNT(DISTINCT CASE WHEN pi.status = 'closed' THEN pi.processed_issue_id END) as closed_issues,
                    
                    -- Discipline breakdown
                    COUNT(DISTINCT CASE WHEN disc.category_name = 'Electrical' THEN pi.processed_issue_id END) as electrical_issues,
                    COUNT(DISTINCT CASE WHEN disc.category_name = 'Hydraulic/Plumbing' THEN pi.processed_issue_id END) as hydraulic_issues,
                    COUNT(DISTINCT CASE WHEN disc.category_name = 'Mechanical (HVAC)' THEN pi.processed_issue_id END) as mechanical_issues,
                    COUNT(DISTINCT CASE WHEN disc.category_name = 'Structural' THEN pi.processed_issue_id END) as structural_issues,
                    COUNT(DISTINCT CASE WHEN disc.category_name = 'Architectural' THEN pi.processed_issue_id END) as architectural_issues,
                    
                    -- Top issue types
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Clash%' THEN pi.processed_issue_id END) as clash_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Information%' THEN pi.processed_issue_id END) as info_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Design%' THEN pi.processed_issue_id END) as design_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Constructability%' THEN pi.processed_issue_id END) as constructability_issues,
                    
                    -- Scoring metrics
                    AVG(pi.urgency_score) as avg_urgency,
                    AVG(pi.complexity_score) as avg_complexity,
                    AVG(pi.categorization_confidence) as avg_confidence,
                    AVG(pi.sentiment_score) as avg_sentiment,
                    
                    -- Resolution metrics
                    AVG(CASE 
                        WHEN pi.closed_at IS NOT NULL AND pi.created_at IS NOT NULL 
                        THEN DATEDIFF(day, pi.created_at, pi.closed_at)
                        ELSE NULL 
                    END) as avg_resolution_days,
                    
                    -- Priority distribution
                    COUNT(DISTINCT CASE WHEN pi.priority IN ('critical', 'high') THEN pi.processed_issue_id END) as high_priority_count,
                    COUNT(DISTINCT CASE WHEN pi.priority IN ('low', 'minor') THEN pi.processed_issue_id END) as low_priority_count
                    
                FROM ProcessedIssues pi
                INNER JOIN vw_ProjectManagement_AllIssues ai 
                    ON pi.source_issue_id = CAST(ai.issue_id AS NVARCHAR(255)) 
                    AND pi.source = ai.source
                LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                WHERE pi.processed_at IS NOT NULL
                GROUP BY ai.project_name, ai.source
                HAVING COUNT(DISTINCT pi.processed_issue_id) > 0
                ORDER BY total_issues DESC
            """
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                
                # Calculate pain point score (weighted metric)
                # Higher urgency, complexity, and open issue ratio = higher pain
                open_ratio = (result['open_issues'] / result['total_issues']) if result['total_issues'] > 0 else 0
                result['pain_point_score'] = (
                    float(result['avg_urgency'] or 0) * 0.3 +
                    float(result['avg_complexity'] or 0) * 0.3 +
                    open_ratio * 0.4
                )
                
                # Calculate issue density (issues per project)
                result['issue_density'] = result['total_issues']
                
                results.append(result)
            
            logger.info(f"Calculated pain points for {len(results)} projects")
            return results
            
        except Exception as e:
            logger.error(f"Error calculating project pain points: {e}")
            return []
        finally:
            conn.close()
    
    def calculate_pain_points_by_discipline(self) -> List[Dict]:
        """
        Calculate pain points aggregated by discipline.
        
        Returns:
            List of dictionaries with discipline pain point metrics
        """
        conn = connect_to_db(self.db_name)
        if conn is None:
            logger.error("Failed to connect to database")
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COALESCE(disc.category_name, 'Unknown') as discipline,
                    -- Issue counts
                    COUNT(DISTINCT pi.processed_issue_id) as total_issues,
                    COUNT(DISTINCT CASE WHEN pi.status = 'open' THEN pi.processed_issue_id END) as open_issues,
                    COUNT(DISTINCT CASE WHEN pi.status = 'closed' THEN pi.processed_issue_id END) as closed_issues,
                    COUNT(DISTINCT ai.project_name) as project_count,
                    
                    -- Top issue types within discipline
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Clash%' THEN pi.processed_issue_id END) as clash_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Information%' THEN pi.processed_issue_id END) as info_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Design%' THEN pi.processed_issue_id END) as design_issues,
                    COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Constructability%' THEN pi.processed_issue_id END) as constructability_issues,
                    
                    -- Scoring metrics
                    AVG(pi.urgency_score) as avg_urgency,
                    AVG(pi.complexity_score) as avg_complexity,
                    AVG(pi.categorization_confidence) as avg_confidence,
                    AVG(pi.sentiment_score) as avg_sentiment,
                    
                    -- Resolution metrics
                    AVG(CASE 
                        WHEN pi.closed_at IS NOT NULL AND pi.created_at IS NOT NULL 
                        THEN DATEDIFF(day, pi.created_at, pi.closed_at)
                        ELSE NULL 
                    END) as avg_resolution_days,
                    
                    -- Priority distribution
                    COUNT(DISTINCT CASE WHEN pi.priority IN ('critical', 'high') THEN pi.processed_issue_id END) as high_priority_count,
                    COUNT(DISTINCT CASE WHEN pi.priority IN ('low', 'minor') THEN pi.processed_issue_id END) as low_priority_count
                    
                FROM ProcessedIssues pi
                INNER JOIN vw_ProjectManagement_AllIssues ai 
                    ON pi.source_issue_id = CAST(ai.issue_id AS NVARCHAR(255)) 
                    AND pi.source = ai.source
                LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                WHERE pi.processed_at IS NOT NULL
                GROUP BY COALESCE(disc.category_name, 'Unknown')
                HAVING COUNT(DISTINCT pi.processed_issue_id) > 0
                ORDER BY total_issues DESC
            """
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                
                # Calculate pain point score
                open_ratio = (result['open_issues'] / result['total_issues']) if result['total_issues'] > 0 else 0
                result['pain_point_score'] = (
                    float(result['avg_urgency'] or 0) * 0.3 +
                    float(result['avg_complexity'] or 0) * 0.3 +
                    open_ratio * 0.4
                )
                
                # Calculate issue density (issues per project)
                result['issues_per_project'] = (
                    result['total_issues'] / result['project_count'] 
                    if result['project_count'] > 0 else 0
                )
                
                results.append(result)
            
            logger.info(f"Calculated pain points for {len(results)} disciplines")
            return results
            
        except Exception as e:
            logger.error(f"Error calculating discipline pain points: {e}")
            return []
        finally:
            conn.close()
    
    def identify_recurring_patterns(self, similarity_threshold: float = 0.8) -> List[Dict]:
        """
        Identify recurring issue patterns using title similarity.
        
        Args:
            similarity_threshold: Minimum similarity score to consider issues similar
            
        Returns:
            List of recurring pattern clusters
        """
        conn = connect_to_db(self.db_name)
        if conn is None:
            logger.error("Failed to connect to database")
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get issues with their keywords for similarity analysis
            query = """
                SELECT 
                    pi.processed_issue_id,
                    pi.title,
                    pi.extracted_keywords,
                    pi.project_id,
                    disc.category_name as discipline,
                    prim.category_name as issue_type,
                    COUNT(*) as occurrence_count
                FROM ProcessedIssues pi
                LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                WHERE pi.extracted_keywords IS NOT NULL 
                    AND pi.extracted_keywords != ''
                GROUP BY 
                    pi.processed_issue_id,
                    pi.title,
                    pi.extracted_keywords,
                    pi.project_id,
                    disc.category_name,
                    prim.category_name
                HAVING COUNT(*) >= 1
                ORDER BY occurrence_count DESC
            """
            
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            issues = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Simple keyword-based clustering
            # Group issues by common keywords
            keyword_clusters = {}
            for issue in issues:
                keywords = set(issue['extracted_keywords'].lower().split(','))
                keywords = {kw.strip() for kw in keywords if kw.strip()}
                
                # Find or create cluster
                matched_cluster = None
                for cluster_keywords, cluster_issues in keyword_clusters.items():
                    # Calculate Jaccard similarity
                    intersection = keywords & cluster_keywords
                    union = keywords | cluster_keywords
                    similarity = len(intersection) / len(union) if union else 0
                    
                    if similarity >= similarity_threshold:
                        matched_cluster = cluster_keywords
                        break
                
                if matched_cluster:
                    keyword_clusters[matched_cluster].append(issue)
                else:
                    keyword_clusters[frozenset(keywords)] = [issue]
            
            # Format results for clusters with 3+ issues
            recurring_patterns = []
            for keywords, cluster_issues in keyword_clusters.items():
                if len(cluster_issues) >= 3:
                    # Aggregate metrics for this pattern
                    disciplines = {}
                    issue_types = {}
                    projects = set()
                    
                    for issue in cluster_issues:
                        disc = issue['discipline'] or 'Unknown'
                        itype = issue['issue_type'] or 'Unknown'
                        
                        disciplines[disc] = disciplines.get(disc, 0) + 1
                        issue_types[itype] = issue_types.get(itype, 0) + 1
                        projects.add(issue['project_id'])
                    
                    # Get most common discipline and issue type
                    top_discipline = max(disciplines.items(), key=lambda x: x[1]) if disciplines else ('Unknown', 0)
                    top_issue_type = max(issue_types.items(), key=lambda x: x[1]) if issue_types else ('Unknown', 0)
                    
                    pattern = {
                        'pattern_id': len(recurring_patterns) + 1,
                        'common_keywords': ', '.join(sorted(keywords)[:5]),  # Top 5 keywords
                        'occurrence_count': len(cluster_issues),
                        'project_count': len(projects),
                        'top_discipline': top_discipline[0],
                        'discipline_count': top_discipline[1],
                        'top_issue_type': top_issue_type[0],
                        'issue_type_count': top_issue_type[1],
                        'example_titles': [issue['title'] for issue in cluster_issues[:3]]
                    }
                    recurring_patterns.append(pattern)
            
            # Sort by occurrence count
            recurring_patterns.sort(key=lambda x: x['occurrence_count'], reverse=True)
            
            logger.info(f"Identified {len(recurring_patterns)} recurring patterns")
            return recurring_patterns
            
        except Exception as e:
            logger.error(f"Error identifying recurring patterns: {e}")
            return []
        finally:
            conn.close()
    
    def get_top_pain_points_summary(self, top_n: int = 10) -> Dict:
        """
        Get a comprehensive summary of top pain points across all dimensions.
        
        Args:
            top_n: Number of top items to return for each dimension
            
        Returns:
            Dictionary with top pain points by various dimensions
        """
        logger.info("Generating comprehensive pain points summary...")
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'by_project': self.calculate_pain_points_by_project()[:top_n],
            'by_discipline': self.calculate_pain_points_by_discipline()[:top_n],
            'recurring_patterns': self.identify_recurring_patterns()[:top_n]
        }
        
        return summary
    
    def populate_pain_points_table(self):
        """
        Populate the IssuePainPoints table with aggregated analytics.
        This provides a persistent store of pain point metrics.
        """
        conn = connect_to_db(self.db_name)
        if conn is None:
            logger.error("Failed to connect to database")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM IssuePainPoints")
            logger.info("Cleared existing pain points data")
            
            # Insert client-level pain points
            client_pain_points = self.calculate_pain_points_by_client()
            for cp in client_pain_points:
                cursor.execute("""
                    INSERT INTO IssuePainPoints (
                        aggregation_level, aggregation_key, aggregation_label,
                        total_issues, open_issues, closed_issues,
                        electrical_issues, hydraulic_issues, mechanical_issues,
                        structural_issues, architectural_issues,
                        clash_issues, info_issues, design_issues,
                        avg_urgency_score, avg_complexity_score, avg_confidence_score,
                        avg_resolution_days, pain_point_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'client',
                    str(cp['client_id']),
                    cp['client_name'],
                    cp['total_issues'],
                    cp['open_issues'],
                    cp['closed_issues'],
                    cp['electrical_issues'],
                    cp['hydraulic_issues'],
                    cp['mechanical_issues'],
                    cp['structural_issues'],
                    cp['architectural_issues'],
                    cp['clash_issues'],
                    cp['info_issues'],
                    cp['design_issues'],
                    cp['avg_urgency'],
                    cp['avg_complexity'],
                    cp['avg_confidence'],
                    cp['avg_resolution_days'],
                    cp['pain_point_score']
                ))
            
            logger.info(f"Inserted {len(client_pain_points)} client pain point records")
            
            # Insert project type pain points
            type_pain_points = self.calculate_pain_points_by_project_type()
            for tp in type_pain_points:
                cursor.execute("""
                    INSERT INTO IssuePainPoints (
                        aggregation_level, aggregation_key, aggregation_label,
                        total_issues, open_issues, closed_issues,
                        electrical_issues, hydraulic_issues, mechanical_issues,
                        structural_issues, architectural_issues,
                        clash_issues, info_issues, design_issues,
                        avg_urgency_score, avg_complexity_score, avg_confidence_score,
                        avg_resolution_days, pain_point_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'project_type',
                    tp['project_type'] or 'unknown',
                    tp['project_type'] or 'Unknown',
                    tp['total_issues'],
                    tp['open_issues'],
                    tp['closed_issues'],
                    tp['electrical_issues'],
                    tp['hydraulic_issues'],
                    tp['mechanical_issues'],
                    tp['structural_issues'],
                    tp['architectural_issues'],
                    tp['clash_issues'],
                    tp['info_issues'],
                    tp['design_issues'],
                    tp['avg_urgency'],
                    tp['avg_complexity'],
                    tp['avg_confidence'],
                    tp['avg_resolution_days'],
                    tp['pain_point_score']
                ))
            
            logger.info(f"Inserted {len(type_pain_points)} project type pain point records")
            
            conn.commit()
            logger.info("Successfully populated IssuePainPoints table")
            return True
            
        except Exception as e:
            logger.error(f"Error populating pain points table: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


if __name__ == "__main__":
    # Test the service
    service = IssueAnalyticsService()
    
    print("\n" + "="*80)
    print("ISSUE ANALYTICS SERVICE - TEST")
    print("="*80)
    
    # Test project pain points
    print("\n📊 PROJECT PAIN POINTS")
    print("-" * 80)
    project_pain_points = service.calculate_pain_points_by_project()
    for i, pp in enumerate(project_pain_points[:5], 1):
        print(f"\n{i}. {pp['project_name']} ({pp['source']})")
        print(f"   Total Issues: {pp['total_issues']} (Open: {pp['open_issues']}, Closed: {pp['closed_issues']})")
        print(f"   Pain Score: {pp['pain_point_score']:.2f}")
        print(f"   Top Disciplines: Electrical={pp['electrical_issues']}, Hydraulic={pp['hydraulic_issues']}, Mechanical={pp['mechanical_issues']}")
        print(f"   Avg Resolution: {pp['avg_resolution_days']:.1f} days" if pp['avg_resolution_days'] else "   Avg Resolution: N/A")
    
    # Test discipline pain points
    print("\n\n🏗️ DISCIPLINE PAIN POINTS")
    print("-" * 80)
    disc_pain_points = service.calculate_pain_points_by_discipline()
    for i, dp in enumerate(disc_pain_points[:5], 1):
        print(f"\n{i}. {dp['discipline']}")
        print(f"   Total Issues: {dp['total_issues']} across {dp['project_count']} projects")
        print(f"   Issues per Project: {dp['issues_per_project']:.1f}")
        print(f"   Pain Score: {dp['pain_point_score']:.2f}")
        print(f"   Top Issues: Clash={dp['clash_issues']}, Info={dp['info_issues']}, Design={dp['design_issues']}")
    
    # Test recurring patterns
    print("\n\n🔄 RECURRING PATTERNS")
    print("-" * 80)
    patterns = service.identify_recurring_patterns()
    for i, pattern in enumerate(patterns[:5], 1):
        print(f"\n{i}. Pattern #{pattern['pattern_id']}")
        print(f"   Keywords: {pattern['common_keywords']}")
        print(f"   Occurrences: {pattern['occurrence_count']} across {pattern['project_count']} projects")
        print(f"   Top Discipline: {pattern['top_discipline']}")
        print(f"   Top Issue Type: {pattern['top_issue_type']}")
        print(f"   Example: {pattern['example_titles'][0][:80]}...")
    
    print("\n\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
