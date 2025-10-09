"""
Review Management Service Layer - Clean API for Business Logic

This service layer provides clean, reusable business logic for review management
that can be consumed by both Tkinter UI and Flask REST API.

Key Features:
- Pure business logic (no UI dependencies)
- Comprehensive validation
- Proper error handling
- Transaction management
- Logging for audit trail
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from database_pool import db_manager, get_db_connection
from constants import schema as S

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review cycle status enumeration."""
    PLANNED = 'planned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    OVERDUE = 'overdue'


class ReviewFrequency(Enum):
    """Review frequency types."""
    ONE_OFF = 'one-off'
    WEEKLY = 'weekly'
    FORTNIGHTLY = 'fortnightly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'


@dataclass
class ReviewCycle:
    """Data class for review cycle."""
    cycle_id: Optional[int]
    project_id: int
    stage_id: int
    cycle_number: int
    planned_date: date
    due_date: Optional[date]
    actual_date: Optional[date]
    status: ReviewStatus
    weight_factor: Decimal
    disciplines: Optional[str]
    deliverables: Optional[str]
    evidence_links: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'cycle_id': self.cycle_id,
            'project_id': self.project_id,
            'stage_id': self.stage_id,
            'cycle_number': self.cycle_number,
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'actual_date': self.actual_date.isoformat() if self.actual_date else None,
            'status': self.status.value if isinstance(self.status, ReviewStatus) else self.status,
            'weight_factor': float(self.weight_factor) if self.weight_factor else 1.0,
            'disciplines': self.disciplines,
            'deliverables': self.deliverables,
            'evidence_links': self.evidence_links
        }


class ReviewServiceError(Exception):
    """Base exception for review service errors."""
    pass


class ReviewValidationError(ReviewServiceError):
    """Raised when validation fails."""
    pass


class ReviewNotFoundError(ReviewServiceError):
    """Raised when review cycle is not found."""
    pass


class ReviewService:
    """
    Service layer for review management operations.
    
    Provides business logic for:
    - Creating and managing review cycles
    - Auto-generating review schedules
    - Tracking deliverables
    - Progress monitoring
    - Status transitions
    """
    
    def __init__(self):
        """Initialize review service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ========== Review Cycle CRUD Operations ==========
    
    def create_review_cycle(self, project_id: int, stage_id: int,
                           planned_date: date, cycle_number: int = 1,
                           due_date: Optional[date] = None,
                           weight_factor: Decimal = Decimal('1.0'),
                           disciplines: Optional[str] = None,
                           deliverables: Optional[str] = None) -> int:
        """
        Create a new review cycle.
        
        Args:
            project_id: Project identifier
            stage_id: Review stage identifier
            planned_date: Planned review date
            cycle_number: Cycle sequence number
            due_date: Due date (optional)
            weight_factor: Weight for billing calculations
            disciplines: Comma-separated disciplines involved
            deliverables: Expected deliverables
            
        Returns:
            cycle_id: ID of created review cycle
            
        Raises:
            ReviewValidationError: If validation fails
            ReviewServiceError: If creation fails
        """
        # Validate inputs
        if project_id <= 0:
            raise ReviewValidationError("Invalid project_id")
        
        if stage_id <= 0:
            raise ReviewValidationError("Invalid stage_id")
        
        if cycle_number <= 0:
            raise ReviewValidationError("Cycle number must be positive")
        
        if weight_factor <= 0:
            raise ReviewValidationError("Weight factor must be positive")
        
        # Check for duplicates
        if self._cycle_exists(project_id, stage_id, cycle_number):
            raise ReviewValidationError(
                f"Review cycle {cycle_number} already exists for this project and stage"
            )
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    INSERT INTO {S.ReviewSchedule.TABLE} (
                        {S.ReviewSchedule.PROJECT_ID},
                        {S.ReviewSchedule.STAGE_ID},
                        {S.ReviewSchedule.CYCLE_NUMBER},
                        {S.ReviewSchedule.PLANNED_DATE},
                        {S.ReviewSchedule.DUE_DATE},
                        {S.ReviewSchedule.STATUS},
                        {S.ReviewSchedule.WEIGHT_FACTOR},
                        {S.ReviewSchedule.DISCIPLINES},
                        {S.ReviewSchedule.DELIVERABLES}
                    ) OUTPUT INSERTED.{S.ReviewSchedule.CYCLE_ID}
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id, stage_id, cycle_number, planned_date, due_date,
                    ReviewStatus.PLANNED.value, weight_factor, disciplines, deliverables
                ))
                
                cycle_id = cursor.fetchone()[0]
                conn.commit()
                
                self.logger.info(
                    f"Created review cycle {cycle_id} for project {project_id}, "
                    f"stage {stage_id}, cycle #{cycle_number}"
                )
                
                return cycle_id
                
        except Exception as e:
            self.logger.error(f"Failed to create review cycle: {e}")
            raise ReviewServiceError(f"Failed to create review cycle: {str(e)}")
    
    def get_review_cycle(self, cycle_id: int) -> ReviewCycle:
        """
        Get review cycle by ID.
        
        Args:
            cycle_id: Review cycle identifier
            
        Returns:
            ReviewCycle instance
            
        Raises:
            ReviewNotFoundError: If cycle not found
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        {S.ReviewSchedule.CYCLE_ID},
                        {S.ReviewSchedule.PROJECT_ID},
                        {S.ReviewSchedule.STAGE_ID},
                        {S.ReviewSchedule.CYCLE_NUMBER},
                        {S.ReviewSchedule.PLANNED_DATE},
                        {S.ReviewSchedule.DUE_DATE},
                        {S.ReviewSchedule.ACTUAL_DATE},
                        {S.ReviewSchedule.STATUS},
                        {S.ReviewSchedule.WEIGHT_FACTOR},
                        {S.ReviewSchedule.DISCIPLINES},
                        {S.ReviewSchedule.DELIVERABLES},
                        {S.ReviewSchedule.EVIDENCE_LINKS}
                    FROM {S.ReviewSchedule.TABLE}
                    WHERE {S.ReviewSchedule.CYCLE_ID} = ?
                """, (cycle_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    raise ReviewNotFoundError(f"Review cycle {cycle_id} not found")
                
                return ReviewCycle(
                    cycle_id=row[0],
                    project_id=row[1],
                    stage_id=row[2],
                    cycle_number=row[3],
                    planned_date=row[4],
                    due_date=row[5],
                    actual_date=row[6],
                    status=ReviewStatus(row[7]) if row[7] else ReviewStatus.PLANNED,
                    weight_factor=row[8] or Decimal('1.0'),
                    disciplines=row[9],
                    deliverables=row[10],
                    evidence_links=row[11]
                )
                
        except ReviewNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get review cycle {cycle_id}: {e}")
            raise ReviewServiceError(f"Failed to get review cycle: {str(e)}")
    
    def list_review_cycles(self, project_id: int, 
                          stage_id: Optional[int] = None,
                          status: Optional[ReviewStatus] = None) -> List[ReviewCycle]:
        """
        List review cycles for a project.
        
        Args:
            project_id: Project identifier
            stage_id: Filter by stage (optional)
            status: Filter by status (optional)
            
        Returns:
            List of ReviewCycle instances
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Build query
                where_clauses = [f"{S.ReviewSchedule.PROJECT_ID} = ?"]
                params = [project_id]
                
                if stage_id is not None:
                    where_clauses.append(f"{S.ReviewSchedule.STAGE_ID} = ?")
                    params.append(stage_id)
                
                if status is not None:
                    where_clauses.append(f"{S.ReviewSchedule.STATUS} = ?")
                    params.append(status.value)
                
                where_clause = " AND ".join(where_clauses)
                
                cursor.execute(f"""
                    SELECT 
                        {S.ReviewSchedule.CYCLE_ID},
                        {S.ReviewSchedule.PROJECT_ID},
                        {S.ReviewSchedule.STAGE_ID},
                        {S.ReviewSchedule.CYCLE_NUMBER},
                        {S.ReviewSchedule.PLANNED_DATE},
                        {S.ReviewSchedule.DUE_DATE},
                        {S.ReviewSchedule.ACTUAL_DATE},
                        {S.ReviewSchedule.STATUS},
                        {S.ReviewSchedule.WEIGHT_FACTOR},
                        {S.ReviewSchedule.DISCIPLINES},
                        {S.ReviewSchedule.DELIVERABLES},
                        {S.ReviewSchedule.EVIDENCE_LINKS}
                    FROM {S.ReviewSchedule.TABLE}
                    WHERE {where_clause}
                    ORDER BY {S.ReviewSchedule.PLANNED_DATE}, {S.ReviewSchedule.CYCLE_NUMBER}
                """, params)
                
                cycles = []
                for row in cursor.fetchall():
                    cycles.append(ReviewCycle(
                        cycle_id=row[0],
                        project_id=row[1],
                        stage_id=row[2],
                        cycle_number=row[3],
                        planned_date=row[4],
                        due_date=row[5],
                        actual_date=row[6],
                        status=ReviewStatus(row[7]) if row[7] else ReviewStatus.PLANNED,
                        weight_factor=row[8] or Decimal('1.0'),
                        disciplines=row[9],
                        deliverables=row[10],
                        evidence_links=row[11]
                    ))
                
                return cycles
                
        except Exception as e:
            self.logger.error(f"Failed to list review cycles: {e}")
            raise ReviewServiceError(f"Failed to list review cycles: {str(e)}")
    
    def update_review_cycle(self, cycle_id: int, **kwargs) -> bool:
        """
        Update review cycle fields.
        
        Args:
            cycle_id: Review cycle identifier
            **kwargs: Fields to update (planned_date, due_date, status, etc.)
            
        Returns:
            True if updated successfully
            
        Raises:
            ReviewNotFoundError: If cycle not found
            ReviewValidationError: If validation fails
        """
        # Validate cycle exists
        self.get_review_cycle(cycle_id)
        
        allowed_fields = {
            'planned_date': S.ReviewSchedule.PLANNED_DATE,
            'due_date': S.ReviewSchedule.DUE_DATE,
            'actual_date': S.ReviewSchedule.ACTUAL_DATE,
            'status': S.ReviewSchedule.STATUS,
            'weight_factor': S.ReviewSchedule.WEIGHT_FACTOR,
            'disciplines': S.ReviewSchedule.DISCIPLINES,
            'deliverables': S.ReviewSchedule.DELIVERABLES,
            'evidence_links': S.ReviewSchedule.EVIDENCE_LINKS
        }
        
        # Build update query
        update_fields = []
        params = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                update_fields.append(f"{allowed_fields[key]} = ?")
                
                # Convert enums to values
                if isinstance(value, ReviewStatus):
                    params.append(value.value)
                else:
                    params.append(value)
        
        if not update_fields:
            raise ReviewValidationError("No valid fields to update")
        
        params.append(cycle_id)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = f"""
                    UPDATE {S.ReviewSchedule.TABLE}
                    SET {', '.join(update_fields)}
                    WHERE {S.ReviewSchedule.CYCLE_ID} = ?
                """
                
                cursor.execute(query, params)
                conn.commit()
                
                self.logger.info(f"Updated review cycle {cycle_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update review cycle {cycle_id}: {e}")
            raise ReviewServiceError(f"Failed to update review cycle: {str(e)}")
    
    def delete_review_cycle(self, cycle_id: int) -> bool:
        """
        Delete a review cycle.
        
        Args:
            cycle_id: Review cycle identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    DELETE FROM {S.ReviewSchedule.TABLE}
                    WHERE {S.ReviewSchedule.CYCLE_ID} = ?
                """, (cycle_id,))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    self.logger.info(f"Deleted review cycle {cycle_id}")
                else:
                    self.logger.warning(f"Review cycle {cycle_id} not found for deletion")
                
                return deleted
                
        except Exception as e:
            self.logger.error(f"Failed to delete review cycle {cycle_id}: {e}")
            raise ReviewServiceError(f"Failed to delete review cycle: {str(e)}")
    
    # ========== Auto-Generation Logic ==========
    
    def generate_review_schedule(self, project_id: int, stage_id: int,
                                start_date: date, end_date: date,
                                frequency: ReviewFrequency,
                                num_cycles: Optional[int] = None) -> List[int]:
        """
        Auto-generate review schedule based on frequency.
        
        Args:
            project_id: Project identifier
            stage_id: Stage identifier  
            start_date: Schedule start date
            end_date: Schedule end date
            frequency: Review frequency
            num_cycles: Number of cycles (overrides end_date if provided)
            
        Returns:
            List of created cycle IDs
            
        Raises:
            ReviewValidationError: If parameters invalid
        """
        if start_date >= end_date and num_cycles is None:
            raise ReviewValidationError("start_date must be before end_date")
        
        cycle_dates = self._calculate_cycle_dates(
            start_date, end_date, frequency, num_cycles
        )
        
        created_ids = []
        
        try:
            for cycle_num, planned_date in enumerate(cycle_dates, start=1):
                # Calculate due date (7 days after planned)
                due_date = planned_date + timedelta(days=7)
                
                cycle_id = self.create_review_cycle(
                    project_id=project_id,
                    stage_id=stage_id,
                    planned_date=planned_date,
                    cycle_number=cycle_num,
                    due_date=due_date
                )
                
                created_ids.append(cycle_id)
            
            self.logger.info(
                f"Generated {len(created_ids)} review cycles for project {project_id}"
            )
            
            return created_ids
            
        except Exception as e:
            self.logger.error(f"Failed to generate review schedule: {e}")
            # Rollback - delete created cycles
            for cycle_id in created_ids:
                try:
                    self.delete_review_cycle(cycle_id)
                except:
                    pass
            raise ReviewServiceError(f"Failed to generate review schedule: {str(e)}")
    
    def _calculate_cycle_dates(self, start_date: date, end_date: date,
                              frequency: ReviewFrequency,
                              num_cycles: Optional[int] = None) -> List[date]:
        """Calculate review cycle dates based on frequency."""
        dates = []
        current_date = start_date
        
        # Define frequency deltas
        frequency_deltas = {
            ReviewFrequency.WEEKLY: timedelta(days=7),
            ReviewFrequency.FORTNIGHTLY: timedelta(days=14),
            ReviewFrequency.MONTHLY: timedelta(days=30),
            ReviewFrequency.QUARTERLY: timedelta(days=90)
        }
        
        if frequency == ReviewFrequency.ONE_OFF:
            return [start_date]
        
        delta = frequency_deltas.get(frequency)
        if not delta:
            raise ReviewValidationError(f"Invalid frequency: {frequency}")
        
        if num_cycles:
            # Generate specific number of cycles
            for _ in range(num_cycles):
                dates.append(current_date)
                current_date += delta
        else:
            # Generate cycles until end_date
            while current_date <= end_date:
                dates.append(current_date)
                current_date += delta
        
        return dates
    
    # ========== Helper Methods ==========
    
    def _cycle_exists(self, project_id: int, stage_id: int, cycle_number: int) -> bool:
        """Check if a review cycle already exists."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM {S.ReviewSchedule.TABLE}
                    WHERE {S.ReviewSchedule.PROJECT_ID} = ?
                      AND {S.ReviewSchedule.STAGE_ID} = ?
                      AND {S.ReviewSchedule.CYCLE_NUMBER} = ?
                """, (project_id, stage_id, cycle_number))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Error checking cycle existence: {e}")
            return False
    
    def get_project_progress(self, project_id: int) -> Dict[str, Any]:
        """
        Calculate project progress based on completed reviews.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dictionary with progress metrics
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_cycles,
                        SUM(CASE WHEN {S.ReviewSchedule.STATUS} = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN {S.ReviewSchedule.STATUS} = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN {S.ReviewSchedule.STATUS} = 'planned' THEN 1 ELSE 0 END) as planned,
                        SUM({S.ReviewSchedule.WEIGHT_FACTOR}) as total_weight,
                        SUM(CASE WHEN {S.ReviewSchedule.STATUS} = 'completed' 
                            THEN {S.ReviewSchedule.WEIGHT_FACTOR} ELSE 0 END) as completed_weight
                    FROM {S.ReviewSchedule.TABLE}
                    WHERE {S.ReviewSchedule.PROJECT_ID} = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                
                total = row[0] or 0
                completed = row[1] or 0
                in_progress = row[2] or 0
                planned = row[3] or 0
                total_weight = float(row[4] or 0)
                completed_weight = float(row[5] or 0)
                
                progress_pct = (completed_weight / total_weight * 100) if total_weight > 0 else 0
                
                return {
                    'total_cycles': total,
                    'completed': completed,
                    'in_progress': in_progress,
                    'planned': planned,
                    'progress_percentage': round(progress_pct, 2),
                    'total_weight': total_weight,
                    'completed_weight': completed_weight
                }
                
        except Exception as e:
            self.logger.error(f"Failed to calculate project progress: {e}")
            raise ReviewServiceError(f"Failed to calculate progress: {str(e)}")
