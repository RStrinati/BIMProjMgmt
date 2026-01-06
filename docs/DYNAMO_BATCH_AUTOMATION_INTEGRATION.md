# Dynamo Batch Automation Integration Plan

## Overview

This document outlines the integration strategy for DynamoAutomation and BIM-Automation-Tool into the BIM Project Management System, enabling automated batch processing of Revit files with Dynamo scripts.

## Integration Architecture

### Current System Capabilities

Your application already has:
- ✅ **Project folder management** - Each project has `folder_path` (model files) and `ifc_folder_path`
- ✅ **File tracking** - `tblACCDocs` table for tracking Revit files per project
- ✅ **Service & task management** - Structured workflow for project services and tasks
- ✅ **Data import handlers** - Pattern for batch importing external data (ACC, Revit Health)
- ✅ **React UI with Material-UI** - Modern frontend for building new features
- ✅ **Background process management** - Experience with Revizto CLI integration

### Proposed Architecture

```
Project Management System
    ↓
[Batch Processing Service]
    ↓
┌─────────────────────────────────┐
│   DynamoAutomation Wrapper      │
│   (Python subprocess)           │
└─────────────────────────────────┘
    ↓
DynamoAutomation Engine (C#)
    ↓
Batch Process Multiple RVT Files
    ↓
[Results → Database → Reports]
```

## Integration Phases

### Phase 1: Backend Service Layer (Python)

Create a new service: `services/dynamo_batch_service.py`

#### 1.1 Core Service Structure

```python
# services/dynamo_batch_service.py
import os
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from config import Config
from constants import schema as S
from database import get_db_connection, get_project_folders


class DynamoBatchService:
    """
    Service for managing Dynamo batch automation operations.
    Wraps DynamoAutomation or similar batch processing tools.
    """
    
    def __init__(self, dynamo_exe_path: str = None):
        """
        Initialize the service with path to DynamoAutomation executable.
        
        Args:
            dynamo_exe_path: Path to DynamoAutomation.exe or batch processor
        """
        self.dynamo_exe_path = dynamo_exe_path or self._find_dynamo_automation()
        if not self.dynamo_exe_path:
            raise FileNotFoundError("DynamoAutomation executable not found")
    
    def _find_dynamo_automation(self) -> Optional[str]:
        """Locate DynamoAutomation executable."""
        possible_paths = [
            # Services folder (preferred)
            r"services\dynamo-automation\DynamoAutomation.exe",
            # Common install locations
            r"C:\Program Files\DynamoAutomation\DynamoAutomation.exe",
            r"C:\Tools\DynamoAutomation\DynamoAutomation.exe",
        ]
        
        project_root = Path(__file__).parent.parent
        for path in possible_paths:
            full_path = project_root / path if not os.path.isabs(path) else Path(path)
            if full_path.exists():
                return str(full_path)
        return None
    
    def create_batch_job(self, project_id: int, script_path: str, 
                        file_filter: str = "*.rvt",
                        options: Dict = None) -> int:
        """
        Create a new batch processing job.
        
        Args:
            project_id: Project ID to process files for
            script_path: Path to Dynamo script (.dyn file)
            file_filter: File pattern to match (e.g., "*.rvt", "*_ARCH_*.rvt")
            options: Additional processing options
            
        Returns:
            batch_job_id: ID of created batch job
        """
        # Get project folder
        folder_path, _ = get_project_folders(project_id)
        if not folder_path or not os.path.exists(folder_path):
            raise ValueError(f"Project folder not found for project {project_id}")
        
        # Create batch job record
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {S.DynamoBatchJobs.TABLE} (
                    {S.DynamoBatchJobs.PROJECT_ID},
                    {S.DynamoBatchJobs.SCRIPT_PATH},
                    {S.DynamoBatchJobs.SOURCE_FOLDER},
                    {S.DynamoBatchJobs.FILE_FILTER},
                    {S.DynamoBatchJobs.STATUS},
                    {S.DynamoBatchJobs.OPTIONS_JSON},
                    {S.DynamoBatchJobs.CREATED_AT}
                ) VALUES (?, ?, ?, ?, 'pending', ?, GETDATE())
            """, (
                project_id,
                script_path,
                folder_path,
                file_filter,
                json.dumps(options or {})
            ))
            conn.commit()
            
            # Get the created job ID
            cursor.execute("SELECT @@IDENTITY")
            job_id = cursor.fetchone()[0]
            return job_id
    
    def execute_batch_job(self, job_id: int) -> Dict:
        """
        Execute a batch processing job using DynamoAutomation.
        
        Args:
            job_id: Batch job ID to execute
            
        Returns:
            Dict with execution results
        """
        # Get job details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {S.DynamoBatchJobs.PROJECT_ID}, 
                       {S.DynamoBatchJobs.SCRIPT_PATH},
                       {S.DynamoBatchJobs.SOURCE_FOLDER},
                       {S.DynamoBatchJobs.FILE_FILTER},
                       {S.DynamoBatchJobs.OPTIONS_JSON}
                FROM {S.DynamoBatchJobs.TABLE}
                WHERE {S.DynamoBatchJobs.ID} = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Batch job {job_id} not found")
            
            project_id, script_path, source_folder, file_filter, options_json = row
            options = json.loads(options_json) if options_json else {}
        
        # Update status to running
        self._update_job_status(job_id, 'running')
        
        try:
            # Build command for DynamoAutomation
            command = [
                self.dynamo_exe_path,
                script_path,
                source_folder,
                "--filter", file_filter,
            ]
            
            # Add options
            if options.get('revit_version'):
                command.extend(["--revit-version", options['revit_version']])
            if options.get('log_path'):
                command.extend(["--log", options['log_path']])
            
            # Execute
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Parse results
            success = result.returncode == 0
            
            # Update job with results
            self._update_job_results(
                job_id,
                status='completed' if success else 'failed',
                stdout=result.stdout,
                stderr=result.stderr,
                files_processed=self._count_processed_files(result.stdout)
            )
            
            return {
                'success': success,
                'job_id': job_id,
                'files_processed': self._count_processed_files(result.stdout),
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            self._update_job_status(job_id, 'failed', str(e))
            raise
    
    def get_batch_jobs(self, project_id: int = None, 
                       status: str = None,
                       limit: int = 50) -> List[Dict]:
        """Get list of batch jobs with optional filters."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            where_clauses = []
            params = []
            
            if project_id:
                where_clauses.append(f"{S.DynamoBatchJobs.PROJECT_ID} = ?")
                params.append(project_id)
            
            if status:
                where_clauses.append(f"{S.DynamoBatchJobs.STATUS} = ?")
                params.append(status)
            
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            cursor.execute(f"""
                SELECT 
                    {S.DynamoBatchJobs.ID},
                    {S.DynamoBatchJobs.PROJECT_ID},
                    {S.DynamoBatchJobs.SCRIPT_PATH},
                    {S.DynamoBatchJobs.STATUS},
                    {S.DynamoBatchJobs.FILES_PROCESSED},
                    {S.DynamoBatchJobs.CREATED_AT},
                    {S.DynamoBatchJobs.COMPLETED_AT}
                FROM {S.DynamoBatchJobs.TABLE}
                {where_sql}
                ORDER BY {S.DynamoBatchJobs.CREATED_AT} DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
            """, params + [limit])
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _update_job_status(self, job_id: int, status: str, error: str = None):
        """Update job status."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if status in ('completed', 'failed'):
                cursor.execute(f"""
                    UPDATE {S.DynamoBatchJobs.TABLE}
                    SET {S.DynamoBatchJobs.STATUS} = ?,
                        {S.DynamoBatchJobs.ERROR_MESSAGE} = ?,
                        {S.DynamoBatchJobs.COMPLETED_AT} = GETDATE()
                    WHERE {S.DynamoBatchJobs.ID} = ?
                """, (status, error, job_id))
            else:
                cursor.execute(f"""
                    UPDATE {S.DynamoBatchJobs.TABLE}
                    SET {S.DynamoBatchJobs.STATUS} = ?,
                        {S.DynamoBatchJobs.ERROR_MESSAGE} = ?
                    WHERE {S.DynamoBatchJobs.ID} = ?
                """, (status, error, job_id))
            conn.commit()
    
    def _update_job_results(self, job_id: int, status: str, 
                           stdout: str, stderr: str, files_processed: int):
        """Update job with execution results."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE {S.DynamoBatchJobs.TABLE}
                SET {S.DynamoBatchJobs.STATUS} = ?,
                    {S.DynamoBatchJobs.FILES_PROCESSED} = ?,
                    {S.DynamoBatchJobs.LOG_OUTPUT} = ?,
                    {S.DynamoBatchJobs.ERROR_MESSAGE} = ?,
                    {S.DynamoBatchJobs.COMPLETED_AT} = GETDATE()
                WHERE {S.DynamoBatchJobs.ID} = ?
            """, (status, files_processed, stdout, stderr, job_id))
            conn.commit()
    
    def _count_processed_files(self, output: str) -> int:
        """Parse stdout to count processed files."""
        # This depends on DynamoAutomation output format
        # Adjust based on actual tool output
        import re
        match = re.search(r'Processed (\d+) files', output)
        return int(match.group(1)) if match else 0
```

#### 1.2 Database Schema Addition

Add to `constants/schema.py`:

```python
class DynamoBatchJobs:
    """tblDynamoBatchJobs - Dynamo batch processing jobs"""
    TABLE = "tblDynamoBatchJobs"
    ID = "batch_job_id"
    PROJECT_ID = "project_id"
    SCRIPT_PATH = "script_path"
    SCRIPT_NAME = "script_name"
    SOURCE_FOLDER = "source_folder"
    FILE_FILTER = "file_filter"
    STATUS = "status"  # 'pending', 'running', 'completed', 'failed'
    FILES_PROCESSED = "files_processed"
    OPTIONS_JSON = "options_json"
    LOG_OUTPUT = "log_output"
    ERROR_MESSAGE = "error_message"
    CREATED_AT = "created_at"
    COMPLETED_AT = "completed_at"
    CREATED_BY = "created_by"


class DynamoScripts:
    """tblDynamoScripts - Registered Dynamo scripts"""
    TABLE = "tblDynamoScripts"
    ID = "script_id"
    SCRIPT_NAME = "script_name"
    SCRIPT_PATH = "script_path"
    DESCRIPTION = "description"
    CATEGORY = "category"  # 'export', 'validation', 'cleanup', 'custom'
    PARAMETERS_JSON = "parameters_json"
    IS_ACTIVE = "is_active"
    CREATED_AT = "created_at"
```

Create SQL migration script `sql/migrations/add_dynamo_batch_tables.sql`:

```sql
-- Create tblDynamoBatchJobs
CREATE TABLE dbo.tblDynamoBatchJobs (
    batch_job_id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    script_path NVARCHAR(500) NOT NULL,
    script_name NVARCHAR(255),
    source_folder NVARCHAR(500),
    file_filter NVARCHAR(100) DEFAULT '*.rvt',
    status NVARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    files_processed INT DEFAULT 0,
    options_json NVARCHAR(MAX),
    log_output NVARCHAR(MAX),
    error_message NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    completed_at DATETIME2,
    created_by NVARCHAR(100),
    CONSTRAINT FK_DynamoBatchJobs_Projects FOREIGN KEY (project_id) 
        REFERENCES dbo.tblProjects(project_id) ON DELETE CASCADE
);

-- Create tblDynamoScripts
CREATE TABLE dbo.tblDynamoScripts (
    script_id INT IDENTITY(1,1) PRIMARY KEY,
    script_name NVARCHAR(255) NOT NULL,
    script_path NVARCHAR(500) NOT NULL,
    description NVARCHAR(MAX),
    category NVARCHAR(50), -- 'export', 'validation', 'cleanup', 'custom'
    parameters_json NVARCHAR(MAX),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Create indexes
CREATE INDEX IX_DynamoBatchJobs_ProjectId ON dbo.tblDynamoBatchJobs(project_id);
CREATE INDEX IX_DynamoBatchJobs_Status ON dbo.tblDynamoBatchJobs(status);
CREATE INDEX IX_DynamoBatchJobs_CreatedAt ON dbo.tblDynamoBatchJobs(created_at DESC);
```

### Phase 2: Backend API Endpoints

Add to `backend/app.py`:

```python
# --- Dynamo Batch Automation API Endpoints ---

@app.route('/api/projects/<int:project_id>/dynamo/scripts', methods=['GET'])
def get_dynamo_scripts(project_id):
    """Get list of available Dynamo scripts."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT {S.DynamoScripts.ID}, {S.DynamoScripts.SCRIPT_NAME},
                       {S.DynamoScripts.DESCRIPTION}, {S.DynamoScripts.CATEGORY},
                       {S.DynamoScripts.SCRIPT_PATH}
                FROM {S.DynamoScripts.TABLE}
                WHERE {S.DynamoScripts.IS_ACTIVE} = 1
                ORDER BY {S.DynamoScripts.CATEGORY}, {S.DynamoScripts.SCRIPT_NAME}
            """)
            
            scripts = []
            for row in cursor.fetchall():
                scripts.append({
                    'script_id': row[0],
                    'script_name': row[1],
                    'description': row[2],
                    'category': row[3],
                    'script_path': row[4]
                })
            
            return jsonify({'scripts': scripts})
    except Exception as e:
        logging.exception("Error fetching Dynamo scripts")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/dynamo/batch-jobs', methods=['POST'])
def create_dynamo_batch_job(project_id):
    """Create a new Dynamo batch processing job."""
    try:
        from services.dynamo_batch_service import DynamoBatchService
        
        body = request.get_json() or {}
        script_path = body.get('script_path')
        file_filter = body.get('file_filter', '*.rvt')
        options = body.get('options', {})
        
        if not script_path:
            return jsonify({'error': 'script_path is required'}), 400
        
        service = DynamoBatchService()
        job_id = service.create_batch_job(
            project_id=project_id,
            script_path=script_path,
            file_filter=file_filter,
            options=options
        )
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Batch job created successfully'
        }), 201
        
    except Exception as e:
        logging.exception("Error creating Dynamo batch job")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/dynamo/batch-jobs/<int:job_id>/execute', methods=['POST'])
def execute_dynamo_batch_job(project_id, job_id):
    """Execute a Dynamo batch processing job."""
    try:
        from services.dynamo_batch_service import DynamoBatchService
        
        service = DynamoBatchService()
        result = service.execute_batch_job(job_id)
        
        return jsonify(result)
        
    except Exception as e:
        logging.exception("Error executing Dynamo batch job")
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/dynamo/batch-jobs', methods=['GET'])
def get_dynamo_batch_jobs(project_id):
    """Get list of batch jobs for a project."""
    try:
        from services.dynamo_batch_service import DynamoBatchService
        
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        service = DynamoBatchService()
        jobs = service.get_batch_jobs(
            project_id=project_id,
            status=status,
            limit=limit
        )
        
        return jsonify({'jobs': jobs})
        
    except Exception as e:
        logging.exception("Error fetching Dynamo batch jobs")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dynamo/check-installation', methods=['GET'])
def check_dynamo_installation():
    """Check if DynamoAutomation is installed and accessible."""
    try:
        from services.dynamo_batch_service import DynamoBatchService
        
        service = DynamoBatchService()
        
        return jsonify({
            'installed': True,
            'path': service.dynamo_exe_path,
            'message': 'DynamoAutomation is installed and accessible'
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'installed': False,
            'error': str(e),
            'message': 'DynamoAutomation not found. Please install or configure path.'
        }), 404
    except Exception as e:
        logging.exception("Error checking Dynamo installation")
        return jsonify({'error': str(e)}), 500
```

### Phase 3: Frontend Integration

#### 3.1 Create Dynamo Batch Panel Component

Create `frontend/src/components/dataImports/DynamoBatchPanel.tsx`:

```typescript
/**
 * Dynamo Batch Processing Panel
 * Allows users to run Dynamo scripts on multiple Revit files
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { formatDate } from '@/utils/dateUtils';

interface DynamoBatchPanelProps {
  projectId: number;
  projectName: string;
}

export const DynamoBatchPanel: React.FC<DynamoBatchPanelProps> = ({
  projectId,
  projectName,
}) => {
  const queryClient = useQueryClient();
  const [selectedScript, setSelectedScript] = useState('');
  const [fileFilter, setFileFilter] = useState('*.rvt');
  const [executing, setExecuting] = useState(false);

  // Check if DynamoAutomation is installed
  const { data: installStatus } = useQuery({
    queryKey: ['dynamo-installation'],
    queryFn: async () => {
      const response = await axios.get('/api/dynamo/check-installation');
      return response.data;
    },
  });

  // Get available Dynamo scripts
  const { data: scriptsData, isLoading: scriptsLoading } = useQuery({
    queryKey: ['dynamo-scripts', projectId],
    queryFn: async () => {
      const response = await axios.get(`/api/projects/${projectId}/dynamo/scripts`);
      return response.data;
    },
  });

  // Get batch jobs
  const { data: jobsData, isLoading: jobsLoading, refetch: refetchJobs } = useQuery({
    queryKey: ['dynamo-batch-jobs', projectId],
    queryFn: async () => {
      const response = await axios.get(`/api/projects/${projectId}/dynamo/batch-jobs`);
      return response.data;
    },
  });

  // Create batch job mutation
  const createJobMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(
        `/api/projects/${projectId}/dynamo/batch-jobs`,
        {
          script_path: selectedScript,
          file_filter: fileFilter,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      refetchJobs();
    },
  });

  // Execute job mutation
  const executeJobMutation = useMutation({
    mutationFn: async (jobId: number) => {
      setExecuting(true);
      const response = await axios.post(
        `/api/projects/${projectId}/dynamo/batch-jobs/${jobId}/execute`
      );
      return response.data;
    },
    onSuccess: () => {
      refetchJobs();
      setExecuting(false);
    },
    onError: () => {
      setExecuting(false);
    },
  });

  const handleCreateAndExecute = async () => {
    if (!selectedScript) return;

    try {
      const createResult = await createJobMutation.mutateAsync();
      if (createResult.success) {
        await executeJobMutation.mutateAsync(createResult.job_id);
      }
    } catch (error) {
      console.error('Error creating/executing batch job:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <CircularProgress size={20} />;
      default:
        return <PendingIcon color="action" />;
    }
  };

  const getStatusChip = (status: string) => {
    const colors = {
      completed: 'success',
      failed: 'error',
      running: 'info',
      pending: 'default',
    };
    return (
      <Chip
        label={status.toUpperCase()}
        color={colors[status] || 'default'}
        size="small"
      />
    );
  };

  if (!installStatus?.installed) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="warning">
          DynamoAutomation is not installed or not found. Please install DynamoAutomation
          from GitHub and configure the path in your system.
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Dynamo Batch Processing
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Execute Dynamo scripts on multiple Revit files in the project folder.
      </Typography>

      {/* Script Selection */}
      <Box sx={{ mb: 3 }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Select Dynamo Script</InputLabel>
          <Select
            value={selectedScript}
            onChange={(e) => setSelectedScript(e.target.value)}
            disabled={scriptsLoading}
          >
            {scriptsData?.scripts?.map((script) => (
              <MenuItem key={script.script_id} value={script.script_path}>
                {script.script_name} - {script.description}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="File Filter"
          value={fileFilter}
          onChange={(e) => setFileFilter(e.target.value)}
          placeholder="*.rvt or *_ARCH_*.rvt"
          helperText="Pattern to match Revit files (e.g., *.rvt for all files)"
          sx={{ mb: 2 }}
        />

        <Button
          variant="contained"
          startIcon={executing ? <CircularProgress size={20} /> : <PlayIcon />}
          onClick={handleCreateAndExecute}
          disabled={!selectedScript || executing}
          fullWidth
        >
          {executing ? 'Processing...' : 'Create and Execute Batch Job'}
        </Button>
      </Box>

      {/* Batch Jobs History */}
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Batch Jobs History</Typography>
          <IconButton onClick={() => refetchJobs()} size="small">
            <RefreshIcon />
          </IconButton>
        </Box>

        {jobsLoading ? (
          <CircularProgress />
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Script</TableCell>
                  <TableCell>Files Processed</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobsData?.jobs?.map((job) => (
                  <TableRow key={job.batch_job_id}>
                    <TableCell>{getStatusChip(job.status)}</TableCell>
                    <TableCell>{job.script_name || job.script_path}</TableCell>
                    <TableCell>{job.files_processed || 0}</TableCell>
                    <TableCell>{formatDate(job.created_at)}</TableCell>
                    <TableCell>{formatDate(job.completed_at)}</TableCell>
                    <TableCell>
                      {job.status === 'pending' && (
                        <Tooltip title="Execute">
                          <IconButton
                            size="small"
                            onClick={() => executeJobMutation.mutate(job.batch_job_id)}
                          >
                            <PlayIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Paper>
  );
};
```

#### 3.2 Add to Data Imports Page

Update `frontend/src/pages/DataImportsPage.tsx` to include the new tab:

```typescript
// Add import
import { DynamoBatchPanel } from '@/components/dataImports/DynamoBatchPanel';

// Add to tabs array (around line 80)
const tabs = [
  { label: 'ACC Desktop Connector', icon: <CloudDownloadIcon />, value: 0 },
  { label: 'ACC Data Import', icon: <UploadIcon />, value: 1 },
  { label: 'ACC Sync (APS)', icon: <SyncIcon />, value: 2 },
  { label: 'Revizto Issues', icon: <ReviztoIcon />, value: 3 },
  { label: 'Revit Health', icon: <HealthIcon />, value: 4 },
  { label: 'Dynamo Batch', icon: <AutomationIcon />, value: 5 }, // NEW
];

// Add tab panel (around line 200)
<TabPanel value={activeTab} index={5}>
  {selectedProject && (
    <DynamoBatchPanel
      projectId={selectedProject.project_id}
      projectName={selectedProject.project_name}
    />
  )}
</TabPanel>
```

### Phase 4: Integration with Project Services

#### 4.1 Link to Service Templates

You can create service templates that trigger Dynamo batch processing:

```python
# In review_management_service.py or new service file

def create_dynamo_service_template():
    """Create service template for Dynamo batch operations."""
    template = {
        'name': 'Model Quality Check - Batch',
        'sector': 'Quality Assurance',
        'items': [
            {
                'service_code': 'QA-DYNAMO-01',
                'service_name': 'Batch Model Validation',
                'unit_type': 'lump_sum',
                'lump_sum_fee': 500.00,
                'notes': 'Automated Dynamo validation on all models'
            }
        ]
    }
    return template
```

#### 4.2 Task Integration

Link Dynamo batch jobs to tasks:

```python
# Add foreign key to tblDynamoBatchJobs
ALTER TABLE dbo.tblDynamoBatchJobs
ADD task_id INT NULL,
CONSTRAINT FK_DynamoBatchJobs_Tasks FOREIGN KEY (task_id)
    REFERENCES dbo.tblTasks(task_id) ON DELETE SET NULL;
```

## Phase 5: Advanced Features

### 5.1 Scheduled Batch Processing

Integrate with task scheduler:

```python
# services/dynamo_scheduler_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from services.dynamo_batch_service import DynamoBatchService

class DynamoScheduler:
    """Schedule recurring Dynamo batch jobs."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.service = DynamoBatchService()
    
    def schedule_weekly_validation(self, project_id: int, script_path: str):
        """Schedule weekly validation run."""
        self.scheduler.add_job(
            func=self._execute_validation,
            args=[project_id, script_path],
            trigger='cron',
            day_of_week='mon',
            hour=2,
            minute=0
        )
    
    def _execute_validation(self, project_id: int, script_path: str):
        """Execute scheduled validation."""
        job_id = self.service.create_batch_job(
            project_id=project_id,
            script_path=script_path,
            file_filter='*.rvt'
        )
        self.service.execute_batch_job(job_id)
```

### 5.2 Results Dashboard

Create analytics for batch processing results:

```sql
-- View for batch processing metrics
CREATE VIEW vw_DynamoBatchMetrics AS
SELECT 
    p.project_id,
    p.project_name,
    COUNT(j.batch_job_id) as total_jobs,
    SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
    SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
    SUM(j.files_processed) as total_files_processed,
    AVG(DATEDIFF(SECOND, j.created_at, j.completed_at)) as avg_duration_seconds
FROM dbo.tblProjects p
LEFT JOIN dbo.tblDynamoBatchJobs j ON j.project_id = p.project_id
GROUP BY p.project_id, p.project_name;
```

## Benefits

### Immediate Value

1. **Automated Quality Control** - Run validation scripts on all models automatically
2. **Batch Export** - Export multiple formats (DWG, IFC, NWC) in one operation
3. **Standards Enforcement** - Apply naming conventions and cleanup scripts
4. **Time Savings** - Process 50+ files in minutes vs hours of manual work

### Integration Points

- **Project Services** - Link batch operations to billable services
- **Review Cycles** - Trigger validation before each review milestone
- **Task Management** - Create tasks that execute Dynamo scripts
- **Analytics Dashboard** - Track batch processing metrics

### Scalability

- Supports multiple Dynamo scripts per project
- Queue system for managing multiple jobs
- Background processing doesn't block UI
- Extensible to other automation tools (pyRevit, BIM-Automation-Tool)

## Next Steps

1. **Install DynamoAutomation** from GitHub
2. **Run database migration** to create batch job tables
3. **Implement backend service** (`dynamo_batch_service.py`)
4. **Add API endpoints** to `backend/app.py`
5. **Create frontend component** (`DynamoBatchPanel.tsx`)
6. **Test with sample script** on a development project
7. **Create Dynamo script library** for common operations

## Example Dynamo Scripts

### 1. Export to DWG (All Sheets)
```
Export all sheets to DWG format with proper layer settings
```

### 2. Model Validation
```
Check for:
- Unplaced rooms
- Overlapping elements
- Missing parameters
- Naming convention violations
```

### 3. Family Audit
```
Identify:
- Unused families
- Duplicate families
- Families needing updates
```

### 4. Coordinate Check
```
Verify project coordinates and survey points
```

## Conclusion

This integration brings powerful automation capabilities to your BIM Project Management System while maintaining the structured workflow approach. The modular design allows for incremental implementation and easy extension to support additional tools like BIM-Automation-Tool in the future.
