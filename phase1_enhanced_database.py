"""
Enhanced Database Module for Phase 1 Improvements
Extends existing database.py with new functionality for tasks, milestones, and resource management
"""

import pyodbc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from database import connect_to_db

class EnhancedTaskManager:
    """Enhanced task management with dependencies, progress tracking, and resource allocation"""
    
    def __init__(self, db_name="ProjectManagement"):
        self.db_name = db_name
    
    def get_connection(self):
        """Get database connection"""
        return connect_to_db(self.db_name)
    
    def create_task_with_dependencies(self, task_data: Dict) -> bool:
        """Create a task with dependency relationships and resource allocation"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Insert main task
            cursor.execute("""
                INSERT INTO tasks (
                    task_name, project_id, start_date, end_date, assigned_to, 
                    priority, estimated_hours, predecessor_task_id, progress_percentage,
                    description, status, task_type, review_id, created_at, updated_at
                ) 
                OUTPUT INSERTED.task_id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                task_data['task_name'],
                task_data['project_id'],
                task_data['start_date'],
                task_data['end_date'],
                task_data.get('assigned_to'),
                task_data.get('priority', 'Medium'),
                task_data.get('estimated_hours', 0),
                task_data.get('predecessor_task_id'),
                task_data.get('progress_percentage', 0),
                task_data.get('description', ''),
                task_data.get('status', 'Not Started'),
                task_data.get('task_type', 'General'),
                task_data.get('review_id')
            ))
            
            task_id = cursor.fetchone()[0]
            
            # If there are additional team members, create task assignments
            if 'team_members' in task_data:
                for member in task_data['team_members']:
                    cursor.execute("""
                        INSERT INTO task_assignments (task_id, user_id, allocated_hours, role_in_task)
                        VALUES (?, ?, ?, ?)
                    """, (
                        task_id,
                        member['user_id'],
                        member.get('allocated_hours', 0),
                        member.get('role', 'Support')
                    ))
            
            conn.commit()
            print(f"✅ Task created successfully with ID: {task_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_task_progress(self, task_id: int, progress_percentage: int, 
                           actual_hours: float = None, comment: str = None,
                           user_id: int = None) -> bool:
        """Update task progress with automatic status management"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Determine status based on progress
            if progress_percentage == 0:
                status = 'Not Started'
            elif progress_percentage == 100:
                status = 'Complete'
            elif progress_percentage > 0:
                status = 'In Progress'
            
            # Update task
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
            
            # Add comment if provided
            if comment and user_id:
                cursor.execute("""
                    INSERT INTO task_comments (task_id, user_id, comment_text)
                    VALUES (?, ?, ?)
                """, (task_id, user_id, comment))
            
            # Check and update successor tasks if this task is complete
            if status == 'Complete':
                self._check_successor_tasks(cursor, task_id)
            
            conn.commit()
            print(f"✅ Task {task_id} progress updated to {progress_percentage}%")
            return True
            
        except Exception as e:
            print(f"❌ Error updating task progress: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def _check_successor_tasks(self, cursor, completed_task_id: int):
        """Check and update successor tasks when predecessor is complete"""
        # Find tasks that depend on the completed task
        cursor.execute("""
            SELECT task_id, task_name FROM tasks 
            WHERE predecessor_task_id = ? AND status = 'Not Started'
        """, (completed_task_id,))
        
        successor_tasks = cursor.fetchall()
        
        # Update successor tasks to 'Ready to Start' status
        for task in successor_tasks:
            cursor.execute("""
                UPDATE tasks SET status = 'Ready to Start', updated_at = GETDATE() 
                WHERE task_id = ?
            """, (task.task_id,))
            print(f"🚀 Task '{task.task_name}' is now ready to start")
    
    def get_project_task_hierarchy(self, project_id: int) -> List[Dict]:
        """Get project tasks with dependency hierarchy"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    t.task_id, t.task_name, t.start_date, t.end_date, 
                    t.estimated_hours, t.actual_hours, t.progress_percentage,
                    t.priority, t.status, t.predecessor_task_id,
                    u.name as assigned_user, pred.task_name as predecessor_name,
                    CASE 
                        WHEN t.end_date < GETDATE() AND t.progress_percentage < 100 THEN 'Overdue'
                        WHEN t.end_date <= DATEADD(day, 3, GETDATE()) AND t.progress_percentage < 100 THEN 'Due Soon'
                        WHEN t.progress_percentage = 100 THEN 'Complete'
                        ELSE 'On Track'
                    END as health_status
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.user_id
                LEFT JOIN tasks pred ON t.predecessor_task_id = pred.task_id
                WHERE t.project_id = ?
                ORDER BY t.start_date, t.task_id
            """, (project_id,))
            
            tasks = cursor.fetchall()
            
            return [
                {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'estimated_hours': task.estimated_hours or 0,
                    'actual_hours': task.actual_hours or 0,
                    'progress_percentage': task.progress_percentage,
                    'priority': task.priority,
                    'status': task.status,
                    'assigned_user': task.assigned_user,
                    'predecessor_task_id': task.predecessor_task_id,
                    'predecessor_name': task.predecessor_name,
                    'health_status': task.health_status,
                    'variance_hours': (task.actual_hours or 0) - (task.estimated_hours or 0),
                    'days_remaining': (task.end_date - datetime.now().date()).days if task.end_date else None
                } for task in tasks
            ]
            
        except Exception as e:
            print(f"❌ Error getting project task hierarchy: {e}")
            return []
        finally:
            conn.close()
    
    def get_project_tasks(self, project_id: int) -> List[Dict]:
        """Get all tasks for a project with assigned user names"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    t.task_id, t.task_name, t.start_date, t.end_date, 
                    t.estimated_hours, t.actual_hours, t.progress_percentage,
                    t.priority, t.status, t.predecessor_task_id, t.description,
                    t.task_type, t.review_id, t.cycle_id,
                    u.name as assigned_to_name, u.user_id as assigned_to,
                    CASE 
                        WHEN t.end_date < GETDATE() AND t.progress_percentage < 100 THEN 'Overdue'
                        WHEN t.end_date <= DATEADD(day, 3, GETDATE()) AND t.progress_percentage < 100 THEN 'Warning'
                        WHEN t.progress_percentage = 100 THEN 'Complete'
                        ELSE 'Healthy'
                    END as health_status
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.user_id
                WHERE t.project_id = ?
                ORDER BY t.start_date, t.task_id
            """, (project_id,))
            
            tasks = cursor.fetchall()
            
            return [
                {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'estimated_hours': task.estimated_hours or 0,
                    'actual_hours': task.actual_hours or 0,
                    'progress_percentage': task.progress_percentage or 0,
                    'priority': task.priority,
                    'status': task.status,
                    'predecessor_task_id': task.predecessor_task_id,
                    'description': task.description,
                    'task_type': task.task_type,
                    'review_id': task.review_id,
                    'cycle_id': task.cycle_id,
                    'assigned_to': task.assigned_to,
                    'assigned_to_name': task.assigned_to_name,
                    'health_status': task.health_status
                } for task in tasks
            ]
            
        except Exception as e:
            print(f"❌ Error getting project tasks: {e}")
            return []
        finally:
            conn.close()
    
    def get_tasks_by_review(self, review_id: int) -> List[Dict]:
        """Get all tasks associated with a specific review"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    t.task_id, t.task_name, t.start_date, t.end_date, 
                    t.estimated_hours, t.actual_hours, t.progress_percentage,
                    t.priority, t.status, t.description, t.task_type,
                    u.name as assigned_to_name, u.user_id as assigned_to
                FROM tasks t
                LEFT JOIN users u ON t.assigned_to = u.user_id
                WHERE t.review_id = ?
                ORDER BY t.start_date, t.task_id
            """, (review_id,))
            
            tasks = cursor.fetchall()
            
            return [
                {
                    'task_id': task.task_id,
                    'task_name': task.task_name,
                    'start_date': task.start_date,
                    'end_date': task.end_date,
                    'estimated_hours': task.estimated_hours or 0,
                    'actual_hours': task.actual_hours or 0,
                    'progress_percentage': task.progress_percentage or 0,
                    'priority': task.priority,
                    'status': task.status,
                    'description': task.description,
                    'task_type': task.task_type,
                    'assigned_to': task.assigned_to,
                    'assigned_to_name': task.assigned_to_name
                } for task in tasks
            ]
            
        except Exception as e:
            print(f"❌ Error getting tasks by review: {e}")
            return []
        finally:
            conn.close()
    
    def assign_review_tasks_to_user(self, review_id: int, user_id: int) -> bool:
        """Assign all tasks for a review to a specific user"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Update all tasks for this review
            cursor.execute("""
                UPDATE tasks 
                SET assigned_to = ?, updated_at = GETDATE()
                WHERE review_id = ?
            """, (user_id, review_id))
            
            conn.commit()
            print(f"✅ Assigned all tasks for review {review_id} to user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error assigning review tasks: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_critical_path(self, project_id: int) -> List[Dict]:
        """Calculate and return critical path for a project"""
        tasks = self.get_project_task_hierarchy(project_id)
        
        # Simple critical path calculation
        # In a full implementation, you'd use proper CPM algorithm
        critical_tasks = []
        
        for task in tasks:
            # A task is critical if it has successors and any delay would delay the project
            is_critical = (
                task['health_status'] in ['Overdue', 'Due Soon'] or
                task['predecessor_task_id'] is not None or
                any(t['predecessor_task_id'] == task['task_id'] for t in tasks)
            )
            
            if is_critical:
                task['is_critical'] = True
                critical_tasks.append(task)
        
        return critical_tasks

class MilestoneManager:
    """Milestone management for project tracking"""
    
    def __init__(self, db_name="ProjectManagement"):
        self.db_name = db_name
    
    def get_connection(self):
        return connect_to_db(self.db_name)
    
    def create_milestone(self, milestone_data: Dict) -> bool:
        """Create a new project milestone"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO milestones (
                    project_id, milestone_name, target_date, 
                    description, status, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                milestone_data['project_id'],
                milestone_data['milestone_name'],
                milestone_data['target_date'],
                milestone_data.get('description', ''),
                milestone_data.get('status', 'Pending'),
                milestone_data.get('created_by')
            ))
            
            conn.commit()
            print(f"✅ Milestone '{milestone_data['milestone_name']}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating milestone: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_project_milestones(self, project_id: int) -> List[Dict]:
        """Get all milestones for a project with status indicators"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.milestone_id, m.milestone_name, m.target_date, 
                    m.actual_date, m.status, m.description, m.created_at,
                    u.name as created_by_name,
                    CASE 
                        WHEN m.actual_date IS NOT NULL THEN 'Achieved'
                        WHEN m.target_date < GETDATE() AND m.actual_date IS NULL THEN 'Overdue'
                        WHEN m.target_date <= DATEADD(day, 7, GETDATE()) THEN 'Due Soon'
                        ELSE 'On Track'
                    END as milestone_health,
                    DATEDIFF(day, GETDATE(), m.target_date) as days_to_target
                FROM milestones m
                LEFT JOIN users u ON m.created_by = u.user_id
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
                    'created_by': m.created_by_name,
                    'health': m.milestone_health,
                    'days_to_target': m.days_to_target if m.actual_date is None else None
                } for m in milestones
            ]
            
        except Exception as e:
            print(f"❌ Error getting milestones: {e}")
            return []
        finally:
            conn.close()
    
    def achieve_milestone(self, milestone_id: int, actual_date: datetime = None, user_id: int = None) -> bool:
        """Mark a milestone as achieved"""
        if actual_date is None:
            actual_date = datetime.now().date()
        
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE milestones 
                SET status = 'Achieved', actual_date = ?, updated_at = GETDATE()
                WHERE milestone_id = ?
            """, (actual_date, milestone_id))
            
            conn.commit()
            print(f"🎯 Milestone {milestone_id} achieved on {actual_date}")
            return True
            
        except Exception as e:
            print(f"❌ Error achieving milestone: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

class ResourceManager:
    """Resource allocation and capacity management"""
    
    def __init__(self, db_name="ProjectManagement"):
        self.db_name = db_name
    
    def get_connection(self):
        return connect_to_db(self.db_name)
    
    def get_resource_workload(self, user_id: int = None, start_date: datetime = None, 
                            end_date: datetime = None) -> List[Dict]:
        """Get workload analysis for users within a date range"""
        conn = self.get_connection()
        if not conn:
            return []
        
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=30)
        
        try:
            cursor = conn.cursor()
            
            # Base query for resource utilization (simplified without task_assignments table)
            query = """
                SELECT 
                    u.user_id, u.name, u.role_level, u.weekly_capacity_hours,
                    u.department, u.skills,
                    0 as active_assignments,
                    0 as allocated_hours,
                    0 as total_estimated_hours,
                    0 as total_actual_hours,
                    0 as avg_task_progress
                FROM users u
                WHERE u.is_active = 1
            """
            
            params = []
            
            if user_id:
                query += " AND u.user_id = ?"
                params.append(user_id)
            
            query += " GROUP BY u.user_id, u.name, u.role_level, u.weekly_capacity_hours, u.department, u.skills"
            
            cursor.execute(query, params)
            resources = cursor.fetchall()
            
            result = []
            for resource in resources:
                weekly_capacity = resource.weekly_capacity_hours or 40
                allocated_hours = resource.allocated_hours or 0
                
                utilization_pct = (allocated_hours / weekly_capacity * 100) if weekly_capacity > 0 else 0
                
                workload_status = 'Low'
                if utilization_pct > 100:
                    workload_status = 'Overallocated'
                elif utilization_pct > 80:
                    workload_status = 'High'
                elif utilization_pct > 50:
                    workload_status = 'Medium'
                
                result.append({
                    'user_id': resource.user_id,
                    'name': resource.name,
                    'role_level': resource.role_level,
                    'department': resource.department,
                    'skills': resource.skills,
                    'weekly_capacity_hours': weekly_capacity,
                    'allocated_hours': allocated_hours,
                    'active_assignments': resource.active_assignments or 0,
                    'total_estimated_hours': resource.total_estimated_hours or 0,
                    'total_actual_hours': resource.total_actual_hours or 0,
                    'avg_progress': resource.avg_task_progress or 0,
                    'utilization_percentage': round(utilization_pct, 1),
                    'workload_status': workload_status,
                    'is_overallocated': utilization_pct > 100,
                    'available_hours': max(0, weekly_capacity - allocated_hours)
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting resource workload: {e}")
            return []
        finally:
            conn.close()
    
    def find_available_resources(self, required_skills: List[str] = None, 
                               role_level: str = None, max_utilization: float = 80.0) -> List[Dict]:
        """Find available resources based on skills and current workload"""
        resources = self.get_resource_workload()
        
        available = []
        for resource in resources:
            # Check utilization threshold
            if resource['utilization_percentage'] > max_utilization:
                continue
            
            # Check role level
            if role_level and resource['role_level'] != role_level:
                continue
            
            # Check skills
            if required_skills:
                user_skills = (resource['skills'] or '').lower().split(',')
                user_skills = [skill.strip() for skill in user_skills]
                
                has_required_skills = any(
                    req_skill.lower() in user_skills 
                    for req_skill in required_skills
                )
                
                if not has_required_skills:
                    continue
            
            available.append(resource)
        
        # Sort by utilization (least utilized first)
        return sorted(available, key=lambda x: x['utilization_percentage'])

class ProjectTemplateManager:
    """Project template management for standardized project creation"""
    
    def __init__(self, db_name="ProjectManagement"):
        self.db_name = db_name
    
    def get_connection(self):
        return connect_to_db(self.db_name)
    
    def create_project_from_template(self, project_name: str, template_id: int, 
                                   start_date: datetime, created_by: int) -> bool:
        """Create a new project from a template"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                EXEC sp_CreateProjectFromTemplate ?, ?, ?, ?
            """, (project_name, template_id, start_date, created_by))
            
            result = cursor.fetchone()
            if result:
                print(f"✅ Project created successfully with ID: {result[0]}")
                print(f"📝 {result[1]}")
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error creating project from template: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_project_templates(self) -> List[Dict]:
        """Get all available project templates"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    pt.template_id, pt.template_name, pt.project_type,
                    pt.description, pt.estimated_duration_days,
                    COUNT(tt.template_task_id) as task_count
                FROM project_templates pt
                LEFT JOIN template_tasks tt ON pt.template_id = tt.template_id
                WHERE pt.is_active = 1
                GROUP BY pt.template_id, pt.template_name, pt.project_type,
                         pt.description, pt.estimated_duration_days
                ORDER BY pt.template_name
            """)
            
            templates = cursor.fetchall()
            
            return [
                {
                    'template_id': t.template_id,
                    'template_name': t.template_name,
                    'project_type': t.project_type,
                    'description': t.description,
                    'estimated_duration_days': t.estimated_duration_days,
                    'task_count': t.task_count
                } for t in templates
            ]
            
        except Exception as e:
            print(f"❌ Error getting templates: {e}")
            return []
        finally:
            conn.close()

# Usage example functions
def example_phase1_usage():
    """Example usage of Phase 1 enhancements"""
    
    # Initialize managers
    task_mgr = EnhancedTaskManager()
    milestone_mgr = MilestoneManager()
    resource_mgr = ResourceManager()
    template_mgr = ProjectTemplateManager()
    
    # 1. Create a project from template
    print("=== Creating Project from Template ===")
    templates = template_mgr.get_project_templates()
    if templates:
        success = template_mgr.create_project_from_template(
            project_name="New Residential Development",
            template_id=templates[0]['template_id'],
            start_date=datetime.now(),
            created_by=1  # Assuming user ID 1
        )
        print(f"Template project creation: {'Success' if success else 'Failed'}")
    
    # 2. Create milestones
    print("\n=== Creating Milestones ===")
    milestone_data = {
        'project_id': 1,
        'milestone_name': 'Design Phase Complete',
        'target_date': datetime.now() + timedelta(days=30),
        'description': 'All design deliverables completed and approved',
        'created_by': 1
    }
    milestone_mgr.create_milestone(milestone_data)
    
    # 3. Check resource utilization
    print("\n=== Resource Utilization Analysis ===")
    resources = resource_mgr.get_resource_workload()
    for resource in resources[:3]:  # Show first 3 resources
        print(f"👤 {resource['name']} ({resource['role_level']})")
        print(f"   Utilization: {resource['utilization_percentage']}% - {resource['workload_status']}")
        print(f"   Active assignments: {resource['active_assignments']}")
        print(f"   Available hours: {resource['available_hours']}")
    
    # 4. Find available resources
    print("\n=== Finding Available Resources ===")
    available = resource_mgr.find_available_resources(
        required_skills=['BIM', 'Revit'],
        role_level='Senior',
        max_utilization=75.0
    )
    
    if available:
        print("Available senior BIM resources:")
        for resource in available[:2]:  # Show first 2
            print(f"👤 {resource['name']} - {resource['utilization_percentage']}% utilized")
    else:
        print("No available resources matching criteria")

if __name__ == "__main__":
    example_phase1_usage()
