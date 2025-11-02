"""
Optimized Project Alias Service with performance improvements

Key optimizations:
1. Single-query unmapped discovery
2. Cached main project names
3. Lightweight summary endpoint
4. Batch operations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.project_alias_service import ProjectAliasManager
from constants import schema as S

class OptimizedProjectAliasManager(ProjectAliasManager):
    """Performance-optimized version of ProjectAliasManager"""
    
    def get_summary_quick(self):
        """Ultra-fast summary - just counts, no heavy processing"""
        conn = self._get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Single query for all counts
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM project_aliases) as total_aliases,
                    (SELECT COUNT(DISTINCT pm_project_id) FROM project_aliases) as projects_with_aliases,
                    (SELECT COUNT(*) FROM projects) as total_projects
            """)
            
            row = cursor.fetchone()
            
            return {
                'total_aliases': row[0],
                'projects_with_aliases': row[1],
                'total_projects': row[2],
                'unmapped_count': None  # Load on demand
            }
        
        except Exception as e:
            print(f"❌ Error getting quick summary: {e}")
            return {}
    
    def discover_unmapped_optimized(self):
        """Optimized unmapped discovery with single query"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Single query to get unmapped projects with stats
            cursor.execute("""
                WITH AllMappedNames AS (
                    -- Existing aliases
                    SELECT alias_name as name FROM project_aliases
                    UNION
                    -- Main project names
                    SELECT project_name as name FROM projects
                ),
                UnmappedProjects AS (
                    SELECT DISTINCT vi.project_name
                    FROM vw_ProjectManagement_AllIssues vi
                    WHERE vi.project_name IS NOT NULL
                        AND vi.project_name NOT IN (SELECT name FROM AllMappedNames)
                )
                SELECT 
                    up.project_name,
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN vi.status = 'open' THEN 1 ELSE 0 END) as open_issues,
                    COUNT(DISTINCT vi.source) as sources,
                    MIN(vi.created_at) as first_issue,
                    MAX(vi.created_at) as last_issue
                FROM UnmappedProjects up
                INNER JOIN vw_ProjectManagement_AllIssues vi ON up.project_name = vi.project_name
                GROUP BY up.project_name
                ORDER BY COUNT(*) DESC
            """)
            
            # Get main project names once
            cursor.execute(f"SELECT {S.Projects.NAME} FROM {S.Projects.TABLE}")
            main_project_names = [row[0] for row in cursor.fetchall()]
            
            unmapped = []
            for row in cursor.fetchall():
                unmapped.append({
                    'project_name': row[0],
                    'total_issues': row[1],
                    'open_issues': row[2],
                    'closed_issues': row[1] - row[2],
                    'sources': row[3],
                    'first_issue_date': row[4],
                    'last_issue_date': row[5],
                    'suggested_match': self._suggest_project_match(row[0], main_project_names)
                })
            
            return unmapped
        
        except Exception as e:
            print(f"❌ Error discovering unmapped projects (optimized): {e}")
            return []


def run_matching_analysis():
    """
    Run the enhanced matching analysis (from test script)
    Returns analysis results for display in UI
    """
    manager = OptimizedProjectAliasManager()
    
    try:
        unmapped = manager.discover_unmapped_optimized()
        
        if not unmapped:
            return {
                'summary': {
                    'total_unmapped': 0,
                    'high_confidence': 0,
                    'medium_confidence': 0,
                    'low_confidence': 0,
                    'no_suggestion': 0
                },
                'recommendations': [],
                'unmapped_details': []
            }
        
        # Categorize by confidence
        high_confidence = []
        medium_confidence = []
        low_confidence = []
        no_suggestion = []
        
        for item in unmapped:
            suggestion = item.get('suggested_match')
            if not suggestion:
                no_suggestion.append(item)
            elif suggestion['confidence'] >= 0.85:
                high_confidence.append(item)
            elif suggestion['confidence'] >= 0.70:
                medium_confidence.append(item)
            else:
                low_confidence.append(item)
        
        # Build recommendations
        recommendations = []
        for item in sorted(high_confidence, key=lambda x: x['suggested_match']['confidence'], reverse=True)[:10]:
            sugg = item['suggested_match']
            recommendations.append({
                'alias_name': item['project_name'],
                'suggested_project': sugg['project_name'],
                'confidence': sugg['confidence'],
                'match_type': sugg['match_type'],
                'total_issues': item['total_issues'],
                'open_issues': item['open_issues']
            })
        
        return {
            'summary': {
                'total_unmapped': len(unmapped),
                'high_confidence': len(high_confidence),
                'medium_confidence': len(medium_confidence),
                'low_confidence': len(low_confidence),
                'no_suggestion': len(no_suggestion)
            },
            'recommendations': recommendations,
            'unmapped_details': unmapped
        }
    
    finally:
        manager.close_connection()
