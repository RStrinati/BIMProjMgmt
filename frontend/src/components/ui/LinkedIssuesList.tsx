/**
 * LinkedIssuesList Component
 *
 * Displays a paginated, sortable list of issues linked to an anchor
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useAnchorLinkedIssues, useDeleteIssueLink } from '@/hooks/useAnchorLinks';

type SortField = 'updated_at' | 'priority_normalized' | 'status_normalized';

interface LinkedIssuesListProps {
  projectId: number;
  anchorType: 'review' | 'service' | 'item';
  anchorId: number;
  enabled?: boolean;
  readonly?: boolean;
  linkRole?: string;
  'data-testid'?: string;
}

const priorityColors: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  Critical: 'error',
  High: 'warning',
  Medium: 'info',
  Low: 'default',
};

const statusColors: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  Open: 'error',
  'In Progress': 'warning',
  'In Review': 'info',
  Closed: 'success',
  Resolved: 'success',
};

export const LinkedIssuesList: React.FC<LinkedIssuesListProps> = ({
  projectId,
  anchorType,
  anchorId,
  enabled = true,
  readonly = false,
  linkRole,
  'data-testid': testId,
}) => {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [sortBy, setSortBy] = useState<SortField>('updated_at');
  const [sortDir, setSortDir] = useState<'ASC' | 'DESC'>('DESC');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [linkToDelete, setLinkToDelete] = useState<number | null>(null);

  const { data: issuesData, isLoading, error } = useAnchorLinkedIssues(
    projectId,
    anchorType,
    anchorId,
    page + 1, // Convert 0-based to 1-based
    pageSize,
    sortBy,
    sortDir,
    linkRole,
    enabled
  );

  const { mutate: deleteLink, isLoading: isDeleting } = useDeleteIssueLink(projectId, anchorType, anchorId);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'ASC' ? 'DESC' : 'ASC');
    } else {
      setSortBy(field);
      setSortDir('DESC');
    }
    setPage(0);
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPageSize(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleDeleteClick = (linkId: number) => {
    setLinkToDelete(linkId);
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    if (linkToDelete) {
      deleteLink(linkToDelete);
    }
    setDeleteConfirmOpen(false);
    setLinkToDelete(null);
  };

  if (!enabled) {
    return null;
  }

  if (error) {
    return <Alert severity="error">Error loading linked issues</Alert>;
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <CircularProgress />
      </Box>
    );
  }

  if (!issuesData?.issues || issuesData.issues.length === 0) {
    return <Alert severity="info">No linked issues</Alert>;
  }

  return (
    <>
      <Paper data-testid={testId || `linked-issues-list-${anchorType}-${anchorId}`}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell>
                <TableSortLabel
                  active={sortBy === 'updated_at'}
                  direction={sortDir === 'ASC' ? 'asc' : 'desc'}
                  onClick={() => handleSort('updated_at')}
                >
                  Issue
                </TableSortLabel>
              </TableCell>
              <TableCell>Title</TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortBy === 'status_normalized'}
                  direction={sortDir === 'ASC' ? 'asc' : 'desc'}
                  onClick={() => handleSort('status_normalized')}
                >
                  Status
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">
                <TableSortLabel
                  active={sortBy === 'priority_normalized'}
                  direction={sortDir === 'ASC' ? 'asc' : 'desc'}
                  onClick={() => handleSort('priority_normalized')}
                >
                  Priority
                </TableSortLabel>
              </TableCell>
              <TableCell align="center">Role</TableCell>
              <TableCell>Note</TableCell>
              {!readonly && <TableCell align="center">Action</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {issuesData.issues.map((issue) => (
              <TableRow key={issue.link_id} hover>
                <TableCell>
                  <strong>{issue.display_id}</strong>
                </TableCell>
                <TableCell>{issue.title}</TableCell>
                <TableCell align="center">
                  <Chip
                    label={issue.status_normalized}
                    size="small"
                    color={statusColors[issue.status_normalized] || 'default'}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={issue.priority_normalized}
                    size="small"
                    color={priorityColors[issue.priority_normalized] || 'default'}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell align="center">
                  <Chip label={issue.link_role} size="small" variant="outlined" />
                </TableCell>
                <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {issue.note && (
                    <Tooltip title={issue.note}>
                      <span>{issue.note}</span>
                    </Tooltip>
                  )}
                </TableCell>
                {!readonly && (
                  <TableCell align="center">
                    <Tooltip title="Delete link">
                      <span>
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            console.debug('[LinkedIssuesList] Delete button clicked', { linkId: issue.link_id });
                            handleDeleteClick(issue.link_id);
                          }}
                          disabled={isDeleting}
                          data-testid={`delete-link-btn-${issue.link_id}`}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={issuesData.total_count}
          rowsPerPage={pageSize}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Delete confirmation dialog */}
      <Dialog 
        open={deleteConfirmOpen} 
        onClose={() => setDeleteConfirmOpen(false)}
        keepMounted
        PaperProps={{
          'data-testid': 'anchor-links-delete-modal',
        }}
      >
        <DialogTitle>Delete Link?</DialogTitle>
        <DialogContent>Are you sure you want to remove this issue link?</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleConfirmDelete} 
            color="error" 
            variant="contained" 
            disabled={isDeleting}
            data-testid="delete-link-confirm-button"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default LinkedIssuesList;
