"""
Test Issue Analytics with Real Data

Processes actual issues from the database and categorizes them.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_db
from services.issue_text_processor import IssueTextProcessor
from services.issue_categorizer import IssueCategorizer

def test_real_issues():
    """Test with real issues from the database."""
    print("=" * 70)
    print("TESTING WITH REAL ISSUES FROM DATABASE")
    print("=" * 70)
    print()
    
    # Initialize processors
    processor = IssueTextProcessor()
    categorizer = IssueCategorizer()
    
    # Get sample issues
    conn = connect_to_db('ProjectManagement')
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get 10 sample issues
        cursor.execute("""
            SELECT TOP 10
                source,
                issue_id,
                title,
                status,
                created_at,
                assignee,
                project_name,
                priority
            FROM vw_ProjectManagement_AllIssues
            WHERE title IS NOT NULL
            ORDER BY created_at DESC
        """)
        
        issues = cursor.fetchall()
        
        if not issues:
            print("❌ No issues found in database")
            return
        
        print(f"Processing {len(issues)} issues...\n")
        
        results = []
        
        for idx, issue in enumerate(issues, 1):
            source = issue[0]
            issue_id = issue[1]
            title = issue[2]
            status = issue[3]
            created_at = issue[4]
            assignee = issue[5]
            project_name = issue[6]
            priority = issue[7]
            
            print(f"\n{'='*70}")
            print(f"Issue {idx}: {title}")
            print(f"{'='*70}")
            print(f"Source: {source}")
            print(f"Project: {project_name}")
            print(f"Status: {status}")
            print(f"Assignee: {assignee}")
            print(f"Priority: {priority}")
            print()
            
            # Categorize
            categorization = categorizer.categorize_issue(title, None)
            
            # Get analysis scores
            combined_text = processor.combine_text_fields(title, None)
            sentiment = processor.analyze_sentiment(combined_text)
            urgency = processor.calculate_urgency_score(combined_text, priority)
            complexity = processor.calculate_complexity_score(combined_text, 0)
            
            print(f"CATEGORIZATION:")
            print(f"  Discipline: {categorizer.get_category_name(categorization['discipline_category_id'])}")
            print(f"  Type: {categorizer.get_category_name(categorization['primary_category_id'])}")
            print(f"  Sub-type: {categorizer.get_category_name(categorization['secondary_category_id'])}")
            print(f"  Confidence: {categorization['confidence']:.2f}")
            
            print(f"\nANALYSIS:")
            print(f"  Sentiment: {sentiment:.2f}")
            print(f"  Urgency: {urgency:.2f}")
            print(f"  Complexity: {complexity:.2f}")
            
            if categorization['scores']:
                top_3 = list(categorization['scores'].items())[:3]
                print(f"\nTop Scores: {', '.join([f'{cat}({score})' for cat, score in top_3])}")
            
            if categorization['extracted_keywords']:
                print(f"Keywords: {', '.join(categorization['extracted_keywords'][:5])}")
            
            results.append({
                'title': title,
                'discipline': categorizer.get_category_name(categorization['discipline_category_id']),
                'type': categorizer.get_category_name(categorization['primary_category_id']),
                'confidence': categorization['confidence'],
                'urgency': urgency
            })
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        # Count by discipline
        from collections import Counter
        disciplines = Counter([r['discipline'] for r in results])
        print("\nIssues by Discipline:")
        for disc, count in disciplines.most_common():
            print(f"  {disc}: {count}")
        
        # Count by type
        types = Counter([r['type'] for r in results])
        print("\nIssues by Type:")
        for itype, count in types.most_common():
            print(f"  {itype}: {count}")
        
        # Average confidence
        avg_confidence = sum([r['confidence'] for r in results]) / len(results)
        print(f"\nAverage Confidence: {avg_confidence:.2f}")
        
        # High urgency issues
        high_urgency = [r for r in results if r['urgency'] > 0.5]
        print(f"High Urgency Issues: {len(high_urgency)}/{len(results)}")
        
        print("\n" + "=" * 70)
        print("✓ Test complete!")
        print("=" * 70)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_real_issues()
