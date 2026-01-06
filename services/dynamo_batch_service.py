"""
Dynamo Batch Service
Manages batch execution of Dynamo scripts using RevitBatchProcessor
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from database import connect_to_db
from constants import schema as S

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamoBatchService:
    """Service for managing batch Dynamo script execution via RevitBatchProcessor"""
    
    def __init__(self, revit_batch_processor_path: str = None):
        """
        Initialize the service
        
        Args:
            revit_batch_processor_path: Path to RevitBatchProcessor.exe
                                       If None, will search common locations
        """
        self.rbp_path = revit_batch_processor_path or self._find_revit_batch_processor()
        if not self.rbp_path:
            logger.warning("RevitBatchProcessor not found in common locations")
    
    def _find_revit_batch_processor(self) -> Optional[str]:
        """Search for RevitBatchProcessor.exe in common locations"""
        common_paths = [
            r"C:\Program Files\RevitBatchProcessor\RevitBatchProcessor.exe",
            r"C:\Program Files (x86)\RevitBatchProcessor\RevitBatchProcessor.exe",
            r"C:\Tools\RevitBatchProcessor\RevitBatchProcessor.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"Found RevitBatchProcessor at: {path}")
                return path
        
        return None
    
    def get_scripts(self, category: str = None, active_only: bool = True) -> List[Dict]:
        """
        Get available Dynamo scripts
        
        Args:
            category: Filter by category (Health Check, QA/QC, Export, Analysis)
            active_only: Only return active scripts
        
        Returns:
            List of script dictionaries
        """
        conn = connect_to_db()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM {S.DynamoScripts.TABLE} WHERE 1=1"
            params = []
            
            if active_only:
                query += f" AND {S.DynamoScripts.IS_ACTIVE} = ?"
                params.append(True)
            
            if category:
                query += f" AND {S.DynamoScripts.CATEGORY} = ?"
                params.append(category)
            
            query += f" ORDER BY {S.DynamoScripts.CATEGORY}, {S.DynamoScripts.SCRIPT_NAME}"
            
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            scripts = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return scripts
        finally:
            conn.close()
    
    def create_job(self, job_name: str, script_id: int, file_paths: List[str],
                   project_id: int = None, created_by: int = None,
                   configuration: Dict = None) -> Optional[int]:
        """
        Create a new batch job
        
        Args:
            job_name: Name for the job
            script_id: ID of the script to execute
            file_paths: List of Revit file paths to process
            project_id: Optional project ID
            created_by: Optional user ID
            configuration: Job configuration dict with options:
                - detach_from_central: bool (default True)
                - audit_on_opening: bool (default True)
                - close_all_worksets: bool (default False)
                - discard_worksets: bool (default False)
                - timeout_minutes: int (default 30)
        
        Returns:
            Job ID if successful, None otherwise
        """
        conn = connect_to_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Get script details
            cursor.execute(f"""
                SELECT {S.DynamoScripts.SCRIPT_PATH}, {S.DynamoScripts.OUTPUT_FOLDER}
                FROM {S.DynamoScripts.TABLE}
                WHERE {S.DynamoScripts.SCRIPT_ID} = ?
            """, (script_id,))
            
            script_data = cursor.fetchone()
            if not script_data:
                logger.error(f"Script ID {script_id} not found")
                return None
            
            script_path, output_folder = script_data
            
            # Default configuration
            config = {
                'detach_from_central': True,
                'audit_on_opening': True,
                'close_all_worksets': False,
                'discard_worksets': False,
                'timeout_minutes': 30
            }
            if configuration:
                config.update(configuration)
            
            # Create job record
            cursor.execute(f"""
                INSERT INTO {S.DynamoBatchJobs.TABLE} (
                    {S.DynamoBatchJobs.JOB_NAME},
                    {S.DynamoBatchJobs.SCRIPT_ID},
                    {S.DynamoBatchJobs.PROJECT_ID},
                    {S.DynamoBatchJobs.CREATED_BY},
                    {S.DynamoBatchJobs.STATUS},
                    {S.DynamoBatchJobs.TOTAL_FILES},
                    {S.DynamoBatchJobs.OUTPUT_FOLDER},
                    {S.DynamoBatchJobs.CONFIGURATION}
                )
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
            """, (
                job_name,
                script_id,
                project_id,
                created_by,
                len(file_paths),
                output_folder or 'C:\\Exports\\DynamoBatch',
                json.dumps(config)
            ))
            
            job_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
            
            # Create file records
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                cursor.execute(f"""
                    INSERT INTO {S.DynamoBatchJobFiles.TABLE} (
                        {S.DynamoBatchJobFiles.JOB_ID},
                        {S.DynamoBatchJobFiles.FILE_PATH},
                        {S.DynamoBatchJobFiles.FILE_NAME},
                        {S.DynamoBatchJobFiles.STATUS}
                    )
                    VALUES (?, ?, ?, 'pending')
                """, (job_id, file_path, file_name))
            
            conn.commit()
            logger.info(f"Created job {job_id} with {len(file_paths)} files")
            return job_id
        
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def execute_job(self, job_id: int) -> Tuple[bool, str]:
        """
        Execute a batch job using RevitBatchProcessor
        
        Args:
            job_id: Job ID to execute
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.rbp_path:
            return False, "RevitBatchProcessor executable not found"
        
        conn = connect_to_db()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            
            # Get job details
            cursor.execute(f"""
                SELECT 
                    j.{S.DynamoBatchJobs.SCRIPT_ID},
                    j.{S.DynamoBatchJobs.OUTPUT_FOLDER},
                    j.{S.DynamoBatchJobs.CONFIGURATION},
                    s.{S.DynamoScripts.SCRIPT_PATH}
                FROM {S.DynamoBatchJobs.TABLE} j
                JOIN {S.DynamoScripts.TABLE} s ON j.{S.DynamoBatchJobs.SCRIPT_ID} = s.{S.DynamoScripts.SCRIPT_ID}
                WHERE j.{S.DynamoBatchJobs.JOB_ID} = ?
            """, (job_id,))
            
            job_data = cursor.fetchone()
            if not job_data:
                return False, f"Job {job_id} not found"
            
            script_id, output_folder, config_json, script_path = job_data
            config = json.loads(config_json) if config_json else {}
            
            # Get file list
            cursor.execute(f"""
                SELECT {S.DynamoBatchJobFiles.FILE_PATH}
                FROM {S.DynamoBatchJobFiles.TABLE}
                WHERE {S.DynamoBatchJobFiles.JOB_ID} = ?
                AND {S.DynamoBatchJobFiles.STATUS} = 'pending'
            """, (job_id,))
            
            file_paths = [row[0] for row in cursor.fetchall()]
            
            if not file_paths:
                return False, "No files to process"
            
            # Update job status to 'queued'
            cursor.execute(f"""
                UPDATE {S.DynamoBatchJobs.TABLE}
                SET {S.DynamoBatchJobs.STATUS} = 'queued',
                    {S.DynamoBatchJobs.START_TIME} = ?
                WHERE {S.DynamoBatchJobs.JOB_ID} = ?
            """, (datetime.now(), job_id))
            conn.commit()
            
            # Create RevitBatchProcessor task file
            task_file_path = self._create_task_file(
                job_id, script_path, file_paths, output_folder, config
            )
            
            # Update task file path
            cursor.execute(f"""
                UPDATE {S.DynamoBatchJobs.TABLE}
                SET {S.DynamoBatchJobs.TASK_FILE_PATH} = ?
                WHERE {S.DynamoBatchJobs.JOB_ID} = ?
            """, (task_file_path, job_id))
            conn.commit()
            
            logger.info(f"Job {job_id} queued with task file: {task_file_path}")
            return True, f"Job queued successfully. Task file: {task_file_path}"
        
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            return False, str(e)
        finally:
            conn.close()
    
    def _create_task_file(self, job_id: int, script_path: str, file_paths: List[str],
                         output_folder: str, config: Dict) -> str:
        """
        Create RevitBatchProcessor task JSON file
        
        Args:
            job_id: Job ID
            script_path: Path to Dynamo script
            file_paths: List of Revit files
            output_folder: Output folder path
            config: Job configuration
        
        Returns:
            Path to created task file
        """
        task_folder = Path("C:/Temp/DynamoBatchTasks")
        task_folder.mkdir(parents=True, exist_ok=True)
        
        task_file = task_folder / f"job_{job_id}_{uuid.uuid4().hex[:8]}.json"
        
        task_config = {
            "TaskScript": script_path,
            "RevitFileList": file_paths,
            "AuditOnOpening": config.get('audit_on_opening', True),
            "DetachFromCentral": config.get('detach_from_central', True),
            "CloseAllWorksets": config.get('close_all_worksets', False),
            "DiscardWorksets": config.get('discard_worksets', False),
            "TimeoutMinutes": config.get('timeout_minutes', 30),
            "LogFolder": output_folder
        }
        
        with open(task_file, 'w') as f:
            json.dump(task_config, f, indent=2)
        
        logger.info(f"Created task file: {task_file}")
        return str(task_file)
    
    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """Get job status and details"""
        conn = connect_to_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    j.*,
                    s.{S.DynamoScripts.SCRIPT_NAME},
                    s.{S.DynamoScripts.CATEGORY}
                FROM {S.DynamoBatchJobs.TABLE} j
                JOIN {S.DynamoScripts.TABLE} s ON j.{S.DynamoBatchJobs.SCRIPT_ID} = s.{S.DynamoScripts.SCRIPT_ID}
                WHERE j.{S.DynamoBatchJobs.JOB_ID} = ?
            """, (job_id,))
            
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            
            if not row:
                return None
            
            job = dict(zip(columns, row))
            
            # Get file-level details
            cursor.execute(f"""
                SELECT {S.DynamoBatchJobFiles.STATUS}, COUNT(*) as count
                FROM {S.DynamoBatchJobFiles.TABLE}
                WHERE {S.DynamoBatchJobFiles.JOB_ID} = ?
                GROUP BY {S.DynamoBatchJobFiles.STATUS}
            """, (job_id,))
            
            job['file_status_breakdown'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return job
        finally:
            conn.close()
    
    def get_jobs(self, project_id: int = None, status: str = None,
                 limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of jobs with optional filters"""
        conn = connect_to_db()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = f"""
                SELECT 
                    j.*,
                    s.{S.DynamoScripts.SCRIPT_NAME},
                    s.{S.DynamoScripts.CATEGORY}
                FROM {S.DynamoBatchJobs.TABLE} j
                JOIN {S.DynamoScripts.TABLE} s ON j.{S.DynamoBatchJobs.SCRIPT_ID} = s.{S.DynamoScripts.SCRIPT_ID}
                WHERE 1=1
            """
            params = []
            
            if project_id:
                query += f" AND j.{S.DynamoBatchJobs.PROJECT_ID} = ?"
                params.append(project_id)
            
            if status:
                query += f" AND j.{S.DynamoBatchJobs.STATUS} = ?"
                params.append(status)
            
            query += f" ORDER BY j.{S.DynamoBatchJobs.CREATED_DATE} DESC"
            query += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return jobs
        finally:
            conn.close()


if __name__ == '__main__':
    # Test the service
    service = DynamoBatchService()
    
    # List available scripts
    scripts = service.get_scripts()
    print(f"\n=== Available Scripts ({len(scripts)}) ===")
    for script in scripts:
        print(f"  [{script['script_id']}] {script['script_name']} ({script['category']})")
