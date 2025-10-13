"""
Issue Batch Processor Service
==============================

Processes large batches of issues from the database, categorizing them and storing results.

Features:
- Batch processing with progress tracking
- Incremental processing (only new/updated issues)
- Error handling and retry logic
- Performance optimization with batching
- Detailed logging and statistics

Usage:
    processor = IssueBatchProcessor()
    results = processor.process_all_issues(batch_size=100)
    print(f"Processed {results['total_processed']} issues")
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection
from services.issue_text_processor import IssueTextProcessor
from services.issue_categorizer import IssueCategorizer
from datetime import datetime
import time


class IssueBatchProcessor:
    """Batch processes issues for categorization and analysis."""
    
    def __init__(self, db_name='ProjectManagement'):
        """
        Initialize the batch processor.
        
        Args:
            db_name: Name of the database to connect to
        """
        self.db_name = db_name
        self.text_processor = IssueTextProcessor()
        self.categorizer = IssueCategorizer()
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'start_time': None,
            'end_time': None
        }
        
    def get_unprocessed_issues(self, limit=None):
        """
        Retrieve issues that haven't been processed yet.
        
        Args:
            limit: Optional limit on number of issues to retrieve
            
        Returns:
            List of issue dictionaries
        """
        with get_db_connection(self.db_name) as conn:
        if conn is None:
            raise Exception("Failed to connect to database")
            
        try:
            cursor = conn.cursor()
            
            # Query to get unprocessed issues from the combined view
            # Build query with optional limit
            if limit:
                query = f"""
                    SELECT TOP {limit}
                        i.issue_id,
                        i.project_id,
                        i.title,
                        i.priority,
                        i.status,
                        i.source,
                        i.created_at,
                        i.closed_at,
                        i.assignee,
                        i.author,
                        i.project_name
                    FROM vw_ProjectManagement_AllIssues i
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM ProcessedIssues pi 
                        WHERE CAST(pi.source_issue_id AS NVARCHAR(255)) = CAST(i.issue_id AS NVARCHAR(255))
                        AND pi.source = i.source
                    )
                    ORDER BY i.created_at DESC
                """
            else:
                query = """
                    SELECT 
                        i.issue_id,
                        i.project_id,
                        i.title,
                        i.priority,
                        i.status,
                        i.source,
                        i.created_at,
                        i.closed_at,
                        i.assignee,
                        i.author,
                        i.project_name
                    FROM vw_ProjectManagement_AllIssues i
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM ProcessedIssues pi 
                        WHERE CAST(pi.source_issue_id AS NVARCHAR(255)) = CAST(i.issue_id AS NVARCHAR(255))
                        AND pi.source = i.source
                    )
                    ORDER BY i.created_at DESC
                """
            
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            issues = []
            
            for row in cursor.fetchall():
                issue = dict(zip(columns, row))
                issues.append(issue)
            
            return issues
            
        finally:
    
    def get_updated_issues(self, since_date=None):
        """
        Retrieve issues that have been updated since last processing.
        
        Args:
            since_date: Only get issues updated after this date
            
        Returns:
            List of issue dictionaries
        """
        with get_db_connection(self.db_name) as conn:
        if conn is None:
            raise Exception("Failed to connect to database")
            
        try:
            cursor = conn.cursor()
            
            # Get last processing date if not provided
            if since_date is None:
                cursor.execute("""
                    SELECT MAX(end_time) 
                    FROM IssueProcessingLog 
                    WHERE status = 'completed'
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    since_date = result[0]
                else:
                    # If no previous processing, get all issues
                    return self.get_unprocessed_issues()
            
            # Query for updated issues
            query = """
                SELECT 
                    i.issue_id,
                    i.project_id,
                    i.title,
                    i.priority,
                    i.status,
                    i.source,
                    i.created_at,
                    i.closed_at,
                    i.assignee,
                    i.author,
                    i.project_name
                FROM vw_ProjectManagement_AllIssues i
                WHERE i.created_at > ? OR i.closed_at > ?
                ORDER BY i.created_at DESC
            """
            
            cursor.execute(query, (since_date, since_date))
            columns = [column[0] for column in cursor.description]
            issues = []
            
            for row in cursor.fetchall():
                issue = dict(zip(columns, row))
                issues.append(issue)
            
            return issues
            
        finally:
    
    def process_issue(self, issue):
        """
        Process a single issue through the categorization pipeline.
        
        Args:
            issue: Issue dictionary with required fields
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract text for processing
            title = issue.get('title', '')
            description = ''  # No description in current view
            combined_text = title.strip()
            
            # Text analysis
            cleaned_text = self.text_processor.clean_text(combined_text)
            keywords_raw = self.text_processor.extract_keywords(cleaned_text, top_n=10)
            # Extract just the keyword strings (keywords_raw can be list of tuples or list of strings)
            if keywords_raw and isinstance(keywords_raw[0], tuple):
                keywords = [kw[0] for kw in keywords_raw]
            else:
                keywords = keywords_raw if keywords_raw else []
            
            sentiment = self.text_processor.analyze_sentiment(combined_text)
            urgency = self.text_processor.calculate_urgency_score(
                combined_text, 
                issue.get('priority', 'medium')
            )
            complexity = self.text_processor.calculate_complexity_score(combined_text)
            
            # Categorization
            categorization = self.categorizer.categorize_issue(
                title=title,
                description=description
            )
            
            # Build result
            result = {
                'source_issue_id': str(issue['issue_id']),  # Convert Decimal to string
                'source_system': issue['source'],
                'project_id': str(issue['project_id']),  # Convert to string in case it's also Decimal/UUID
                'original_title': title,
                'original_description': description,
                'cleaned_text': cleaned_text,
                'extracted_keywords': ', '.join(keywords) if keywords else '',
                'discipline_category_id': categorization['discipline_category_id'],
                'primary_category_id': categorization['primary_category_id'],
                'secondary_category_id': categorization['secondary_category_id'],
                'confidence_score': categorization['confidence'],
                'sentiment_score': sentiment,
                'urgency_score': urgency,
                'complexity_score': complexity,
                'priority': issue.get('priority'),
                'status': issue.get('status'),
                'created_date': issue.get('created_at'),
                'due_date': issue.get('closed_at'),
                'assigned_to': issue.get('assignee'),
                'processed_date': datetime.now(),
                'success': True,
                'error_message': None
            }
            
            return result
            
        except Exception as e:
            return {
                'source_issue_id': issue.get('issue_id'),
                'source_system': issue.get('source', 'unknown'),
                'success': False,
                'error_message': str(e)
            }
    
    def save_processed_issue(self, result):
        """
        Save a processed issue to the database.
        
        Args:
            result: Processing result dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not result.get('success', False):
            return False
            
        with get_db_connection(self.db_name) as conn:            
        try:
            cursor = conn.cursor()
            
            # Check if already exists
            cursor.execute("""
                SELECT processed_issue_id 
                FROM ProcessedIssues 
                WHERE source_issue_id = ? AND source = ?
            """, (result['source_issue_id'], result['source_system']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE ProcessedIssues
                    SET project_id = ?,
                        title = ?,
                        description = ?,
                        extracted_keywords = ?,
                        discipline_category_id = ?,
                        primary_category_id = ?,
                        secondary_category_id = ?,
                        categorization_confidence = ?,
                        sentiment_score = ?,
                        urgency_score = ?,
                        complexity_score = ?,
                        priority = ?,
                        status = ?,
                        created_at = ?,
                        closed_at = ?,
                        assignee = ?,
                        author = ?,
                        processed_at = GETDATE()
                    WHERE processed_issue_id = ?
                """, (
                    result['project_id'],
                    result['original_title'],
                    result['original_description'],
                    result['extracted_keywords'],
                    result['discipline_category_id'],
                    result['primary_category_id'],
                    result['secondary_category_id'],
                    result['confidence_score'],
                    result['sentiment_score'],
                    result['urgency_score'],
                    result['complexity_score'],
                    result['priority'],
                    result['status'],
                    result['created_date'],
                    result['due_date'],
                    result['assigned_to'],
                    result.get('author', ''),
                    existing[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO ProcessedIssues (
                        source_issue_id, source, project_id,
                        title, description,
                        extracted_keywords, discipline_category_id, primary_category_id,
                        secondary_category_id, categorization_confidence, sentiment_score,
                        urgency_score, complexity_score, priority, status,
                        created_at, closed_at, assignee, author, processed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    result['source_issue_id'],
                    result['source_system'],
                    result['project_id'],
                    result['original_title'],
                    result['original_description'],
                    result['extracted_keywords'],
                    result['discipline_category_id'],
                    result['primary_category_id'],
                    result['secondary_category_id'],
                    result['confidence_score'],
                    result['sentiment_score'],
                    result['urgency_score'],
                    result['complexity_score'],
                    result['priority'],
                    result['status'],
                    result['created_date'],
                    result['due_date'],
                    result['assigned_to'],
                    result.get('author', '')
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error saving processed issue {result.get('source_issue_id')}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
    
    def create_processing_log(self, batch_name='manual'):
        """
        Create a new processing log entry.
        
        Args:
            batch_name: Name/identifier for this batch run
            
        Returns:
            Log ID or None if logging not available
        """
        # Skip logging if table doesn't exist
        return None
    
    def update_processing_log(self, log_id, status='completed', error_message=None):
        """
        Update a processing log entry.
        
        Args:
            log_id: ID of the log entry
            status: Status to set (running, completed, failed)
            error_message: Optional error message
        """
        # Skip if logging not available or no log_id
        if log_id is None:
            return
    
    def process_batch(self, issues, show_progress=True):
        """
        Process a batch of issues.
        
        Args:
            issues: List of issue dictionaries
            show_progress: Whether to print progress updates
            
        Returns:
            List of processing results
        """
        results = []
        total = len(issues)
        
        for idx, issue in enumerate(issues, 1):
            try:
                # Process issue
                result = self.process_issue(issue)
                results.append(result)
                
                # Save to database
                if result.get('success', False):
                    saved = self.save_processed_issue(result)
                    if saved:
                        self.stats['successful'] += 1
                        
                        # Track confidence levels
                        confidence = result.get('confidence_score', 0)
                        if confidence >= 0.5:
                            self.stats['high_confidence'] += 1
                        elif confidence >= 0.3:
                            self.stats['medium_confidence'] += 1
                        else:
                            self.stats['low_confidence'] += 1
                    else:
                        self.stats['failed'] += 1
                        result['error_message'] = "Failed to save to database"
                        print(f"  Issue {issue.get('issue_id')}: Save failed")
                else:
                    self.stats['failed'] += 1
                    print(f"  Issue {issue.get('issue_id')}: Processing failed - {result.get('error_message')}")
                
                self.stats['total_processed'] += 1
                
                # Progress update
                if show_progress and idx % 10 == 0:
                    elapsed = time.time() - self.stats['start_time']
                    rate = idx / elapsed if elapsed > 0 else 0
                    remaining = (total - idx) / rate if rate > 0 else 0
                    
                    print(f"Progress: {idx}/{total} ({idx/total*100:.1f}%) | "
                          f"Rate: {rate:.1f} issues/sec | "
                          f"ETA: {remaining/60:.1f} min | "
                          f"Success: {self.stats['successful']} | "
                          f"Failed: {self.stats['failed']}")
                
            except Exception as e:
                print(f"Error processing issue {issue.get('issue_id')}: {e}")
                self.stats['failed'] += 1
                results.append({
                    'source_issue_id': issue.get('issue_id'),
                    'success': False,
                    'error_message': str(e)
                })
        
        return results
    
    def process_all_issues(self, batch_size=100, limit=None, show_progress=True):
        """
        Process all unprocessed issues in batches.
        
        Args:
            batch_size: Number of issues to process before committing
            limit: Optional limit on total issues to process
            show_progress: Whether to show progress updates
            
        Returns:
            Dictionary with processing statistics
        """
        self.stats['start_time'] = time.time()
        
        # Create processing log
        log_id = self.create_processing_log('batch_all_issues')
        
        try:
            # Get unprocessed issues
            print("Retrieving unprocessed issues...")
            issues = self.get_unprocessed_issues(limit=limit)
            total_issues = len(issues)
            
            if total_issues == 0:
                print("No unprocessed issues found.")
                self.update_processing_log(log_id, 'completed')
                return self.stats
            
            print(f"Found {total_issues} unprocessed issues.")
            print("Starting batch processing...\n")
            
            # Process in batches
            for i in range(0, total_issues, batch_size):
                batch = issues[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_issues + batch_size - 1) // batch_size
                
                print(f"\n=== Batch {batch_num}/{total_batches} ({len(batch)} issues) ===")
                self.process_batch(batch, show_progress=show_progress)
            
            # Final stats
            self.stats['end_time'] = time.time()
            elapsed = self.stats['end_time'] - self.stats['start_time']
            
            print("\n" + "="*60)
            print("BATCH PROCESSING COMPLETE")
            print("="*60)
            print(f"Total Processed: {self.stats['total_processed']}")
            print(f"Successful: {self.stats['successful']}")
            print(f"Failed: {self.stats['failed']}")
            print(f"\nConfidence Distribution:")
            if self.stats['successful'] > 0:
                print(f"  High (≥0.5): {self.stats['high_confidence']} "
                      f"({self.stats['high_confidence']/self.stats['successful']*100:.1f}%)")
                print(f"  Medium (0.3-0.5): {self.stats['medium_confidence']} "
                      f"({self.stats['medium_confidence']/self.stats['successful']*100:.1f}%)")
                print(f"  Low (<0.3): {self.stats['low_confidence']} "
                      f"({self.stats['low_confidence']/self.stats['successful']*100:.1f}%)")
            else:
                print(f"  No successful categorizations")
            print(f"\nTime Elapsed: {elapsed/60:.1f} minutes")
            print(f"Processing Rate: {self.stats['total_processed']/elapsed:.2f} issues/sec")
            print("="*60)
            
            # Update log
            self.update_processing_log(log_id, 'completed')
            
            return self.stats
            
        except Exception as e:
            print(f"\nBatch processing failed: {e}")
            self.update_processing_log(log_id, 'failed', str(e))
            raise


if __name__ == '__main__':
    """
    Test the batch processor with a small sample.
    """
    print("="*60)
    print("ISSUE BATCH PROCESSOR TEST")
    print("="*60)
    
    processor = IssueBatchProcessor()
    
    # Process first 10 issues as a test
    print("\nProcessing first 10 issues as test...\n")
    results = processor.process_all_issues(batch_size=10, limit=10, show_progress=True)
    
    print("\nTest complete!")
