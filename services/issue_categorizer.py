"""
Issue Categorizer Service

Categorizes issues by matching text against keyword taxonomy.
Assigns discipline, primary type, and secondary type categories.
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from constants import schema as S
from services.issue_text_processor import IssueTextProcessor


class IssueCategorizer:
    """
    Categorizes issues using keyword matching against taxonomy.
    """
    
    def __init__(self):
        """Initialize categorizer and load category keywords."""
        self.text_processor = IssueTextProcessor()
        self.categories = {}  # category_id -> category info
        self.keywords = {}  # keyword -> [(category_id, weight), ...]
        self.load_categories()
        self.load_keywords()
    
    def load_categories(self):
        """Load category taxonomy from database."""
        with get_db_connection() as conn:
        if conn is None:
            print("❌ Failed to connect to database")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    category_id,
                    category_name,
                    parent_category_id,
                    category_level,
                    description
                FROM IssueCategories
                WHERE is_active = 1
                ORDER BY category_level, display_order
            """)
            
            for row in cursor.fetchall():
                self.categories[row[0]] = {
                    'id': row[0],
                    'name': row[1],
                    'parent_id': row[2],
                    'level': row[3],
                    'description': row[4]
                }
            
            print(f"✓ Loaded {len(self.categories)} categories")
        
        except Exception as e:
            print(f"❌ Error loading categories: {e}")
        
        finally:
    
    def load_keywords(self):
        """Load keyword mappings from database."""
        with get_db_connection() as conn:
        if conn is None:
            print("❌ Failed to connect to database")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    ick.keyword,
                    ick.category_id,
                    ick.weight
                FROM IssueCategoryKeywords ick
                JOIN IssueCategories ic ON ick.category_id = ic.category_id
                WHERE ick.is_active = 1 AND ic.is_active = 1
                ORDER BY ick.keyword
            """)
            
            for row in cursor.fetchall():
                keyword = row[0].lower()
                category_id = row[1]
                weight = float(row[2])
                
                if keyword not in self.keywords:
                    self.keywords[keyword] = []
                
                self.keywords[keyword].append((category_id, weight))
            
            print(f"✓ Loaded {len(self.keywords)} unique keywords")
        
        except Exception as e:
            print(f"❌ Error loading keywords: {e}")
        
        finally:
    
    def match_keywords(self, text: str) -> Dict[int, float]:
        """
        Match keywords in text and calculate category scores.
        
        Args:
            text: Cleaned and normalized text
            
        Returns:
            Dictionary of category_id -> score
        """
        if not text:
            return {}
        
        text = text.lower()
        scores = {}
        
        # Check each keyword
        for keyword, category_weights in self.keywords.items():
            # Count occurrences (including partial matches)
            count = text.count(keyword)
            
            if count > 0:
                # Add scores to relevant categories
                for category_id, weight in category_weights:
                    if category_id not in scores:
                        scores[category_id] = 0.0
                    
                    # Score = weight * min(count, 3) to avoid over-weighting repetition
                    scores[category_id] += weight * min(count, 3)
        
        return scores
    
    def get_parent_category(self, category_id: int) -> Optional[int]:
        """Get parent category ID."""
        if category_id in self.categories:
            return self.categories[category_id]['parent_id']
        return None
    
    def get_category_level(self, category_id: int) -> int:
        """Get category level (1, 2, or 3)."""
        if category_id in self.categories:
            return self.categories[category_id]['level']
        return 0
    
    def get_categories_by_level(self, level: int) -> List[int]:
        """Get all category IDs for a specific level."""
        return [cat_id for cat_id, cat in self.categories.items() if cat['level'] == level]
    
    def categorize_issue(self, title: str, description: Optional[str] = None,
                        comments: Optional[str] = None) -> Dict:
        """
        Categorize an issue based on text content.
        
        Args:
            title: Issue title
            description: Issue description
            comments: Issue comments (concatenated or latest)
            
        Returns:
            Dictionary with categorization results:
            {
                'discipline_category_id': int,
                'primary_category_id': int,
                'secondary_category_id': int,
                'confidence': float,
                'scores': dict,
                'extracted_keywords': list
            }
        """
        # Combine text fields
        combined_text = self.text_processor.combine_text_fields(title, description, comments)
        
        # Clean text
        cleaned_text = self.text_processor.clean_text(combined_text)
        
        # Extract keywords from issue
        issue_keywords = self.text_processor.extract_keywords(cleaned_text, top_n=10)
        
        # Match against category keywords
        scores = self.match_keywords(cleaned_text)
        
        if not scores:
            # No matches - return uncategorized
            other_cat_id = self._get_other_category_id()
            return {
                'discipline_category_id': other_cat_id,
                'primary_category_id': None,
                'secondary_category_id': None,
                'confidence': 0.0,
                'scores': {},
                'extracted_keywords': [kw for kw, _ in issue_keywords]
            }
        
        # Separate scores by category level
        level_1_scores = {cat_id: score for cat_id, score in scores.items() 
                         if self.get_category_level(cat_id) == 1}
        level_2_scores = {cat_id: score for cat_id, score in scores.items() 
                         if self.get_category_level(cat_id) == 2}
        level_3_scores = {cat_id: score for cat_id, score in scores.items() 
                         if self.get_category_level(cat_id) == 3}
        
        # Find best discipline (level 1)
        discipline_id = None
        discipline_score = 0.0
        if level_1_scores:
            discipline_id = max(level_1_scores.items(), key=lambda x: x[1])[0]
            discipline_score = level_1_scores[discipline_id]
        
        # Find best primary category (level 2)
        # Prefer categories that are children of the selected discipline
        primary_id = None
        primary_score = 0.0
        
        if discipline_id and level_2_scores:
            # Filter to children of discipline
            child_scores = {cat_id: score for cat_id, score in level_2_scores.items()
                           if self.get_parent_category(cat_id) == discipline_id}
            
            if child_scores:
                primary_id = max(child_scores.items(), key=lambda x: x[1])[0]
                primary_score = child_scores[primary_id]
            else:
                # No child matches, take highest scoring level 2
                primary_id = max(level_2_scores.items(), key=lambda x: x[1])[0]
                primary_score = level_2_scores[primary_id]
        
        # Find best secondary category (level 3)
        secondary_id = None
        secondary_score = 0.0
        
        if primary_id and level_3_scores:
            # Filter to children of primary category
            child_scores = {cat_id: score for cat_id, score in level_3_scores.items()
                           if self.get_parent_category(cat_id) == primary_id}
            
            if child_scores:
                secondary_id = max(child_scores.items(), key=lambda x: x[1])[0]
                secondary_score = child_scores[secondary_id]
        
        # Calculate confidence based on relative scores
        total_score = sum(scores.values())
        if total_score > 0:
            # Confidence based on how much the top categories dominate
            top_scores_sum = (discipline_score or 0) + (primary_score or 0) + (secondary_score or 0)
            confidence = min(1.0, top_scores_sum / total_score)
        else:
            confidence = 0.0
        
        # Adjust confidence based on number of keyword matches
        keyword_match_count = len([s for s in scores.values() if s > 0])
        if keyword_match_count < 3:
            confidence *= 0.7  # Lower confidence if few matches
        
        return {
            'discipline_category_id': discipline_id,
            'primary_category_id': primary_id,
            'secondary_category_id': secondary_id,
            'confidence': round(confidence, 2),
            'scores': {
                self.categories[cat_id]['name']: round(score, 2)
                for cat_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
                if cat_id in self.categories
            },
            'extracted_keywords': [kw for kw, _ in issue_keywords]
        }
    
    def batch_categorize(self, issues: List[Dict]) -> List[Dict]:
        """
        Categorize multiple issues.
        
        Args:
            issues: List of issue dictionaries with 'title', 'description', 'comments'
            
        Returns:
            List of categorization results
        """
        results = []
        
        for issue in issues:
            result = self.categorize_issue(
                issue.get('title'),
                issue.get('description'),
                issue.get('comments')
            )
            results.append(result)
        
        return results
    
    def _get_other_category_id(self) -> Optional[int]:
        """Get the 'Other/General' category ID."""
        for cat_id, cat in self.categories.items():
            if cat['name'] == 'Other/General' and cat['level'] == 1:
                return cat_id
        return None
    
    def get_category_name(self, category_id: Optional[int]) -> str:
        """Get category name by ID."""
        if category_id and category_id in self.categories:
            return self.categories[category_id]['name']
        return 'Unknown'
    
    def get_category_path(self, category_id: int) -> str:
        """
        Get full category path (e.g., 'Hydraulic/Plumbing > Clash/Coordination > Clearance Issue').
        
        Args:
            category_id: Category ID
            
        Returns:
            Full path string
        """
        if category_id not in self.categories:
            return 'Unknown'
        
        path = []
        current_id = category_id
        
        while current_id:
            cat = self.categories[current_id]
            path.insert(0, cat['name'])
            current_id = cat['parent_id']
        
        return ' > '.join(path)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Issue Categorizer - Test")
    print("=" * 70)
    print()
    
    # Initialize categorizer
    categorizer = IssueCategorizer()
    
    print(f"Categories loaded: {len(categorizer.categories)}")
    print(f"Keywords loaded: {len(categorizer.keywords)}")
    print()
    
    # Test examples
    test_issues = [
        {
            "title": "Hydraulic Issue - Hydraulic pipework clearance to civil drainage <300mm",
            "description": "The hydraulic pipework does not have sufficient clearance to the civil drainage system. Minimum 300mm clearance required."
        },
        {
            "title": "Electrical Issue - clash",
            "description": "Electrical conduit clashes with structural beam in Zone 5. Coordination required between electrical and structural teams."
        },
        {
            "title": "STR v. ELE - Peno misalignment",
            "description": "Electrical penetration through structural slab is misaligned by 150mm. Core hole needs to be relocated."
        },
        {
            "title": "HVAC ductwork missing information",
            "description": "Mechanical ductwork sizing not specified in drawings. RFI submitted to consultant."
        },
        {
            "title": "Fire sprinkler code compliance issue",
            "description": "Sprinkler head spacing exceeds maximum allowed by AS 2118. Requires additional heads."
        }
    ]
    
    print("Categorizing test issues...\n")
    
    for idx, issue in enumerate(test_issues, 1):
        print(f"Issue {idx}: {issue['title']}")
        print("-" * 70)
        
        result = categorizer.categorize_issue(
            issue['title'],
            issue.get('description')
        )
        
        print(f"Discipline: {categorizer.get_category_name(result['discipline_category_id'])}")
        print(f"Primary Type: {categorizer.get_category_name(result['primary_category_id'])}")
        print(f"Secondary Type: {categorizer.get_category_name(result['secondary_category_id'])}")
        print(f"Confidence: {result['confidence']:.2f}")
        
        if result['scores']:
            print(f"Top Scores: {', '.join([f'{cat}({score})' for cat, score in list(result['scores'].items())[:5]])}")
        
        print(f"Extracted Keywords: {', '.join(result['extracted_keywords'][:5])}")
        
        print()
    
    print("=" * 70)
    print("✓ Test complete")
