/**
 * BIM Project Management Theme
 * 
 * This file exports the Linear-inspired minimal design system theme.
 * All configuration is now centralized in theme-factory.ts for better maintainability.
 * 
 * Version: 3.0.0 (Linear-Inspired Minimal)
 * Last Updated: January 14, 2026
 * 
 * @see theme-factory.ts for complete theme documentation
 */

import { professionalLightTheme } from './theme-factory';

// Export the professional light theme as the default theme
// This maintains backward compatibility with existing code
export const theme = professionalLightTheme;
