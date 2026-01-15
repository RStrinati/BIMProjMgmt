/**
 * BlockerBadge Component
 *
 * Displays blocker counts for an anchor (review, service item, etc.)
 * Color-coded based on severity:
 * - Red (error): Has open blockers
 * - Green (success): No open blockers
 * - Gray (default): Loading or no data
 */

import React from 'react';
import { Chip, CircularProgress, Tooltip } from '@mui/material';
import { useAnchorCounts } from '@/hooks/useAnchorLinks';

interface BlockerBadgeProps {
  projectId: number;
  anchorType: 'review' | 'service' | 'item';
  anchorId: number;
  enabled?: boolean;
  onClick?: () => void;
  size?: 'small' | 'medium';
  variant?: 'filled' | 'outlined';
  'data-testid'?: string;
}

export const BlockerBadge: React.FC<BlockerBadgeProps> = ({
  projectId,
  anchorType,
  anchorId,
  enabled = true,
  onClick,
  size = 'small',
  variant = 'filled',
  'data-testid': testId,
}) => {
  const { data: counts, isLoading, error } = useAnchorCounts(projectId, anchorType, anchorId, enabled);

  if (!enabled) {
    return null;
  }

  if (error) {
    return (
      <Tooltip title="Error loading blockers">
        <Chip label="Error" size={size} variant={variant} color="default" />
      </Tooltip>
    );
  }

  if (isLoading) {
    return (
      <Tooltip title="Loading blockers...">
        <Chip
          icon={<CircularProgress size={16} />}
          label="Loading"
          size={size}
          variant={variant}
          color="default"
        />
      </Tooltip>
    );
  }

  if (!counts) {
    return null;
  }

  const { open_count, critical_count, high_count, total_linked } = counts;
  const isBlocked = open_count > 0;

  // Determine color and label
  const color = isBlocked ? 'error' : 'success';
  const icon = isBlocked ? '🔴' : '✅';
  const label = `${open_count}/${total_linked}`;
  const tooltip = isBlocked
    ? `${open_count} open blocker${open_count !== 1 ? 's' : ''} (${critical_count} critical, ${high_count} high)`
    : `No open blockers (${total_linked} total linked)`;

  const chip = (
    <Chip
      label={`${icon} ${label}`}
      size={size}
      variant={variant}
      color={color}
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        fontWeight: 500,
        '& .MuiChip-label': {
          paddingX: 1,
        },
      }}
    />
  );

  if (!onClick) {
    return chip;
  }

  // Handle click - directly on button element
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    onClick();
  };

  return (
    <Tooltip title={tooltip}>
      <button
        data-testid={testId || `blocker-badge-${anchorType}-${anchorId}`}
        type="button"
        onClick={handleClick}
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {chip}
      </button>
    </Tooltip>
  );
};

export default BlockerBadge;
