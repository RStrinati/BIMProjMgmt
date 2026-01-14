/**
 * Theme Factory - Usage Examples & Integration Guide
 * 
 * This file demonstrates how to use the professional theme-factory system
 * in your React components and application.
 */

import React, { useState } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

// Import themes from the theme factory
import {
  professionalLightTheme,
  professionalDarkTheme,
  corporateLightTheme,
  constructionLightTheme,
  getTheme,
  getDisciplineColor,
  getSeverityColor,
  themeRegistry,
} from '@/theme/theme-factory';

// ==================== EXAMPLE 1: SIMPLE LIGHT THEME APPLICATION ====================

/**
 * Basic usage with professional light theme
 */
export const AppWithProfessionalTheme: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ThemeProvider theme={professionalLightTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};

// ==================== EXAMPLE 2: THEME SWITCHER ====================

/**
 * Theme switcher component for user preference
 */
interface ThemeSwitcherProps {
  children: React.ReactNode;
}

export const AppWithThemeSwitcher: React.FC<ThemeSwitcherProps> = ({ children }) => {
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>('light');
  const [themeName, setThemeName] = useState<'professional' | 'corporate' | 'construction' | 'minimal'>('professional');

  const currentTheme = getTheme(themeName, themeMode);

  return (
    <ThemeProvider theme={currentTheme}>
      <CssBaseline />
      {/* Pass setThemeMode and setThemeName to your UI */}
      {React.cloneElement(children as React.ReactElement, {
        onThemeModeChange: setThemeMode,
        onThemeNameChange: setThemeName,
        currentThemeMode: themeMode,
        currentThemeName: themeName,
      })}
    </ThemeProvider>
  );
};

// ==================== EXAMPLE 3: DISCIPLINE-COLORED COMPONENT ====================

/**
 * Component using discipline colors
 */
interface DisciplineIndicatorProps {
  discipline: string;
  label: string;
}

export const DisciplineIndicator: React.FC<DisciplineIndicatorProps> = ({
  discipline,
  label,
}) => {
  const color = getDisciplineColor(discipline);

  return (
    <div
      style={{
        padding: '8px 12px',
        borderRadius: '6px',
        backgroundColor: `${color}20`, // 20% opacity
        borderLeft: `4px solid ${color}`,
        color: color,
        fontWeight: 500,
      }}
    >
      {label}
    </div>
  );
};

// ==================== EXAMPLE 4: SEVERITY-BASED COLORING ====================

/**
 * Component using severity colors
 */
interface SeverityBadgeProps {
  value: number;
  threshold: number;
  label: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  value,
  threshold,
  label,
}) => {
  const color = getSeverityColor(value, threshold);

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 8px',
        borderRadius: '4px',
        backgroundColor: color,
        color: '#fff',
        fontSize: '12px',
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
};

// ==================== EXAMPLE 5: CONTEXT-BASED THEME PROVIDER ====================

/**
 * Theme context for application-wide access
 */
const ThemeContext = React.createContext<{
  theme: 'professional' | 'corporate' | 'construction' | 'minimal';
  mode: 'light' | 'dark';
  setTheme: (name: 'professional' | 'corporate' | 'construction' | 'minimal') => void;
  setMode: (mode: 'light' | 'dark') => void;
}>({
  theme: 'professional',
  mode: 'light',
  setTheme: () => {},
  setMode: () => {},
});

export const useTheme = () => React.useContext(ThemeContext);

interface AppProviderProps {
  children: React.ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<'professional' | 'corporate' | 'construction' | 'minimal'>('professional');
  const [mode, setMode] = useState<'light' | 'dark'>('light');

  const muiTheme = getTheme(theme, mode);

  return (
    <ThemeContext.Provider value={{ theme, mode, setTheme, setMode }}>
      <ThemeProvider theme={muiTheme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

// ==================== EXAMPLE 6: USAGE IN MAIN APP ====================

/**
 * How to integrate theme factory into your main App component
 * 
 * MAIN APP INTEGRATION:
 * 
 * import { AppProvider } from '@/theme/theme-factory-examples';
 * 
 * function App() {
 *   return (
 *     <AppProvider>
 *       <MainContent />
 *     </AppProvider>
 *   );
 * }
 */

// ==================== EXAMPLE 7: INLINE THEME USAGE ====================

/**
 * Using theme values directly in components
 */
import { useTheme as useMuiTheme } from '@mui/material/styles';

export const ThemedComponentExample: React.FC = () => {
  const muiTheme = useMuiTheme();

  return (
    <div
      style={{
        backgroundColor: muiTheme.palette.background.paper,
        color: muiTheme.palette.text.primary,
        padding: muiTheme.spacing(2),
        borderRadius: muiTheme.shape.borderRadius,
      }}
    >
      {/* Your component content */}
    </div>
  );
};

// ==================== EXPORT THEME NAMES FOR SELECTION UI ====================

export const AVAILABLE_THEMES = [
  {
    id: 'professional',
    name: 'Professional',
    description: 'Clean, modern enterprise theme',
    category: 'General',
  },
  {
    id: 'corporate',
    name: 'Corporate',
    description: 'Formal, traditional business theme',
    category: 'Enterprise',
  },
  {
    id: 'construction',
    name: 'Construction',
    description: 'Industry-specific orange and blue',
    category: 'Industry',
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Data-focused minimal design',
    category: 'Specialized',
  },
];

export const AVAILABLE_MODES = [
  {
    id: 'light',
    name: 'Light',
    description: 'Bright background for daytime use',
  },
  {
    id: 'dark',
    name: 'Dark',
    description: 'Dark background for reduced eye strain',
  },
];
