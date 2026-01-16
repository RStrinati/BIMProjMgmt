import React from 'react';
import {
  TableRow,
  TableCell,
  Chip,
  Box,
  Typography,
  IconButton,
  LinearProgress,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import type { ProjectService } from '@/api/services';

interface ServicesListRowProps {
  service: ProjectService;
  onRowClick: (service: ProjectService) => void;
  onEditService: (service: ProjectService) => void;
  onDeleteService: (serviceId: number) => void;
  formatCurrency: (value?: number | null) => string;
  formatPercent: (value?: number | null) => string;
  getStatusColor: (
    status: string
  ) => 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
}

/**
 * Linear-style flat service row.
 * No expand/collapse icon in main row—click row to open drawer.
 * Minimal styling: hover subtly, no heavy backgrounds.
 */
export function ServicesListRow({
  service,
  onRowClick,
  onEditService,
  onDeleteService,
  formatCurrency,
  formatPercent,
  getStatusColor,
}: ServicesListRowProps) {
  const billedAmount = service.billed_amount ?? service.claimed_to_date ?? 0;
  const progressValue = service.billing_progress_pct ?? service.progress_pct ?? 0;

  return (
    <TableRow
      hover
      onClick={() => onRowClick(service)}
      sx={{
        cursor: 'pointer',
        backgroundColor: 'transparent',
        '&:hover': {
          backgroundColor: 'action.hover',
        },
      }}
    >
      {/* Service code + name (primary column, clickable) */}
      <TableCell sx={{ py: 1.5 }}>
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {service.service_code}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {service.service_name}
          </Typography>
        </Box>
      </TableCell>

      {/* Phase (muted) */}
      <TableCell sx={{ py: 1.5 }}>
        <Typography variant="caption" color="text.secondary">
          {service.phase || '—'}
        </Typography>
      </TableCell>

      {/* Status (color-coded chip) */}
      <TableCell sx={{ py: 1.5 }}>
        <Chip label={service.status} color={getStatusColor(service.status)} size="small" />
      </TableCell>

      {/* Agreed Fee (muted) */}
      <TableCell sx={{ py: 1.5 }}>
        <Typography variant="caption" color="text.secondary">
          {formatCurrency(service.agreed_fee)}
        </Typography>
      </TableCell>

      {/* Billed (muted) */}
      <TableCell sx={{ py: 1.5 }}>
        <Typography variant="caption" color="text.secondary">
          {formatCurrency(billedAmount)}
        </Typography>
      </TableCell>

      {/* Remaining (muted) */}
      <TableCell sx={{ py: 1.5 }}>
        <Typography variant="caption" color="text.secondary">
          {formatCurrency(service.agreed_fee_remaining)}
        </Typography>
      </TableCell>

      {/* Progress bar inline (thin, subtle) */}
      <TableCell sx={{ py: 1.5, minWidth: 120 }}>
        <Box>
          <LinearProgress
            variant="determinate"
            value={progressValue}
            sx={{
              height: 3,
              borderRadius: 1.5,
              backgroundColor: 'action.disabledBackground',
              mb: 0.5,
              '& .MuiLinearProgress-bar': {
                backgroundColor: 'primary.main',
                borderRadius: 1.5,
              },
            }}
          />
          <Typography variant="caption" color="text.secondary">
            {formatPercent(progressValue)}
          </Typography>
        </Box>
      </TableCell>

      {/* Actions (edit/delete) */}
      <TableCell align="right" sx={{ py: 1.5 }} onClick={(e) => e.stopPropagation()}>
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onEditService(service);
          }}
          sx={{ mr: 0.5 }}
        >
          <EditIcon fontSize="small" />
        </IconButton>
        <IconButton
          size="small"
          color="error"
          onClick={(e) => {
            e.stopPropagation();
            onDeleteService(service.service_id);
          }}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </TableCell>
    </TableRow>
  );
}
