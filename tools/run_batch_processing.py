"""
Run Batch Processing Script
============================

User-friendly command-line interface for the Issue Batch Processor.

Usage:
    # Process all unprocessed issues
    python tools/run_batch_processing.py
    
    # Process first 50 issues (test mode)
    python tools/run_batch_processing.py --limit 50
    
    # Process in larger batches
    python tools/run_batch_processing.py --batch-size 500
    
    # Process only new/updated issues since last run
    python tools/run_batch_processing.py --incremental
    
    # Quiet mode (minimal output)
    python tools/run_batch_processing.py --quiet
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.issue_batch_processor import IssueBatchProcessor
from database import connect_to_db
import argparse
from datetime import datetime


def print_header():
    """Print a nice header."""
    print("\n" + "="*70)
    print(" "*20 + "ISSUE BATCH PROCESSOR")
    print(" "*15 + "BIM Project Management System")
    print("="*70)


def get_database_stats():
    """Get current database statistics."""
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Total issues in view
        cursor.execute("SELECT COUNT(*) FROM vw_ProjectManagement_AllIssues")
        total_issues = cursor.fetchone()[0]
        
        # Processed issues
        cursor.execute("SELECT COUNT(*) FROM ProcessedIssues")
        processed_issues = cursor.fetchone()[0]
        
        # ACC vs Revizto breakdown
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM vw_ProjectManagement_AllIssues
            GROUP BY source
        """)
        source_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Processed breakdown
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM ProcessedIssues
            GROUP BY source
        """)
        processed_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Last processing run
        try:
            cursor.execute("""
                SELECT TOP 1 
                    batch_name, 
                    start_time, 
                    end_time, 
                    issues_processed, 
                    status
                FROM IssueProcessingLog
                ORDER BY start_time DESC
            """)
            last_run = cursor.fetchone()
        except:
            last_run = None
        
        return {
            'total_issues': total_issues,
            'processed_issues': processed_issues,
            'unprocessed_issues': total_issues - processed_issues,
            'source_breakdown': source_breakdown,
            'processed_breakdown': processed_breakdown,
            'last_run': last_run
        }
        
    finally:
        conn.close()


def print_stats(stats):
    """Print database statistics."""
    if stats is None:
        print("\n⚠️  Could not retrieve database statistics")
        return
    
    print("\n📊 DATABASE STATISTICS")
    print("-" * 70)
    print(f"Total Issues:           {stats['total_issues']:,}")
    print(f"Processed Issues:       {stats['processed_issues']:,}")
    print(f"Unprocessed Issues:     {stats['unprocessed_issues']:,}")
    
    if stats['unprocessed_issues'] > 0:
        pct = (stats['processed_issues'] / stats['total_issues']) * 100
        print(f"Completion:             {pct:.1f}%")
    
    print("\nSource Breakdown:")
    for source, count in stats['source_breakdown'].items():
        processed = stats['processed_breakdown'].get(source, 0)
        print(f"  {source:15s} {processed:,} / {count:,} processed")
    
    if stats['last_run']:
        print("\nLast Processing Run:")
        print(f"  Batch:      {stats['last_run'][0]}")
        print(f"  Started:    {stats['last_run'][1]}")
        print(f"  Ended:      {stats['last_run'][2]}")
        print(f"  Processed:  {stats['last_run'][3]:,} issues")
        print(f"  Status:     {stats['last_run'][4]}")
    
    print("-" * 70)


def confirm_processing(stats, args):
    """Ask user to confirm processing."""
    if args.yes:
        return True
    
    print(f"\n⚠️  You are about to process {stats['unprocessed_issues']:,} issues.")
    
    if args.limit:
        print(f"   (Limited to first {args.limit:,} issues)")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def print_category_distribution():
    """Print distribution of categories in processed issues."""
    conn = connect_to_db('ProjectManagement')
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        print("\n📈 CATEGORIZATION RESULTS")
        print("-" * 70)
        
        # Discipline distribution
        cursor.execute("""
            SELECT 
                c.category_name,
                COUNT(*) as count,
                AVG(pi.categorization_confidence) as avg_confidence
            FROM ProcessedIssues pi
            JOIN IssueCategories c ON pi.discipline_category_id = c.category_id
            WHERE c.category_level = 1
            GROUP BY c.category_name
            ORDER BY count DESC
        """)
        
        print("\nDiscipline Distribution:")
        total = 0
        for row in cursor.fetchall():
            print(f"  {row[0]:25s} {row[1]:5,} issues (avg confidence: {row[2]:.2f})")
            total += row[1]
        
        # Issue type distribution
        cursor.execute("""
            SELECT 
                c.category_name,
                COUNT(*) as count
            FROM ProcessedIssues pi
            JOIN IssueCategories c ON pi.primary_category_id = c.category_id
            WHERE c.category_level = 2
            GROUP BY c.category_name
            ORDER BY count DESC
        """)
        
        print("\nTop Issue Types:")
        for row in cursor.fetchall()[:10]:
            print(f"  {row[0]:35s} {row[1]:5,} issues")
        
        # Confidence distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN categorization_confidence >= 0.7 THEN 'Very High (≥0.7)'
                    WHEN categorization_confidence >= 0.5 THEN 'High (0.5-0.7)'
                    WHEN categorization_confidence >= 0.3 THEN 'Medium (0.3-0.5)'
                    ELSE 'Low (<0.3)'
                END as confidence_level,
                COUNT(*) as count,
                MAX(CASE 
                    WHEN categorization_confidence >= 0.7 THEN 4
                    WHEN categorization_confidence >= 0.5 THEN 3
                    WHEN categorization_confidence >= 0.3 THEN 2
                    ELSE 1
                END) as sort_order
            FROM ProcessedIssues
            GROUP BY 
                CASE 
                    WHEN categorization_confidence >= 0.7 THEN 'Very High (≥0.7)'
                    WHEN categorization_confidence >= 0.5 THEN 'High (0.5-0.7)'
                    WHEN categorization_confidence >= 0.3 THEN 'Medium (0.3-0.5)'
                    ELSE 'Low (<0.3)'
                END
            ORDER BY sort_order DESC
        """)
        
        print("\nConfidence Score Distribution:")
        for row in cursor.fetchall():
            pct = (row[1] / total) * 100 if total > 0 else 0
            print(f"  {row[0]:25s} {row[1]:5,} issues ({pct:5.1f}%)")
        
        # Sentiment distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN sentiment_score > 0.3 THEN 'Positive'
                    WHEN sentiment_score < -0.3 THEN 'Negative'
                    ELSE 'Neutral'
                END as sentiment,
                COUNT(*) as count,
                AVG(urgency_score) as avg_urgency
            FROM ProcessedIssues
            GROUP BY 
                CASE 
                    WHEN sentiment_score > 0.3 THEN 'Positive'
                    WHEN sentiment_score < -0.3 THEN 'Negative'
                    ELSE 'Neutral'
                END
        """)
        
        print("\nSentiment Analysis:")
        for row in cursor.fetchall():
            print(f"  {row[0]:15s} {row[1]:5,} issues (avg urgency: {row[2]:.2f})")
        
        print("-" * 70)
        
    finally:
        conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Batch process construction issues for categorization and analysis.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all unprocessed issues
  python tools/run_batch_processing.py
  
  # Test with first 50 issues
  python tools/run_batch_processing.py --limit 50
  
  # Process in larger batches for better performance
  python tools/run_batch_processing.py --batch-size 500
  
  # Process only new issues since last run
  python tools/run_batch_processing.py --incremental
  
  # Skip confirmation prompt
  python tools/run_batch_processing.py --yes
        """
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of issues to process in each batch (default: 100)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit total number of issues to process (for testing)'
    )
    
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Process only new/updated issues since last run'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (no progress updates)'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show statistics only, do not process'
    )
    
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Get and print database stats
    stats = get_database_stats()
    print_stats(stats)
    
    # Show category distribution if issues have been processed
    if stats and stats['processed_issues'] > 0:
        print_category_distribution()
    
    # Stats only mode
    if args.stats_only:
        print("\n✅ Statistics display complete.")
        return 0
    
    # Check if there's anything to process
    if stats and stats['unprocessed_issues'] == 0:
        print("\n✅ All issues have been processed!")
        print("\nTip: Use --incremental to process only new/updated issues")
        return 0
    
    # Confirm with user
    if not confirm_processing(stats, args):
        print("\n❌ Processing cancelled by user.")
        return 1
    
    # Initialize processor
    print("\n🚀 Initializing batch processor...")
    processor = IssueBatchProcessor()
    
    # Start processing
    print("\n" + "="*70)
    print("STARTING BATCH PROCESSING")
    print("="*70)
    print(f"Batch Size:     {args.batch_size}")
    if args.limit:
        print(f"Limit:          {args.limit:,} issues")
    print(f"Show Progress:  {'No' if args.quiet else 'Yes'}")
    print("="*70 + "\n")
    
    try:
        results = processor.process_all_issues(
            batch_size=args.batch_size,
            limit=args.limit,
            show_progress=not args.quiet
        )
        
        # Show final category distribution
        if results['successful'] > 0:
            print_category_distribution()
        
        print("\n✅ Batch processing completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user.")
        print(f"Processed {processor.stats['successful']} issues before interruption.")
        return 1
        
    except Exception as e:
        print(f"\n\n❌ Error during batch processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
