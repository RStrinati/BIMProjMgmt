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

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import numpy as np

from database_pool import get_db_connection
from config import Config

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
        try:
            with get_db_connection(self.db_name) as conn:
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
    
    def calculate_pain_points_by_discipline(self) -> List[Dict]:
        """
        Calculate pain points aggregated by discipline.

        Returns:
            List of dictionaries with discipline pain point metrics
        """
        try:
            with get_db_connection(self.db_name) as conn:
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

    def calculate_pain_points_by_client(self) -> List[Dict]:
        """Aggregate pain point metrics at the client level."""

        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        ai.client_id,
                        COALESCE(ai.client_name, 'Unknown') AS client_name,
                        COUNT(DISTINCT pi.processed_issue_id) AS total_issues,
                        COUNT(DISTINCT CASE WHEN pi.status = 'open' THEN pi.processed_issue_id END) AS open_issues,
                        COUNT(DISTINCT CASE WHEN pi.status = 'closed' THEN pi.processed_issue_id END) AS closed_issues,
                        COUNT(DISTINCT pi.project_id) AS project_count,

                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Electrical' THEN pi.processed_issue_id END) AS electrical_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Hydraulic/Plumbing' THEN pi.processed_issue_id END) AS hydraulic_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Mechanical (HVAC)' THEN pi.processed_issue_id END) AS mechanical_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Structural' THEN pi.processed_issue_id END) AS structural_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Architectural' THEN pi.processed_issue_id END) AS architectural_issues,

                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Clash%' THEN pi.processed_issue_id END) AS clash_issues,
                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Information%' THEN pi.processed_issue_id END) AS info_issues,
                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Design%' THEN pi.processed_issue_id END) AS design_issues,

                        AVG(pi.urgency_score) AS avg_urgency,
                        AVG(pi.complexity_score) AS avg_complexity,
                        AVG(pi.categorization_confidence) AS avg_confidence,
                        AVG(pi.sentiment_score) AS avg_sentiment,
                        AVG(CASE
                            WHEN pi.closed_at IS NOT NULL AND pi.created_at IS NOT NULL THEN DATEDIFF(day, pi.created_at, pi.closed_at)
                            ELSE NULL
                        END) AS avg_resolution_days
                    FROM ProcessedIssues pi
                    INNER JOIN vw_ProjectManagement_AllIssues ai
                        ON pi.source_issue_id = CAST(ai.issue_id AS NVARCHAR(255))
                        AND pi.source = ai.source
                    LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                    LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                    WHERE pi.processed_at IS NOT NULL
                    GROUP BY ai.client_id, COALESCE(ai.client_name, 'Unknown')
                    HAVING COUNT(DISTINCT pi.processed_issue_id) > 0
                    ORDER BY total_issues DESC
                """

                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                results: List[Dict] = []

                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    total_issues = result['total_issues'] or 0
                    open_issues = result['open_issues'] or 0
                    avg_urgency = float(result['avg_urgency'] or 0)
                    avg_complexity = float(result['avg_complexity'] or 0)

                    open_ratio = (open_issues / total_issues) if total_issues > 0 else 0
                    result['pain_point_score'] = (
                        avg_urgency * 0.3
                        + avg_complexity * 0.3
                        + open_ratio * 0.4
                    )

                    result['issue_density'] = total_issues
                    results.append(result)

            logger.info("Calculated pain points for %d clients", len(results))
            return results

        except Exception as e:
            logger.error("Error calculating client pain points: %s", e)
            return []

    def calculate_pain_points_by_project_type(self) -> List[Dict]:
        """Aggregate pain point metrics at the project type level."""

        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()

                # Use proper table joins instead of the view which lacks project_type column
                # Note: project_id in ProcessedIssues may be NVARCHAR (GUIDs) while projects.project_id is INT
                # We use TRY_CAST to safely convert only valid integer project_ids
                query = """
                    SELECT
                        COALESCE(pt.project_type_name, 'Unknown') AS project_type,
                        COUNT(DISTINCT pi.processed_issue_id) AS total_issues,
                        COUNT(DISTINCT CASE WHEN pi.status = 'open' THEN pi.processed_issue_id END) AS open_issues,
                        COUNT(DISTINCT CASE WHEN pi.status = 'closed' THEN pi.processed_issue_id END) AS closed_issues,
                        COUNT(DISTINCT TRY_CAST(pi.project_id AS INT)) AS project_count,

                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Electrical' THEN pi.processed_issue_id END) AS electrical_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Hydraulic/Plumbing' THEN pi.processed_issue_id END) AS hydraulic_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Mechanical (HVAC)' THEN pi.processed_issue_id END) AS mechanical_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Structural' THEN pi.processed_issue_id END) AS structural_issues,
                        COUNT(DISTINCT CASE WHEN disc.category_name = 'Architectural' THEN pi.processed_issue_id END) AS architectural_issues,

                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Clash%' THEN pi.processed_issue_id END) AS clash_issues,
                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Information%' THEN pi.processed_issue_id END) AS info_issues,
                        COUNT(DISTINCT CASE WHEN prim.category_name LIKE '%Design%' THEN pi.processed_issue_id END) AS design_issues,

                        AVG(pi.urgency_score) AS avg_urgency,
                        AVG(pi.complexity_score) AS avg_complexity,
                        AVG(pi.categorization_confidence) AS avg_confidence,
                        AVG(pi.sentiment_score) AS avg_sentiment,
                        AVG(CASE
                            WHEN pi.closed_at IS NOT NULL AND pi.created_at IS NOT NULL THEN DATEDIFF(day, pi.created_at, pi.closed_at)
                            ELSE NULL
                        END) AS avg_resolution_days
                    FROM ProcessedIssues pi
                    LEFT JOIN projects p ON TRY_CAST(pi.project_id AS INT) = p.project_id
                    LEFT JOIN project_types pt ON p.type_id = pt.project_type_id
                    LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                    LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                    WHERE pi.processed_at IS NOT NULL
                    GROUP BY COALESCE(pt.project_type_name, 'Unknown')
                    HAVING COUNT(DISTINCT pi.processed_issue_id) > 0
                    ORDER BY total_issues DESC
                """

                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                results: List[Dict] = []

                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    total_issues = result['total_issues'] or 0
                    open_issues = result['open_issues'] or 0
                    avg_urgency = float(result['avg_urgency'] or 0)
                    avg_complexity = float(result['avg_complexity'] or 0)

                    open_ratio = (open_issues / total_issues) if total_issues > 0 else 0
                    result['pain_point_score'] = (
                        avg_urgency * 0.3
                        + avg_complexity * 0.3
                        + open_ratio * 0.4
                    )

                    result['issue_density'] = total_issues
                    results.append(result)

            logger.info("Calculated pain points for %d project types", len(results))
            return results

        except Exception as e:
            logger.error("Error calculating project type pain points: %s", e)
            return []

    def _compute_issue_embeddings(self, issues: List[Dict]) -> Optional[np.ndarray]:
        """Compute semantic embeddings for the provided issues.

        Attempts to use a sentence-transformer model when available and falls back to
        TF-IDF vectors if transformers or the model download is not available. When
        both approaches fail the function returns ``None`` so the caller can degrade
        to keyword-only clustering.
        """

        if not issues:
            return None

        texts = []
        for issue in issues:
            title = issue.get('title') or ''
            description = issue.get('description') or ''
            combined = f"{title.strip()} {description.strip()}".strip()
            texts.append(combined or title or description)

        if not any(texts):
            return None

        try:
            from sentence_transformers import SentenceTransformer

            model_name = getattr(Config, 'ISSUE_PATTERN_MODEL', 'all-MiniLM-L6-v2')
            model = SentenceTransformer(model_name)
            embeddings = model.encode(texts, normalize_embeddings=True)
            return np.asarray(embeddings)
        except Exception as transformer_error:  # pragma: no cover - optional dependency
            logger.info(
                "Falling back to TF-IDF similarity for issue clustering: %s",
                transformer_error,
            )

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.preprocessing import normalize

            vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
            matrix = vectorizer.fit_transform(texts)
            normalized = normalize(matrix)
            return normalized.toarray()
        except Exception as tfidf_error:  # pragma: no cover - optional dependency
            logger.warning(
                "Unable to compute TF-IDF embeddings for recurring patterns: %s",
                tfidf_error,
            )
            return None

    @staticmethod
    def _jaccard_similarity(first: set, second: set) -> float:
        if not first and not second:
            return 1.0
        if not first or not second:
            return 0.0

        intersection = first & second
        union = first | second
        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def _normalize_vector(vector: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """Normalize a vector to unit length, guarding against zero vectors."""

        if vector is None:
            return None

        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector

        return vector / norm

    @staticmethod
    def _normalize_metric(value: float, max_value: float) -> float:
        if max_value <= 0:
            return 0.0
        return max(0.0, min(1.0, value / max_value))

    @staticmethod
    def _safe_datetime(value) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        return None

    def identify_recurring_patterns(self, similarity_threshold: float = 0.65) -> List[Dict]:
        """
        Identify recurring issue patterns using title similarity.
        
        Args:
            similarity_threshold: Minimum similarity score to consider issues similar
            
        Returns:
            List of recurring pattern clusters
        """
        try:
            with get_db_connection(self.db_name) as conn:
                cursor = conn.cursor()

                # Use the baseline query with proper table joins
                # Note: project_id in ProcessedIssues may be NVARCHAR (GUIDs) while projects.project_id is INT
                # We use TRY_CAST to safely convert only valid integer project_ids
                query = """
                    SELECT
                        pi.processed_issue_id,
                        pi.title,
                        pi.description,
                        pi.extracted_keywords,
                        pi.project_id,
                        p.project_name,
                        pt.project_type_name AS project_type,
                        c.client_id,
                        c.client_name,
                        pi.source AS source,
                        disc.category_name AS discipline,
                        prim.category_name AS issue_type,
                        sec.category_name AS phase,
                        pi.created_at,
                        pi.closed_at,
                        pi.status,
                        pi.priority,
                        pi.urgency_score,
                        pi.complexity_score,
                        pi.sentiment_score
                    FROM ProcessedIssues pi
                    LEFT JOIN projects p ON TRY_CAST(pi.project_id AS INT) = p.project_id
                    LEFT JOIN project_types pt ON p.type_id = pt.project_type_id
                    LEFT JOIN clients c ON p.client_id = c.client_id
                    LEFT JOIN IssueCategories disc ON pi.discipline_category_id = disc.category_id
                    LEFT JOIN IssueCategories prim ON pi.primary_category_id = prim.category_id
                    LEFT JOIN IssueCategories sec ON pi.secondary_category_id = sec.category_id
                    WHERE pi.extracted_keywords IS NOT NULL
                        AND pi.extracted_keywords <> ''
                """

                cursor.execute(query)

                columns = [desc[0] for desc in cursor.description]
                raw_issues = [dict(zip(columns, row)) for row in cursor.fetchall()]

                issues = []
                for issue in raw_issues:
                    keyword_string = issue.get('extracted_keywords') or ''
                    keywords = {kw.strip() for kw in keyword_string.lower().split(',') if kw.strip()}
                    if not keywords:
                        continue

                    issue['_keywords'] = keywords
                issue['_created_at'] = self._safe_datetime(issue.get('created_at'))
                issue['_closed_at'] = self._safe_datetime(issue.get('closed_at'))
                issues.append(issue)

            embeddings = self._compute_issue_embeddings(issues)

            clusters: List[Dict] = []
            for idx, issue in enumerate(issues):
                keywords = issue['_keywords']
                issue_embedding = embeddings[idx] if embeddings is not None else None

                best_cluster = None
                best_score = 0.0

                for cluster in clusters:
                    keyword_similarity = self._jaccard_similarity(keywords, cluster['keywords'])
                    semantic_similarity = 0.0

                    if issue_embedding is not None and cluster['centroid'] is not None:
                        semantic_similarity = float(np.dot(issue_embedding, cluster['centroid']))
                        semantic_similarity = max(0.0, min(1.0, semantic_similarity))

                    combined_similarity = (
                        0.5 * keyword_similarity + 0.5 * semantic_similarity
                        if issue_embedding is not None and cluster['centroid'] is not None
                        else keyword_similarity
                    )

                    if combined_similarity >= similarity_threshold and combined_similarity > best_score:
                        best_cluster = cluster
                        best_score = combined_similarity

                if best_cluster:
                    best_cluster['issues'].append(issue)
                    best_cluster['keywords'].update(keywords)
                    if issue_embedding is not None:
                        best_cluster['embedding_sum'] += issue_embedding
                        best_cluster['embedding_count'] += 1
                        average = (
                            best_cluster['embedding_sum'] / best_cluster['embedding_count']
                        )
                        best_cluster['centroid'] = self._normalize_vector(average)
                else:
                    clusters.append(
                        {
                            'issues': [issue],
                            'keywords': set(keywords),
                            'embedding_sum': issue_embedding.copy() if issue_embedding is not None else None,
                            'embedding_count': 1 if issue_embedding is not None else 0,
                            'centroid': self._normalize_vector(
                                issue_embedding.copy()
                            ) if issue_embedding is not None else None,
                        }
                    )

            recurring_patterns: List[Dict] = []

            for cluster in clusters:
                cluster_issues = cluster['issues']
                if len(cluster_issues) < 3:
                    continue

                keyword_counter: Counter = Counter()
                discipline_counter: Counter = Counter()
                issue_type_counter: Counter = Counter()
                phase_counter: Counter = Counter()
                client_counter: Counter = Counter()
                source_counter: Counter = Counter()
                project_names: set = set()
                project_ids: set = set()

                created_dates: List[datetime] = []
                resolution_days: List[float] = []
                open_count = 0
                recent_count = 0
                severity_scores: List[float] = []

                now = datetime.now()
                for issue in cluster_issues:
                    keyword_counter.update(issue['_keywords'])
                    discipline_counter.update([issue.get('discipline') or 'Unknown'])
                    issue_type_counter.update([issue.get('issue_type') or 'Unknown'])
                    phase_counter.update([issue.get('phase') or 'Unknown'])
                    client_counter.update([issue.get('client_name') or 'Unknown'])
                    source_counter.update([issue.get('source') or 'Unknown'])

                    project_id = issue.get('project_id')
                    project_ids.add(project_id)
                    project_names.add(issue.get('project_name') or str(project_id))

                    created_at = issue.get('_created_at')
                    closed_at = issue.get('_closed_at')
                    if created_at:
                        created_dates.append(created_at)
                        if created_at >= now - timedelta(days=30):
                            recent_count += 1

                    if issue.get('status', '').lower() in {'open', 'in progress', 'reopened'}:
                        open_count += 1

                    if created_at and closed_at and closed_at >= created_at:
                        delta = closed_at - created_at
                        resolution_days.append(delta.total_seconds() / 86400.0)

                    urgency = float(issue.get('urgency_score') or 0.0)
                    complexity = float(issue.get('complexity_score') or 0.0)
                    severity_scores.append((urgency + complexity) / 2.0)

                occurrence_count = len(cluster_issues)
                project_count = len({pid for pid in project_ids if pid is not None}) or len(project_ids)
                client_count = len([name for name in client_counter if name != 'Unknown'])
                if client_count == 0 and client_counter:
                    client_count = len(client_counter)

                avg_resolution = sum(resolution_days) / len(resolution_days) if resolution_days else None
                open_rate = open_count / occurrence_count if occurrence_count else 0.0
                severity_avg = sum(severity_scores) / len(severity_scores) if severity_scores else 0.0

                recurrence_score = self._normalize_metric(occurrence_count, 25)
                severity_score = self._normalize_metric(severity_avg, 5)
                breadth_score = self._normalize_metric(project_count + client_count, 10)

                actionability_score = round(
                    0.4 * recurrence_score + 0.35 * severity_score + 0.25 * breadth_score,
                    3,
                )

                top_keywords = [kw for kw, _ in keyword_counter.most_common(5)]
                top_discipline = discipline_counter.most_common(1)[0] if discipline_counter else ('Unknown', 0)
                top_issue_type = issue_type_counter.most_common(1)[0] if issue_type_counter else ('Unknown', 0)
                top_phase = phase_counter.most_common(1)[0] if phase_counter else ('Unknown', 0)

                created_dates.sort()
                first_seen = created_dates[0].isoformat() if created_dates else None
                last_seen = created_dates[-1].isoformat() if created_dates else None

                if len(created_dates) >= 2:
                    recurrence_gaps = [
                        (later - earlier).total_seconds() / 86400.0
                        for earlier, later in zip(created_dates[:-1], created_dates[1:])
                    ]
                    avg_gap = sum(recurrence_gaps) / len(recurrence_gaps)
                else:
                    avg_gap = None

                pattern = {
                    'pattern_id': len(recurring_patterns) + 1,
                    'common_keywords': ', '.join(top_keywords),
                    'occurrence_count': occurrence_count,
                    'project_count': project_count,
                    'client_count': client_count,
                    'top_discipline': top_discipline[0],
                    'discipline_count': top_discipline[1],
                    'top_issue_type': top_issue_type[0],
                    'issue_type_count': top_issue_type[1],
                    'top_phase': top_phase[0],
                    'phase_count': top_phase[1],
                    'example_titles': [issue['title'] for issue in cluster_issues[:3]],
                    'project_names': sorted(project_names),
                    'client_breakdown': [
                        {'client_name': name, 'count': count}
                        for name, count in client_counter.most_common()
                    ],
                    'source_breakdown': [
                        {'source': name, 'count': count}
                        for name, count in source_counter.most_common()
                    ],
                    'temporal_metrics': {
                        'first_seen': first_seen,
                        'last_seen': last_seen,
                        'avg_days_between_occurrences': avg_gap,
                        'avg_resolution_days': avg_resolution,
                        'open_rate': round(open_rate, 3),
                        'occurrences_last_30_days': recent_count,
                    },
                    'severity_summary': {
                        'average_severity': round(severity_avg, 3),
                        'average_sentiment': round(
                            sum(float(issue.get('sentiment_score') or 0.0) for issue in cluster_issues)
                            / occurrence_count,
                            3,
                        )
                        if occurrence_count
                        else None,
                        'priority_distribution': [
                            {'priority': name, 'count': count}
                            for name, count in Counter(
                                (issue.get('priority') or 'unspecified').lower()
                                for issue in cluster_issues
                            ).most_common()
                        ],
                    },
                    'actionability': {
                        'score': actionability_score,
                        'recurrence_score': recurrence_score,
                        'severity_score': severity_score,
                        'breadth_score': breadth_score,
                    },
                }

                recurring_patterns.append(pattern)

            recurring_patterns.sort(
                key=lambda x: (x['actionability']['score'], x['occurrence_count']),
                reverse=True,
            )

            logger.info(f"Identified {len(recurring_patterns)} recurring patterns")
            return recurring_patterns
            
        except Exception as e:
            logger.error(f"Error identifying recurring patterns: {e}")
            return []
    
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
        try:
            with get_db_connection(self.db_name) as conn:
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
            return False


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
