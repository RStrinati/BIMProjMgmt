import React from 'react';
import { Box, LinearProgress, Typography, Stack } from '@mui/material';

interface ServicesSummaryStripProps {
  totalAgreed: number;
  totalBilled: number;
  totalRemaining: number;
  progress: number;
  isPartialSummary?: boolean;
  formatCurrency: (value?: number | null) => string;
  formatPercent: (value?: number | null) => string;
}

/**
 * Linear-style summary strip: discreet, minimal chrome.
 * Replaces 3 heavy Paper cards with a single horizontal strip.
 */
export function ServicesSummaryStrip({
  totalAgreed,
  totalBilled,
  totalRemaining,
  progress,
  isPartialSummary,
  formatCurrency,
  formatPercent,
}: ServicesSummaryStripProps) {
  return (
    <Box sx={{ mb: 3 }}>
      {/* Summary numbers: flat row, calm typography */}
      <Stack
        direction="row"
        spacing={4}
        sx={{
          pb: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Total Contract Sum
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {formatCurrency(totalAgreed)}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Fee Billed
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {formatCurrency(totalBilled)}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Agreed Fee Remaining
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {formatCurrency(totalRemaining)}
          </Typography>
        </Box>
      </Stack>

      {/* Progress bar: thin, muted */}
      <Box sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Billing Progress
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
            {formatPercent(progress)}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={progress}
          sx={{
            height: 4,
            borderRadius: 2,
            backgroundColor: 'action.disabledBackground',
            '& .MuiLinearProgress-bar': {
              backgroundColor: 'primary.main',
              borderRadius: 2,
            },
          }}
        />
      </Box>

      {/* Partial summary warning */}
      {isPartialSummary && (
        <Typography variant="caption" color="warning.main" sx={{ display: 'block', mt: 1 }}>
          Totals reflect the current page until the API provides aggregated rollups.
        </Typography>
      )}
    </Box>
  );
}
