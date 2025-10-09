"""
Enhanced Task Management Module
Extends the existing task functionality with dependencies, priorities, and progress tracking
"""

import pyodbc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

class TaskManager:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_task_with_dependencies(self, task_data: Dict) -> bool:
        """Create a task with dependency relationships"""
        try:
            cursor = self.conn.cursor()
            
            # Insert main task
            cursor.execute("""
                INSERT INTO tasks (
                    task_name, project_id, start_date, end_date, assigned_to, 
                    priority, estimated_hours, predecessor_task_id, progress_percentage,
                    description, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data['task_name'],
                task_data['project_id'],
                task_data['start_date'],
                task_data['end_date'],
                task_data['assigned_to'],
                task_data.get('priority', 'Medium'),
                task_data.get('estimated_hours', 0),
                task_data.get('predecessor_task_id'),
                task_data.get('progress_percentage', 0),
                task_data.get('description', ''),
                task_data.get('status', 'Not Started')
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating task: {e}")
            self.conn.rollback()
            return False
    
    def get_project_critical_path(self, project_id: int) -> List[Dict]:
        """Calculate critical path for a project"""
        cursor = self.conn.cursor()
        
        # Get all tasks for the project with dependencies
        cursor.execute("""
            SELECT t.task_id, t.task_name, t.start_date, t.end_date, 
                   t.estimated_hours, t.predecessor_task_id, t.status
            FROM tasks t
            WHERE t.project_id = ?
            ORDER BY t.start_date
        """, (project_id,))
        
        tasks = cursor.fetchall()
        
        # Simple critical path calculation (can be enhanced with proper CPM algorithm)
        critical_path = []
        for task in tasks:
            task_dict = {
                'task_id': task.task_id,
                'task_name': task.task_name,
                'start_date': task.start_date,
                'end_date': task.end_date,
                'duration_days': (task.end_date - task.start_date).days,
                'predecessor': task.predecessor_task_id,
                'status': task.status,
                'is_critical': self._is_critical_task(task.task_id)
            }
            critical_path.append(task_dict)
        
        return critical_path
    
    def _is_critical_task(self, task_id: int) -> bool:
        """Determine if a task is on the critical path"""
        # Simplified logic - in real implementation, use proper CPM algorithm
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE predecessor_task_id = ? AND status != 'Complete'
        """, (task_id,))
        
        dependent_tasks = cursor.fetchone()[0]
        return dependent_tasks > 0
    
    def update_task_progress(self, task_id: int, progress_percentage: int, actual_hours: float = None) -> bool:
        """Update task progress and automatically adjust status"""
        try:
            cursor = self.conn.cursor()
            
            # Determine status based on progress
            if progress_percentage == 0:
                status = 'Not Started'
            elif progress_percentage == 100:
                status = 'Complete'
            else:
                status = 'In Progress'
            
            update_query = """
                UPDATE tasks 
                SET progress_percentage = ?, status = ?, updated_at = GETDATE()
            """
            params = [progress_percentage, status]
            
            if actual_hours is not None:
                update_query += ", actual_hours = ?"
                params.append(actual_hours)
            
            update_query += " WHERE task_id = ?"
            params.append(task_id)
            
            cursor.execute(update_query, params)
            
            # Auto-advance successor tasks if this task is complete
            if status == 'Complete':
                self._check_successor_tasks(task_id)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating task progress: {e}")
            self.conn.rollback()
            return False
    
    def _check_successor_tasks(self, completed_task_id: int):
        """Check and update successor tasks when predecessor is complete"""
        cursor = self.conn.cursor()
        
        # Find tasks that depend on the completed task
        cursor.execute("""
            SELECT task_id, task_name FROM tasks 
            WHERE predecessor_task_id = ? AND status = 'Not Started'
        """, (completed_task_id,))
        
        successor_tasks = cursor.fetchall()
        
        # Update successor tasks to 'Ready to Start' status
        for task in successor_tasks:
            cursor.execute("""
                UPDATE tasks SET status = 'Ready to Start' WHERE task_id = ?
            """, (task.task_id,))
    
    def get_resource_workload(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict:
        """Get workload analysis for a user within a date range"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT t.task_name, t.start_date, t.end_date, t.estimated_hours, 
                   t.progress_percentage, p.project_name
            FROM tasks t
            JOIN projects p ON t.project_id = p.project_id
            WHERE t.assigned_to = ? 
            AND t.start_date <= ? 
            AND t.end_date >= ?
            AND t.status NOT IN ('Complete', 'Cancelled')
        """, (user_id, end_date, start_date))
        
        tasks = cursor.fetchall()
        
        total_hours = sum(task.estimated_hours or 0 for task in tasks)
        working_days = (end_date - start_date).days
        
        # Get user's weekly capacity
        cursor.execute("""
            SELECT weekly_capacity_hours FROM users WHERE user_id = ?
        """, (user_id,))
        
        user_capacity = cursor.fetchone()
        weekly_capacity = user_capacity.weekly_capacity_hours if user_capacity else 40
        
        capacity_hours = (weekly_capacity * working_days) / 7
        
        return {
            'user_id': user_id,
            'period_start': start_date,
            'period_end': end_date,
            'assigned_tasks': len(tasks),
            'total_estimated_hours': total_hours,
            'available_capacity_hours': capacity_hours,
            'utilization_percentage': (total_hours / capacity_hours * 100) if capacity_hours > 0 else 0,
            'is_overallocated': total_hours > capacity_hours,
            'tasks': [
                {
                    'task_name': task.task_name,
                    'project_name': task.project_name,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'estimated_hours': task.estimated_hours,
                    'progress': task.progress_percentage
                } for task in tasks
            ]
        }

class MilestoneManager:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def create_milestone(self, milestone_data: Dict) -> bool:
        """Create a new project milestone"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO milestones (
                    project_id, milestone_name, target_date, 
                    description, status
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                milestone_data['project_id'],
                milestone_data['milestone_name'],
                milestone_data['target_date'],
                milestone_data.get('description', ''),
                milestone_data.get('status', 'Pending')
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating milestone: {e}")
            self.conn.rollback()
            return False
    
    def get_project_milestones(self, project_id: int) -> List[Dict]:
        """Get all milestones for a project with status indicators"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT m.milestone_id, m.milestone_name, m.target_date, 
                   m.actual_date, m.status, m.description,
                   CASE 
                       WHEN m.actual_date IS NOT NULL THEN 'Achieved'
                       WHEN m.target_date < GETDATE() AND m.actual_date IS NULL THEN 'Overdue'
                       WHEN m.target_date <= DATEADD(day, 7, GETDATE()) THEN 'Due Soon'
                       ELSE 'On Track'
                   END as milestone_health
            FROM milestones m
            WHERE m.project_id = ?
            ORDER BY m.target_date
        """, (project_id,))
        
        milestones = cursor.fetchall()
        
        return [
            {
                'milestone_id': m.milestone_id,
                'milestone_name': m.milestone_name,
                'target_date': m.target_date,
                'actual_date': m.actual_date,
                'status': m.status,
                'description': m.description,
                'health': m.milestone_health,
                'days_to_target': (m.target_date - datetime.now().date()).days if m.actual_date is None else None
            } for m in milestones
        ]
    
    def achieve_milestone(self, milestone_id: int, actual_date: datetime = None) -> bool:
        """Mark a milestone as achieved"""
        if actual_date is None:
            actual_date = datetime.now().date()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE milestones 
                SET status = 'Achieved', actual_date = ?
                WHERE milestone_id = ?
            """, (actual_date, milestone_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error achieving milestone: {e}")
            self.conn.rollback()
            return False

# Usage Examples:
if __name__ == "__main__":
    # This would be called from your main application
    from database import get_db_connection
    
    try:
        with get_db_connection("ProjectManagement") as conn:
            task_mgr = TaskManager(conn)
            milestone_mgr = MilestoneManager(conn)
            
            # Create a task with dependencies
            task_data = {
                'task_name': 'Design Review',
                'project_id': 1,
                'start_date': datetime(2025, 9, 15),
                'end_date': datetime(2025, 9, 20),
                'assigned_to': 101,
                'priority': 'High',
                'estimated_hours': 40,
                'predecessor_task_id': 100,  # Depends on task 100
                'description': 'Review architectural designs for compliance'
            }
            
            success = task_mgr.create_task_with_dependencies(task_data)
            if success:
                print("Task created successfully")
    except Exception as e:
        print(f"Error: {e}")
        # Get resource workload
        workload = task_mgr.get_resource_workload(
            user_id=101,
            start_date=datetime(2025, 9, 1),
            end_date=datetime(2025, 9, 30)
        )
        
        print(f"User utilization: {workload['utilization_percentage']:.1f}%")
        if workload['is_overallocated']:
            print("⚠️ User is overallocated!")
        
        conn.close()
