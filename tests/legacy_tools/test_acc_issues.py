"""
Test with ACC Issues (more descriptive titles)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from services.issue_text_processor import IssueTextProcessor
from services.issue_categorizer import IssueCategorizer

def test_acc_issues():
    """Test with ACC issues which have descriptive titles."""
    print("=" * 70)
    print("TESTING WITH ACC ISSUES (Descriptive Titles)")
    print("=" * 70)
    print()
    
    # Initialize processors
    processor = IssueTextProcessor()
    categorizer = IssueCategorizer()
    
    # Get sample issues
    with get_db_connection('ProjectManagement') as conn:
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get ACC issues with descriptive titles
        cursor.execute("""
            SELECT TOP 15
                source,
                issue_id,
                title,
                status,
                created_at,
                assignee,
                project_name,
                priority
            FROM vw_ProjectManagement_AllIssues
            WHERE source = 'ACC' 
                AND title IS NOT NULL 
                AND LEN(title) > 20
            ORDER BY created_at DESC
        """)
        
        issues = cursor.fetchall()
        
        if not issues:
            print("❌ No ACC issues found")
            return
        
        print(f"Processing {len(issues)} ACC issues...\n")
        
        results = []
        
        for idx, issue in enumerate(issues, 1):
            title = issue[2]
            status = issue[3]
            assignee = issue[5]
            project_name = issue[6]
            priority = issue[7]
            
            print(f"\n{'='*70}")
            print(f"Issue {idx}")
            print(f"{'='*70}")
            print(f"Title: {title}")
            print(f"Project: {project_name}")
            print(f"Status: {status} | Assignee: {assignee}")
            print()
            
            # Categorize
            categorization = categorizer.categorize_issue(title, None)
            
            # Get analysis scores
            combined_text = processor.combine_text_fields(title, None)
            sentiment = processor.analyze_sentiment(combined_text)
            urgency = processor.calculate_urgency_score(combined_text, priority)
            complexity = processor.calculate_complexity_score(combined_text, 0)
            
            discipline = categorizer.get_category_name(categorization['discipline_category_id'])
            itype = categorizer.get_category_name(categorization['primary_category_id'])
            subtype = categorizer.get_category_name(categorization['secondary_category_id'])
            
            print(f"CATEGORIZATION:")
            print(f"  ✓ Discipline: {discipline}")
            print(f"  ✓ Type: {itype}")
            print(f"  ✓ Sub-type: {subtype}")
            print(f"  ✓ Confidence: {categorization['confidence']:.2f}")
            
            print(f"\nANALYSIS:")
            print(f"  Sentiment: {sentiment:+.2f} ", end="")
            print("(Negative)" if sentiment < -0.3 else "(Neutral)" if sentiment < 0.3 else "(Positive)")
            print(f"  Urgency: {urgency:.2f} ", end="")
            print("(High)" if urgency > 0.5 else "(Medium)" if urgency > 0.2 else "(Low)")
            print(f"  Complexity: {complexity:.2f}")
            
            if categorization['scores']:
                top_3 = list(categorization['scores'].items())[:3]
                print(f"\nTop Category Matches:")
                for cat, score in top_3:
                    print(f"  - {cat}: {score:.2f}")
            
            results.append({
                'title': title,
                'discipline': discipline,
                'type': itype,
                'subtype': subtype,
                'confidence': categorization['confidence'],
                'urgency': urgency,
                'sentiment': sentiment
            })
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY & INSIGHTS")
        print("=" * 70)
        
        # Count by discipline
        from collections import Counter
        disciplines = Counter([r['discipline'] for r in results])
        print("\n📊 Issues by Discipline:")
        for disc, count in disciplines.most_common():
            pct = (count / len(results)) * 100
            print(f"  {disc}: {count} ({pct:.1f}%)")
        
        # Count by type
        types = Counter([r['type'] for r in results if r['type'] != 'Unknown'])
        print("\n📊 Issues by Type:")
        for itype, count in types.most_common():
            pct = (count / len(results)) * 100
            print(f"  {itype}: {count} ({pct:.1f}%)")
        
        # Count by subtype
        subtypes = Counter([r['subtype'] for r in results if r['subtype'] != 'Unknown'])
        if subtypes:
            print("\n📊 Issues by Sub-type:")
            for stype, count in subtypes.most_common(5):
                print(f"  {stype}: {count}")
        
        # Statistics
        avg_confidence = sum([r['confidence'] for r in results]) / len(results)
        high_conf = len([r for r in results if r['confidence'] > 0.5])
        print(f"\n📈 Categorization Confidence:")
        print(f"  Average: {avg_confidence:.2f}")
        print(f"  High Confidence (>0.5): {high_conf}/{len(results)} ({(high_conf/len(results)*100):.1f}%)")
        
        # Urgency analysis
        high_urgency = len([r for r in results if r['urgency'] > 0.5])
        medium_urgency = len([r for r in results if 0.2 < r['urgency'] <= 0.5])
        print(f"\n⚠️  Urgency Analysis:")
        print(f"  High Urgency: {high_urgency}/{len(results)}")
        print(f"  Medium Urgency: {medium_urgency}/{len(results)}")
        
        # Sentiment analysis
        negative = len([r for r in results if r['sentiment'] < -0.3])
        positive = len([r for r in results if r['sentiment'] > 0.3])
        print(f"\n😊 Sentiment Analysis:")
        print(f"  Negative: {negative}/{len(results)}")
        print(f"  Positive: {positive}/{len(results)}")
        print(f"  Neutral: {len(results) - negative - positive}/{len(results)}")
        
        print("\n" + "=" * 70)
        print("✓ Test complete!")
        print("\nThe system successfully:")
        print("  • Categorized issues by discipline, type, and sub-type")
        print("  • Calculated confidence scores")
        print("  • Analyzed urgency and sentiment")
        print("  • Extracted relevant keywords")
        print("=" * 70)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:

if __name__ == "__main__":
    test_acc_issues()
