import { createTheme, ThemeOptions } from '@mui/material/styles';

// ==================== BIM DASHBOARD THEMES ====================

/**
 * Modern Professional Theme
 * Clean, corporate feel with blue accent colors
 */
export const moderTheme = createTheme({
  palette: {
    primary: {
      main: '#2196F3',
      light: '#64B5F6',
      dark: '#1565C0',
    },
    secondary: {
      main: '#4CAF50',
      light: '#81C784',
      dark: '#2E7D32',
    },
    success: {
      main: '#4CAF50',
    },
    warning: {
      main: '#FF9800',
    },
    error: {
      main: '#f44336',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.5px',
    },
    h4: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.25px',
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
        },
      },
    },
  },
});

/**
 * Dark Mode Theme
 * For reduced eye strain during extended use
 */
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#64B5F6',
      light: '#90CAF9',
      dark: '#1565C0',
    },
    secondary: {
      main: '#81C784',
      light: '#A5D6A7',
      dark: '#2E7D32',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          backgroundColor: '#1e1e1e',
        },
      },
    },
  },
});

/**
 * High Contrast Theme
 * For accessibility and visibility in bright environments
 */
export const highContrastTheme = createTheme({
  palette: {
    primary: {
      main: '#0D47A1',
      light: '#1565C0',
      dark: '#0D47A1',
    },
    secondary: {
      main: '#FF6F00',
    },
    success: {
      main: '#00B050',
    },
    warning: {
      main: '#FF9800',
    },
    error: {
      main: '#D32F2F',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    h4: {
      fontWeight: 800,
    },
  },
});

/**
 * Construction Industry Theme
 * Orange and steel blue accent colors for construction context
 */
export const constructionTheme = createTheme({
  palette: {
    primary: {
      main: '#FF6F00',
      light: '#FFB74D',
      dark: '#E65100',
    },
    secondary: {
      main: '#455A64',
      light: '#78909C',
      dark: '#263238',
    },
    success: {
      main: '#2E7D32',
    },
    warning: {
      main: '#F57C00',
    },
    error: {
      main: '#C62828',
    },
  },
});

/**
 * Minimal Theme
 * Maximizes data-to-ink ratio with minimal colors
 */
export const minimalTheme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid #E0E0E0',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          },
        },
      },
    },
  },
});

// ==================== COLOR PALETTES FOR DISCIPLINES ====================

export const disciplineColors = {
  structural: '#1565C0',
  mep: '#F57C00',
  architectural: '#6A1B9A',
  civil: '#00796B',
  electrical: '#FFB300',
  mechanical: '#0277BD',
  plumbing: '#1565C0',
  fire_safety: '#D32F2F',
  general_contractor: '#455A64',
  sustainability: '#4CAF50',
};

// ==================== SEVERITY COLOR SCALES ====================

export const severityColors = {
  critical: '#D32F2F',
  high: '#F57C00',
  medium: '#FF9800',
  low: '#FBC02D',
  info: '#1976D2',
  success: '#4CAF50',
};

// ==================== CHART COLOR SCHEMES ====================

export const chartColorSchemes = {
  // Categorical colors for disciplines
  disciplines: [
    '#1565C0', // Structural - Blue
    '#F57C00', // MEP - Orange
    '#6A1B9A', // Architectural - Purple
    '#00796B', // Civil - Teal
    '#FFB300', // Electrical - Gold
    '#0277BD', // Mechanical - Light Blue
  ],

  // Sequential colors for progress/completion
  sequential: [
    '#E3F2FD',
    '#BBDEFB',
    '#90CAF9',
    '#64B5F6',
    '#42A5F5',
    '#2196F3',
    '#1976D2',
    '#1565C0',
    '#0D47A1',
  ],

  // Diverging colors for variance (negative to positive)
  diverging: [
    '#D32F2F', // High negative
    '#F57C00', // Negative
    '#FDD835', // Neutral
    '#81C784', // Positive
    '#2E7D32', // High positive
  ],

  // Status indicators
  status: {
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#f44336',
    info: '#2196F3',
    disabled: '#BDBDBD',
  },
};

// ==================== UTILITY FUNCTIONS ====================

/**
 * Get color based on numeric value
 * @param value - The value to color
 * @param max - Maximum value for scaling
 * @param useSequential - Use sequential color scheme
 */
export const getValueColor = (
  value: number,
  max: number = 100,
  useSequential: boolean = true
): string => {
  const percentage = Math.min(value / max, 1);

  if (useSequential) {
    const colors = chartColorSchemes.sequential;
    const index = Math.floor(percentage * (colors.length - 1));
    return colors[index];
  }

  // Use diverging scheme (for variance)
  const colors = chartColorSchemes.diverging;
  if (percentage < 0.4) return colors[0];
  if (percentage < 0.6) return colors[1];
  if (percentage < 0.8) return colors[2];
  if (percentage < 0.9) return colors[3];
  return colors[4];
};

/**
 * Get severity color based on threshold
 * @param value - Current value
 * @param threshold - Alert threshold
 * @param criticalThreshold - Critical threshold
 */
export const getSeverityColor = (
  value: number,
  threshold: number,
  criticalThreshold: number
): string => {
  if (value >= criticalThreshold) return severityColors.critical;
  if (value >= threshold) return severityColors.high;
  if (value >= threshold * 0.7) return severityColors.medium;
  if (value >= threshold * 0.5) return severityColors.low;
  return severityColors.success;
};

/**
 * Get discipline color
 * @param discipline - Discipline name
 */
export const getDisciplineColor = (discipline: string): string => {
  const normalized = discipline.toLowerCase().replace(/\s+/g, '_');
  return disciplineColors[normalized as keyof typeof disciplineColors] || '#757575';
};

export default {
  moderTheme,
  darkTheme,
  highContrastTheme,
  constructionTheme,
  minimalTheme,
  disciplineColors,
  severityColors,
  chartColorSchemes,
  getValueColor,
  getSeverityColor,
  getDisciplineColor,
};
// @ts-nocheck
