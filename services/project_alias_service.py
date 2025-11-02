"""
Project Alias Management Service

This module provides comprehensive tools for managing project aliases that map
internal project names to external system names (Revizto, ACC, etc.).

Key Features:
- CRUD operations for project aliases
- Auto-discovery of unmapped project names
- Validation and conflict detection  
- Bulk import/export capabilities
- Monitoring and reporting tools
"""

from database_pool import get_db_connection as _get_pool_connection
from database import connect_to_db
from constants import schema as S
import csv
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import os

class ProjectAliasManager:
    """Comprehensive project alias management system"""
    
    def __init__(self):
        self.conn = None
    
    def _get_connection(self):
        """Get database connection"""
        if not self.conn:
            self.conn = connect_to_db()
        return self.conn
    
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # ==================== CRUD Operations ====================
    
    def get_all_aliases(self) -> List[Dict]:
        """Get all project aliases with project details"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    pa.alias_name,
                    pa.pm_project_id,
                    p.project_name,
                    p.status,
                    p.project_manager,
                    p.created_at
                FROM project_aliases pa
                INNER JOIN projects p ON pa.pm_project_id = p.project_id
                ORDER BY p.project_name, pa.alias_name
            """)
            
            aliases = []
            for row in cursor.fetchall():
                aliases.append({
                    'alias_name': row[0],
                    'pm_project_id': row[1],
                    'project_name': row[2],
                    'project_status': row[3],
                    'project_manager': row[4],
                    'project_created': row[5]
                })
            
            return aliases
            
        except Exception as e:
            print(f"❌ Error fetching aliases: {e}")
            return []
    
    def add_alias(self, project_id: int, alias_name: str) -> bool:
        """Add a new alias for a project"""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if alias already exists
            cursor.execute("SELECT COUNT(*) FROM project_aliases WHERE alias_name = ?", (alias_name,))
            if cursor.fetchone()[0] > 0:
                print(f"⚠️ Alias '{alias_name}' already exists")
                return False
            
            # Check if project exists
            cursor.execute(f"SELECT COUNT(*) FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?", (project_id,))
            if cursor.fetchone()[0] == 0:
                print(f"⚠️ Project ID {project_id} does not exist")
                return False
            
            # Add the alias
            cursor.execute("""
                INSERT INTO project_aliases (alias_name, pm_project_id)
                VALUES (?, ?)
            """, (alias_name, project_id))
            
            conn.commit()
            print(f"✅ Added alias '{alias_name}' for project ID {project_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding alias: {e}")
            conn.rollback()
            return False
    
    def update_alias(self, old_alias_name: str, new_alias_name: str, new_project_id: Optional[int] = None) -> bool:
        """Update an existing alias"""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if old alias exists
            cursor.execute("SELECT pm_project_id FROM project_aliases WHERE alias_name = ?", (old_alias_name,))
            result = cursor.fetchone()
            if not result:
                print(f"⚠️ Alias '{old_alias_name}' not found")
                return False
            
            current_project_id = result[0]
            target_project_id = new_project_id if new_project_id is not None else current_project_id
            
            # Check if new alias name conflicts (only if changing name)
            if old_alias_name != new_alias_name:
                cursor.execute("SELECT COUNT(*) FROM project_aliases WHERE alias_name = ?", (new_alias_name,))
                if cursor.fetchone()[0] > 0:
                    print(f"⚠️ New alias name '{new_alias_name}' already exists")
                    return False
            
            # Update the alias
            cursor.execute("""
                UPDATE project_aliases 
                SET alias_name = ?, pm_project_id = ?
                WHERE alias_name = ?
            """, (new_alias_name, target_project_id, old_alias_name))
            
            conn.commit()
            print(f"✅ Updated alias '{old_alias_name}' to '{new_alias_name}' (Project ID: {target_project_id})")
            return True
            
        except Exception as e:
            print(f"❌ Error updating alias: {e}")
            conn.rollback()
            return False
    
    def delete_alias(self, alias_name: str) -> bool:
        """Delete an alias"""
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if alias exists
            cursor.execute("SELECT COUNT(*) FROM project_aliases WHERE alias_name = ?", (alias_name,))
            if cursor.fetchone()[0] == 0:
                print(f"⚠️ Alias '{alias_name}' not found")
                return False
            
            # Delete the alias
            cursor.execute("DELETE FROM project_aliases WHERE alias_name = ?", (alias_name,))
            
            conn.commit()
            print(f"✅ Deleted alias '{alias_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting alias: {e}")
            conn.rollback()
            return False
    
    # ==================== Auto-Discovery ====================
    
    def discover_unmapped_projects(self) -> List[Dict]:
        """Find project names in issues view that don't have aliases"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get all project names from issues view
            cursor.execute("SELECT DISTINCT project_name FROM vw_ProjectManagement_AllIssues")
            issue_projects = [row[0] for row in cursor.fetchall()]
            
            # Get all existing aliases
            cursor.execute("SELECT alias_name FROM project_aliases")
            existing_aliases = [row[0] for row in cursor.fetchall()]
            
            # Get main project names
            cursor.execute(f"SELECT {S.Projects.NAME} FROM {S.Projects.TABLE}")
            main_project_names = [row[0] for row in cursor.fetchall()]
            
            # Find unmapped projects
            all_mapped_names = set(existing_aliases + main_project_names)
            unmapped = []
            
            for project_name in issue_projects:
                if project_name not in all_mapped_names:
                    # Get issue count for this unmapped project
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_issues,
                            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_issues,
                            COUNT(DISTINCT source) as sources,
                            MIN(created_at) as first_issue,
                            MAX(created_at) as last_issue
                        FROM vw_ProjectManagement_AllIssues 
                        WHERE project_name = ?
                    """, (project_name,))
                    
                    stats = cursor.fetchone()
                    
                    unmapped.append({
                        'project_name': project_name,
                        'total_issues': stats[0],
                        'open_issues': stats[1],
                        'closed_issues': stats[0] - stats[1],
                        'sources': stats[2],
                        'first_issue_date': stats[3],
                        'last_issue_date': stats[4],
                        'suggested_match': self._suggest_project_match(project_name, main_project_names)
                    })
            
            return sorted(unmapped, key=lambda x: x['total_issues'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error discovering unmapped projects: {e}")
            return []
    
    def _suggest_project_match(self, unmapped_name: str, main_projects: List[str]) -> Optional[Dict]:
        """
        Enhanced project matching with multiple strategies:
        1. Project code extraction (P220702, MEL071)
        2. Abbreviation matching (CWPS ↔ Calderwood Primary School)
        3. Fuzzy string similarity
        4. File pattern recognition
        5. Substring matching (legacy)
        6. Word overlap analysis
        """
        import re
        from difflib import SequenceMatcher
        
        unmapped_lower = unmapped_name.lower()
        suggestions = []
        
        # Preprocess: Extract project codes from unmapped name
        unmapped_codes = self._extract_project_codes(unmapped_name)
        unmapped_abbrev = self._extract_abbreviations(unmapped_name)
        
        for main_project in main_projects:
            main_lower = main_project.lower()
            
            # Strategy 1: Project Code Matching (Highest Priority)
            # Match patterns like P220702, MEL071, CWPS001
            main_codes = self._extract_project_codes(main_project)
            if unmapped_codes and main_codes:
                if unmapped_codes & main_codes:  # Set intersection
                    suggestions.append({
                        'project_name': main_project,
                        'match_type': 'project_code',
                        'confidence': 0.95,
                        'matched_codes': list(unmapped_codes & main_codes)
                    })
                    continue
            
            # Strategy 2: Abbreviation Matching
            # Match CWPS → Calderwood Primary School, NFPS → North Fremantle PS
            if self._match_abbreviation(unmapped_name, main_project):
                suggestions.append({
                    'project_name': main_project,
                    'match_type': 'abbreviation',
                    'confidence': 0.88
                })
                continue
            
            # Strategy 3: Fuzzy String Similarity (Levenshtein-based)
            # Handles typos and variations
            # Also check against project name without prefix codes
            main_clean = re.sub(r'^(P\d{6}|[A-Z]{3,4}\d{3,4})\s+', '', main_project)
            similarity_full = SequenceMatcher(None, unmapped_lower, main_lower).ratio()
            similarity_clean = SequenceMatcher(None, unmapped_lower, main_clean.lower()).ratio()
            similarity = max(similarity_full, similarity_clean)
            
            if similarity > 0.70:
                suggestions.append({
                    'project_name': main_project,
                    'match_type': 'fuzzy_match',
                    'confidence': min(similarity, 0.92)  # Cap at 92% for fuzzy
                })
            
            # Strategy 4: Exact substring match (legacy behavior)
            if main_lower in unmapped_lower or unmapped_lower in main_lower:
                suggestions.append({
                    'project_name': main_project,
                    'match_type': 'substring',
                    'confidence': 0.85
                })
            
            # Strategy 5: Word overlap analysis (with stop-word filtering)
            unmapped_words = set(unmapped_lower.replace('[', ' ').replace(']', ' ').replace('-', ' ').split())
            main_words = set(main_lower.replace('-', ' ').split())
            
            # Remove common stop words to improve matching
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            unmapped_words = {w for w in unmapped_words if w not in stop_words and len(w) > 2}
            main_words = {w for w in main_words if w not in stop_words and len(w) > 2}
            
            common_words = unmapped_words.intersection(main_words)
            
            if common_words and len(common_words) >= 2:  # Require at least 2 matching words
                # Weight by word importance (longer words = higher weight)
                word_score = sum(len(w) for w in common_words) / sum(len(w) for w in main_words | unmapped_words)
                confidence = min(word_score * 1.2, 0.82)  # Cap at 82% for word matching
                
                suggestions.append({
                    'project_name': main_project,
                    'match_type': 'word_match',
                    'confidence': confidence,
                    'matched_words': list(common_words)
                })
        
        # Return best suggestion (highest confidence)
        if suggestions:
            best_match = max(suggestions, key=lambda x: x['confidence'])
            return best_match
        return None
    
    def _extract_project_codes(self, text: str) -> set:
        """
        Extract project codes from text:
        - P + 6 digits (e.g., P220702)
        - 3-4 letters + 3-4 digits (e.g., MEL071, CWPS001)
        - Standalone numbers with 4+ digits (e.g., 220702)
        """
        import re
        codes = set()
        
        # Pattern 1: P + 6 digits
        codes.update(re.findall(r'P\d{6}', text.upper()))
        
        # Pattern 2: 3-4 letters + 3-4 digits
        codes.update(re.findall(r'[A-Z]{3,4}\d{3,4}', text.upper()))
        
        # Pattern 3: Standalone 4-6 digit numbers (project IDs)
        codes.update(re.findall(r'\b\d{4,6}\b', text))
        
        return codes
    
    def _extract_abbreviations(self, text: str) -> str:
        """Extract uppercase abbreviations from text (e.g., CWPS, NFPS)"""
        import re
        # Find sequences of 3+ consecutive uppercase letters
        abbrevs = re.findall(r'\b[A-Z]{3,}\b', text)
        return ''.join(abbrevs)
    
    def _match_abbreviation(self, file_name: str, project_name: str) -> bool:
        """
        Match abbreviations like:
        - CWPS → Calderwood Primary School
        - NFPS → North Fremantle Primary School  
        - MCC → Melbourne Convention Centre (even if project is "P220702 Melbourne Convention Centre")
        Uses initials of capitalized words
        """
        import re
        
        # Remove project code prefix from project name to get clean name
        project_clean = re.sub(r'^(P\d{6}|[A-Z]{3,4}\d{3,4})\s+', '', project_name)
        
        # Extract capital letters from project name (initials)
        # Match words that start with capitals (including after spaces)
        project_words = re.findall(r'\b[A-Z][a-z]*', project_clean)
        if not project_words:
            return False
        
        # Create abbreviation from first letters
        project_abbrev = ''.join([w[0] for w in project_words])
        
        # Extract standalone abbreviations from file name (2+ consecutive uppercase)
        file_abbrevs = re.findall(r'\b[A-Z]{2,}\b', file_name)
        
        # Check if any file abbreviation matches project initials
        for file_abbrev in file_abbrevs:
            # Exact match
            if file_abbrev == project_abbrev:
                return True
            
            # File abbrev is prefix of project abbrev (at least 2 chars)
            if len(file_abbrev) >= 2 and len(project_abbrev) >= len(file_abbrev):
                if project_abbrev.startswith(file_abbrev):
                    return True
            
            # Project abbrev is prefix of file abbrev (at least 2 chars)
            if len(project_abbrev) >= 2 and len(file_abbrev) >= len(project_abbrev):
                if file_abbrev.startswith(project_abbrev):
                    return True
            
            # Handle common suffixes - match core part
            # NFPS vs NFPS (North Fremantle Primary School)
            if file_abbrev.endswith('PS') and project_abbrev.endswith('PS'):
                # Match if cores are similar
                file_core = file_abbrev[:-2]
                proj_core = project_abbrev[:-2]
                if len(file_core) >= 1 and len(proj_core) >= 1:
                    # Check if cores match or one contains the other
                    if file_core == proj_core or file_core in proj_core or proj_core in file_core:
                        return True
        
        return False
    
    # ==================== Validation & Monitoring ====================
    
    def validate_aliases_basic(self) -> Dict:
        """Basic alias validation without expensive queries"""
        conn = self._get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            validation_results = {
                'orphaned_aliases': [],
                'unused_projects': [],
                'total_aliases': 0,
                'total_projects_with_aliases': 0
            }
            
            # Get summary stats only (fast queries)
            cursor.execute("SELECT COUNT(*) FROM project_aliases")
            validation_results['total_aliases'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT pm_project_id) FROM project_aliases")
            validation_results['total_projects_with_aliases'] = cursor.fetchone()[0]
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Error validating aliases (basic): {e}")
            return {}
    
    def validate_aliases(self) -> Dict:
        """Validate all aliases and detect issues"""
        conn = self._get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            validation_results = {
                'orphaned_aliases': [],
                'duplicate_aliases': [],
                'unused_projects': [],
                'mapping_conflicts': [],
                'total_aliases': 0,
                'total_projects_with_aliases': 0
            }
            
            # Check for orphaned aliases (point to non-existent projects)
            cursor.execute("""
                SELECT pa.alias_name, pa.pm_project_id
                FROM project_aliases pa
                LEFT JOIN projects p ON pa.pm_project_id = p.project_id
                WHERE p.project_id IS NULL
            """)
            
            validation_results['orphaned_aliases'] = [
                {'alias_name': row[0], 'invalid_project_id': row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Check for duplicate aliases (shouldn't happen with constraints but let's verify)
            cursor.execute("""
                SELECT alias_name, COUNT(*) as count
                FROM project_aliases
                GROUP BY alias_name
                HAVING COUNT(*) > 1
            """)
            
            validation_results['duplicate_aliases'] = [
                {'alias_name': row[0], 'count': row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Check for projects without any aliases
            cursor.execute(f"""
                SELECT p.{S.Projects.ID}, p.{S.Projects.NAME}
                FROM {S.Projects.TABLE} p
                LEFT JOIN project_aliases pa ON p.{S.Projects.ID} = pa.pm_project_id
                WHERE pa.pm_project_id IS NULL
            """)
            
            validation_results['unused_projects'] = [
                {'project_id': row[0], 'project_name': row[1]} 
                for row in cursor.fetchall()
            ]
            
            # Get summary stats
            cursor.execute("SELECT COUNT(*) FROM project_aliases")
            validation_results['total_aliases'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT pm_project_id) FROM project_aliases")
            validation_results['total_projects_with_aliases'] = cursor.fetchone()[0]
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Error validating aliases: {e}")
            return {}
    
    def get_alias_usage_stats(self) -> List[Dict]:
        """Get statistics on how aliases are being used"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get alias usage statistics
            cursor.execute("""
                SELECT 
                    p.project_id,
                    p.project_name,
                    COUNT(pa.alias_name) as alias_count,
                    STRING_AGG(pa.alias_name, '; ') as aliases,
                    COALESCE(issue_stats.total_issues, 0) as total_issues,
                    COALESCE(issue_stats.open_issues, 0) as open_issues
                FROM projects p
                LEFT JOIN project_aliases pa ON p.project_id = pa.pm_project_id
                LEFT JOIN (
                    SELECT 
                        pa2.pm_project_id,
                        COUNT(*) as total_issues,
                        SUM(CASE WHEN vi.status = 'open' THEN 1 ELSE 0 END) as open_issues
                    FROM project_aliases pa2
                    INNER JOIN vw_ProjectManagement_AllIssues vi ON pa2.alias_name = vi.project_name
                    GROUP BY pa2.pm_project_id
                ) issue_stats ON p.project_id = issue_stats.pm_project_id
                GROUP BY p.project_id, p.project_name, issue_stats.total_issues, issue_stats.open_issues
                ORDER BY total_issues DESC, alias_count DESC
            """)
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'project_id': row[0],
                    'project_name': row[1],
                    'alias_count': row[2],
                    'aliases': row[3] if row[3] else '',
                    'total_issues': row[4],
                    'open_issues': row[5],
                    'has_issues': row[4] > 0
                })
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting usage stats: {e}")
            return []
    
    # ==================== Import/Export ====================
    
    def export_aliases_to_csv(self, filepath: str) -> bool:
        """Export all aliases to CSV file"""
        try:
            aliases = self.get_all_aliases()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['alias_name', 'pm_project_id', 'project_name', 'project_status', 'project_manager', 'project_created']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for alias in aliases:
                    writer.writerow(alias)
            
            print(f"✅ Exported {len(aliases)} aliases to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting aliases: {e}")
            return False
    
    def import_aliases_from_csv(self, filepath: str, update_existing: bool = False) -> Dict:
        """Import aliases from CSV file"""
        results = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            if not os.path.exists(filepath):
                results['errors'].append(f"File {filepath} not found")
                return results
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        alias_name = row.get('alias_name', '').strip()
                        pm_project_id = row.get('pm_project_id', '').strip()
                        
                        if not alias_name or not pm_project_id:
                            results['errors'].append(f"Row {row_num}: Missing alias_name or pm_project_id")
                            continue
                        
                        try:
                            pm_project_id = int(pm_project_id)
                        except ValueError:
                            results['errors'].append(f"Row {row_num}: Invalid project_id '{pm_project_id}'")
                            continue
                        
                        # Check if alias exists
                        conn = self._get_connection()
                        cursor = conn.cursor()
                        cursor.execute("SELECT pm_project_id FROM project_aliases WHERE alias_name = ?", (alias_name,))
                        existing = cursor.fetchone()
                        
                        if existing:
                            if update_existing and existing[0] != pm_project_id:
                                if self.update_alias(alias_name, alias_name, pm_project_id):
                                    results['updated'] += 1
                                else:
                                    results['errors'].append(f"Row {row_num}: Failed to update alias '{alias_name}'")
                            else:
                                results['skipped'] += 1
                        else:
                            if self.add_alias(pm_project_id, alias_name):
                                results['imported'] += 1
                            else:
                                results['errors'].append(f"Row {row_num}: Failed to import alias '{alias_name}'")
                    
                    except Exception as e:
                        results['errors'].append(f"Row {row_num}: {str(e)}")
            
            print(f"✅ Import complete: {results['imported']} imported, {results['updated']} updated, {results['skipped']} skipped")
            if results['errors']:
                print(f"⚠️ {len(results['errors'])} errors occurred")
            
            return results
            
        except Exception as e:
            results['errors'].append(f"File reading error: {str(e)}")
            return results


# ==================== Standalone Functions ====================

def get_project_alias_manager() -> ProjectAliasManager:
    """Get a new instance of the project alias manager"""
    return ProjectAliasManager()

def quick_add_alias(project_id: int, alias_name: str) -> bool:
    """Quick function to add an alias"""
    manager = ProjectAliasManager()
    result = manager.add_alias(project_id, alias_name)
    manager.close_connection()
    return result

def quick_discover_unmapped() -> List[Dict]:
    """Quick function to discover unmapped projects"""
    manager = ProjectAliasManager()
    result = manager.discover_unmapped_projects()
    manager.close_connection()
    return result

def quick_validate_aliases() -> Dict:
    """Quick function to validate aliases"""
    manager = ProjectAliasManager()
    result = manager.validate_aliases()
    manager.close_connection()
    return result