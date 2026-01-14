/**
 * Theme Factory - Linear-Inspired Minimal Design System
 * 
 * A refined, minimal theme system for BIM Project Management System
 * Inspired by Linear's design philosophy: radical minimalism, neutral foundation,
 * sharp precision, functional elegance, and refined interactions.
 * 
 * Phase 1-3 Complete: Linear Color System + Minimal Shadows + Sharp Radius
 * 
 * @author Theme Factory Generator
 * @version 3.0.0 (Linear-Inspired)
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';

// ==================== PROFESSIONAL FONT STACK ====================
/**
 * Enterprise-grade font stack (unchanged):
 * - Inter: Modern, clean, highly readable sans-serif (Perfect for Linear aesthetic)
 * - Segoe UI: Windows fallback with excellent metrics
 * - Roboto: Android/Material fallback
 */
const PROFESSIONAL_FONTS = {
  primary: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'Roboto',
    'Oxygen',
    'Ubuntu',
    'Cantarell',
    'Helvetica Neue',
    'Arial',
    'sans-serif',
  ].join(','),

  mono: [
    'Menlo',
    'Monaco',
    'Courier New',
    'monospace',
  ].join(','),

  heading: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    'Segoe UI',
    'sans-serif',
  ].join(','),
};

// ==================== LINEAR-INSPIRED MINIMAL COLOR PALETTES ====================

/**
 * Neutral Gray Palette - Foundation of Linear aesthetic
 * Near-white to near-black, used for everything except accent
 */
const NEUTRAL_PALETTE = {
  50: '#FAFAFA',   // Almost white
  100: '#F5F5F5',  // Very light gray
  150: '#F0F0F0',  // Light gray
  200: '#EEEEEE',  // Light gray
  300: '#E0E0E0',  // Medium-light gray
  400: '#BDBDBD',  // Medium gray
  500: '#9E9E9E',  // Medium gray
  600: '#757575',  // Medium-dark gray
  700: '#616161',  // Dark gray
  800: '#424242',  // Very dark gray
  900: '#212121',  // Near black
};

/**
 * Accent Color Palette - Single refined blue (Linear-inspired)
 * #0066CC = Refined, professional blue used for all interactive elements
 * Minimal variance; primarily used as main accent
 */
const ACCENT_PALETTE = {
  50: '#E6F0FF',   // Very light blue
  100: '#CCE0FF',  // Light blue
  200: '#99C2FF',  // Medium-light blue
  300: '#66A3FF',  // Medium blue
  400: '#3385FF',  // Slightly lighter main
  500: '#0066CC',  // Main accent color
  600: '#0052A3',  // Darker variant
  700: '#003D7A',  // Even darker
  800: '#002952',  // Very dark
  900: '#001929',  // Near black
};

/**
 * Status Colors - Simplified for Linear aesthetic
 * Softer, more refined colors compared to Material Design
 */
const STATUS_COLORS = {
  success: '#16A34A',    // Refined green (from #00C853)
  warning: '#D97706',    // Refined amber (from #FF6D00)
  error: '#DC2626',      // Refined red (from #D32F2F)
  info: '#0284C7',       // Refined blue (from #0288D1)
  disabled: '#D1D5DB',   // Refined gray (from #BDBDBD)
};

/**
 * Construction Industry Palette - Softened for Linear aesthetic
 * Discipline-specific colors, refined and muted compared to Material Design
 */
const DISCIPLINE_COLORS = {
  structural: '#1E40AF',       // Deep refined blue
  mep: '#B45309',              // Refined deep orange
  architectural: '#6B21A8',    // Refined deep purple
  civil: '#065F46',            // Refined deep teal
  electrical: '#92400E',       // Refined deep amber
  mechanical: '#0369A1',       // Refined cyan
  plumbing: '#1E3A8A',         // Refined primary blue
  fire_safety: '#991B1B',      // Refined deep red
  general_contractor: '#1F2937',// Refined blue gray
  sustainability: '#166534',   // Refined green
};

/**
 * Deprecated palettes (kept for reference, not used)
 * PRIMARY_PALETTE and SECONDARY_PALETTE replaced by ACCENT_PALETTE and NEUTRAL_PALETTE
 */
const PRIMARY_PALETTE = ACCENT_PALETTE;  // For backward compatibility
const SECONDARY_PALETTE = NEUTRAL_PALETTE;  // For backward compatibility

// ==================== TYPOGRAPHY CONFIGURATION ====================

/**
 * Linear-inspired typography system
 * Simplified from 12 to 8 essential styles for clarity and refinement
 * Maintains hierarchy while reducing cognitive load
 */
const createTypography = () => ({
  fontFamily: PROFESSIONAL_FONTS.primary,

  h1: {
    fontSize: '2rem',        // 32px (reduced from 40px)
    fontWeight: 600,         // Semibold instead of bold
    lineHeight: 1.2,
    letterSpacing: '-0.5px',
    fontFamily: PROFESSIONAL_FONTS.heading,
  },
  h2: {
    fontSize: '1.5rem',      // 24px (reduced from 32px)
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.25px',
    fontFamily: PROFESSIONAL_FONTS.heading,
  },
  h3: {
    fontSize: '1.25rem',     // 20px (reduced from 28px)
    fontWeight: 600,
    lineHeight: 1.4,
    fontFamily: PROFESSIONAL_FONTS.heading,
  },
  h4: {
    fontSize: '1rem',        // 16px (reduced from 24px)
    fontWeight: 600,
    lineHeight: 1.5,
    fontFamily: PROFESSIONAL_FONTS.heading,
  },
  // Removed h5, h6, subtitle1, subtitle2 to simplify to 8 styles
  
  body1: {
    fontSize: '0.95rem',     // 15.2px (refined from 16px)
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0px',
  },
  body2: {
    fontSize: '0.85rem',     // 13.6px (refined from 14px)
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0px',
  },
  caption: {
    fontSize: '0.75rem',     // 12px
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0px',
  },
  button: {
    fontSize: '0.9rem',      // 14.4px
    fontWeight: 600,
    lineHeight: 1.5,
    letterSpacing: '0px',
    textTransform: 'none',
  },
  // Removed overline to simplify
});

// ==================== COMPONENT OVERRIDES ====================

/**
 * Linear-inspired component style overrides
 * Minimal shadows (1-2px), sharp corners (2-3px), color shifts instead of elevations
 */
const createComponentOverrides = (palette: any) => ({
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: '3px',  // Sharp corners (reduced from 6px)
        padding: '8px 12px',  // Slightly tighter padding
        fontWeight: 600,
        textTransform: 'none',
        transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',  // Subtle transition
        '&:hover': {
          // No transform - just color/shadow shift
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
          backgroundColor: 'inherit',  // Maintain background
        },
      },
      contained: {
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.06)',  // Minimal shadow (reduced from 0 2px 4px)
      },
      outlined: {
        borderWidth: '1px',  // Refined border
        border: `1px solid ${palette.borderColor || '#E5E7EB'}`,
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: '3px',  // Sharp corners (reduced from 12px)
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',  // Minimal shadow
        border: `1px solid ${palette.borderColor || '#E5E7EB'}`,  // 1px border for definition
        transition: 'all 0.2s ease',
        '&:hover': {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',  // Subtle shadow lift
          borderColor: palette.accentColor || '#0066CC',
        },
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
        border: `1px solid ${palette.borderColor || '#E5E7EB'}`,  // Add border for definition
      },
      elevation0: {
        boxShadow: 'none',
        borderColor: 'transparent',
      },
      elevation1: {
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
      },
      elevation2: {
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
      },
      elevation3: {
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: '3px',  // Sharp corners
        fontWeight: 500,
        border: `1px solid ${palette.borderColor || '#E5E7EB'}`,
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: '3px',  // Sharp corners
          transition: 'border-color 0.15s ease',
          '&:hover': {
            borderColor: palette.accentColor || '#0066CC',
          },
        },
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: {
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',  // Minimal shadow
        borderBottom: `1px solid ${palette.borderColor || '#E5E7EB'}`,
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 500,
        fontSize: '0.9rem',
        borderBottom: '2px solid transparent',
        '&.Mui-selected': {
          borderBottomColor: palette.accentColor || '#0066CC',
        },
      },
    },
  },
  MuiOutlinedInput: {
    styleOverrides: {
      root: {
        '& fieldset': {
          borderColor: palette.borderColor || '#E5E7EB',
          borderRadius: '3px',
        },
        '&:hover fieldset': {
          borderColor: palette.accentColor || '#0066CC',
        },
      },
    },
  },
});

// ==================== THEME FACTORY ====================

/**
 * Core theme factory function with Linear-inspired palette
 * Creates a Material-UI theme with minimal, refined styling
 */
const createProfessionalTheme = (
  palette: any,
  themeMode: 'light' | 'dark' = 'light'
): ThemeOptions => ({
  palette: {
    mode: themeMode,
    primary: {
      main: palette.primary,
      light: palette.primaryLight,
      dark: palette.primaryDark,
      contrastText: themeMode === 'light' ? '#fff' : '#000',
    },
    secondary: {
      main: palette.secondary,
      light: palette.secondaryLight,
      dark: palette.secondaryDark,
      contrastText: themeMode === 'light' ? '#fff' : '#000',
    },
    success: {
      main: STATUS_COLORS.success,
    },
    warning: {
      main: STATUS_COLORS.warning,
    },
    error: {
      main: STATUS_COLORS.error,
    },
    info: {
      main: STATUS_COLORS.info,
    },
    background: {
      default: palette.bgDefault,
      paper: palette.bgPaper,
    },
    text: {
      primary: palette.textPrimary,
      secondary: palette.textSecondary,
      disabled: palette.textDisabled,
    },
  },
  typography: createTypography(),
  shape: {
    borderRadius: 3,  // Sharp 3px radius globally (reduced from 8px)
  },
  components: createComponentOverrides(palette),
});

// ==================== LIGHT MODE PALETTES ====================

const LIGHT_PALETTES = {
  professional: {
    primary: ACCENT_PALETTE[500],        // #0066CC
    primaryLight: ACCENT_PALETTE[300],   // #66A3FF
    primaryDark: ACCENT_PALETTE[700],    // #003D7A
    secondary: NEUTRAL_PALETTE[500],     // Neutral for secondary
    secondaryLight: NEUTRAL_PALETTE[400],
    secondaryDark: NEUTRAL_PALETTE[600],
    bgDefault: '#FFFFFF',                // White background
    bgPaper: '#FFFFFF',
    textPrimary: '#1F2937',              // Near-black text
    textSecondary: '#6B7280',            // Medium gray text
    textDisabled: '#D1D5DB',             // Light gray for disabled
    borderColor: '#E5E7EB',              // Border color
    accentColor: ACCENT_PALETTE[500],    // #0066CC
  },
  corporate: {
    primary: ACCENT_PALETTE[500],        // #0066CC
    primaryLight: ACCENT_PALETTE[300],
    primaryDark: ACCENT_PALETTE[700],
    secondary: NEUTRAL_PALETTE[600],     // Darker neutral
    secondaryLight: NEUTRAL_PALETTE[500],
    secondaryDark: NEUTRAL_PALETTE[700],
    bgDefault: '#FFFFFF',
    bgPaper: '#FFFFFF',
    textPrimary: '#1F2937',
    textSecondary: '#6B7280',
    textDisabled: '#D1D5DB',
    borderColor: '#E5E7EB',
    accentColor: ACCENT_PALETTE[500],    // #0066CC
  },
  construction: {
    primary: '#D97706',                  // Refined orange
    primaryLight: '#FBBF24',
    primaryDark: '#B45309',
    secondary: ACCENT_PALETTE[500],      // #0066CC as secondary
    secondaryLight: ACCENT_PALETTE[300],
    secondaryDark: ACCENT_PALETTE[700],
    bgDefault: '#FFFFFF',
    bgPaper: '#FFFFFF',
    textPrimary: '#1F2937',
    textSecondary: '#6B7280',
    textDisabled: '#D1D5DB',
    borderColor: '#E5E7EB',
    accentColor: '#D97706',
  },
  minimal: {
    primary: ACCENT_PALETTE[500],        // #0066CC
    primaryLight: ACCENT_PALETTE[300],
    primaryDark: ACCENT_PALETTE[700],
    secondary: NEUTRAL_PALETTE[500],
    secondaryLight: NEUTRAL_PALETTE[400],
    secondaryDark: NEUTRAL_PALETTE[600],
    bgDefault: '#FFFFFF',                // Pure white for minimal
    bgPaper: '#FFFFFF',
    textPrimary: '#1F2937',
    textSecondary: '#6B7280',
    textDisabled: '#D1D5DB',
    borderColor: '#E5E7EB',
    accentColor: ACCENT_PALETTE[500],    // #0066CC
  },
};

// ==================== DARK MODE PALETTES ====================

const DARK_PALETTES = {
  professional: {
    primary: ACCENT_PALETTE[200],        // Light blue
    primaryLight: ACCENT_PALETTE[100],   // Very light blue
    primaryDark: ACCENT_PALETTE[400],    // Medium-light blue
    secondary: NEUTRAL_PALETTE[300],     // Light gray
    secondaryLight: NEUTRAL_PALETTE[200],
    secondaryDark: NEUTRAL_PALETTE[400],
    bgDefault: '#0F172A',                // Very dark blue-black
    bgPaper: '#1A202C',                  // Dark gray-blue
    textPrimary: '#F9FAFB',              // Near-white text
    textSecondary: '#D1D5DB',            // Light gray text
    textDisabled: '#6B7280',             // Medium gray for disabled
    borderColor: '#374151',              // Dark gray border
    accentColor: ACCENT_PALETTE[200],    // Light blue for dark mode
  },
  corporate: {
    primary: ACCENT_PALETTE[200],
    primaryLight: ACCENT_PALETTE[100],
    primaryDark: ACCENT_PALETTE[400],
    secondary: NEUTRAL_PALETTE[300],
    secondaryLight: NEUTRAL_PALETTE[200],
    secondaryDark: NEUTRAL_PALETTE[400],
    bgDefault: '#0F172A',
    bgPaper: '#1A202C',
    textPrimary: '#F9FAFB',
    textSecondary: '#D1D5DB',
    textDisabled: '#6B7280',
    borderColor: '#374151',
    accentColor: ACCENT_PALETTE[200],
  },
  construction: {
    primary: '#FCD34D',                  // Light yellow-amber
    primaryLight: '#FEF3C7',
    primaryDark: '#F59E0B',
    secondary: ACCENT_PALETTE[200],
    secondaryLight: ACCENT_PALETTE[100],
    secondaryDark: ACCENT_PALETTE[400],
    bgDefault: '#0F172A',
    bgPaper: '#1A202C',
    textPrimary: '#F9FAFB',
    textSecondary: '#D1D5DB',
    textDisabled: '#6B7280',
    borderColor: '#374151',
    accentColor: '#FCD34D',
  },
};

// ==================== THEME EXPORTS ====================

/**
 * Professional Enterprise Theme (Light)
 * Recommended for general use
 */
export const professionalLightTheme = createTheme(
  createProfessionalTheme(LIGHT_PALETTES.professional, 'light')
);

/**
 * Professional Enterprise Theme (Dark)
 * Reduced eye strain during extended use
 */
export const professionalDarkTheme = createTheme(
  createProfessionalTheme(DARK_PALETTES.professional, 'dark')
);

/**
 * Corporate Blue Theme (Light)
 * Formal, traditional appearance for stakeholder presentations
 */
export const corporateLightTheme = createTheme(
  createProfessionalTheme(LIGHT_PALETTES.corporate, 'light')
);

/**
 * Corporate Blue Theme (Dark)
 * Dark variant for corporate presentations
 */
export const corporateDarkTheme = createTheme(
  createProfessionalTheme(DARK_PALETTES.corporate, 'dark')
);

/**
 * Construction Industry Theme (Light)
 * Orange and blue for construction context
 */
export const constructionLightTheme = createTheme(
  createProfessionalTheme(LIGHT_PALETTES.construction, 'light')
);

/**
 * Construction Industry Theme (Dark)
 * Dark variant for construction professionals
 */
export const constructionDarkTheme = createTheme(
  createProfessionalTheme(DARK_PALETTES.construction, 'dark')
);

/**
 * Minimal Theme (Light)
 * Data-focused with minimal visual complexity
 */
export const minimalLightTheme = createTheme(
  createProfessionalTheme(LIGHT_PALETTES.minimal, 'light')
);

// ==================== COLOR UTILITIES ====================

/**
 * Get color based on discipline
 * Returns refined, muted colors for Linear aesthetic
 * @param discipline - Discipline name (structural, mep, etc.)
 * @returns Hex color code
 */
export const getDisciplineColor = (discipline: string): string => {
  const normalized = discipline.toLowerCase().replace(/\s+/g, '_') as keyof typeof DISCIPLINE_COLORS;
  return DISCIPLINE_COLORS[normalized] || DISCIPLINE_COLORS.general_contractor;
};

/**
 * Get severity color based on threshold
 * Linear-inspired: softer, more refined colors
 * @param value - Current value
 * @param threshold - Alert threshold
 * @returns Hex color code
 */
export const getSeverityColor = (value: number, threshold: number): string => {
  if (value >= threshold * 1.5) return STATUS_COLORS.error;
  if (value >= threshold) return STATUS_COLORS.warning;
  if (value >= threshold * 0.7) return '#F59E0B';  // Refined amber
  return STATUS_COLORS.success;
};

/**
 * Get sequential color based on percentage
 * Linear-inspired: neutral to accent progression
 * @param percentage - Value between 0-1
 * @returns Hex color code
 */
export const getSequentialColor = (percentage: number): string => {
  const normalized = Math.min(1, Math.max(0, percentage));
  if (normalized < 0.33) return NEUTRAL_PALETTE[300];    // Light gray
  if (normalized < 0.66) return '#F59E0B';               // Amber
  return STATUS_COLORS.success;                          // Green
};

// ==================== THEME REGISTRY ====================

/**
 * Centralized theme registry for easy access
 */
export const themeRegistry = {
  light: {
    professional: professionalLightTheme,
    corporate: corporateLightTheme,
    construction: constructionLightTheme,
    minimal: minimalLightTheme,
  },
  dark: {
    professional: professionalDarkTheme,
    corporate: corporateDarkTheme,
    construction: constructionDarkTheme,
  },
};

/**
 * Get theme by name
 * @param name - Theme name
 * @param mode - light or dark
 * @returns Material-UI theme object
 */
export const getTheme = (
  name: 'professional' | 'corporate' | 'construction' | 'minimal' = 'professional',
  mode: 'light' | 'dark' = 'light'
) => {
  if (mode === 'dark') {
    return themeRegistry.dark[name as keyof typeof themeRegistry.dark] || professionalDarkTheme;
  }
  return themeRegistry.light[name as keyof typeof themeRegistry.light] || professionalLightTheme;
};

// ==================== COLOR PALETTES EXPORT ====================

export const palettes = {
  primary: PRIMARY_PALETTE,
  secondary: SECONDARY_PALETTE,
  status: STATUS_COLORS,
  neutral: NEUTRAL_PALETTE,
  disciplines: DISCIPLINE_COLORS,
};

export const fonts = PROFESSIONAL_FONTS;

export default {
  professionalLightTheme,
  professionalDarkTheme,
  corporateLightTheme,
  corporateDarkTheme,
  constructionLightTheme,
  constructionDarkTheme,
  minimalLightTheme,
  getDisciplineColor,
  getSeverityColor,
  getSequentialColor,
  getTheme,
  themeRegistry,
  palettes,
  fonts,
};
