# Theme Factory - Professional Design System
## BIM Project Management System v2.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Theme Options](#theme-options)
4. [Typography System](#typography-system)
5. [Color Palettes](#color-palettes)
6. [Component Styling](#component-styling)
7. [Utility Functions](#utility-functions)
8. [Integration Guide](#integration-guide)
9. [Best Practices](#best-practices)

---

## Overview

The **Theme Factory** is a professional enterprise design system built on Material-UI v5 that provides:

- **8 Professional Themes** (4 light + 4 dark variants)
- **Enterprise-Grade Typography** with Inter font stack
- **Semantic Color Palettes** for different use cases
- **Discipline-Specific Colors** for construction roles
- **Status-Based Color Codes** for semantic meaning
- **Utility Functions** for dynamic coloring
- **Consistent Component Styling** across the application

### Design Philosophy

✅ **Professional** - Enterprise-ready appearance  
✅ **Accessible** - WCAG AA contrast ratios  
✅ **Responsive** - Mobile-first design  
✅ **Consistent** - Unified design language  
✅ **Flexible** - Multiple theme options  

---

## Quick Start

### 1. Basic Light Theme

```typescript
import { ThemeProvider } from '@mui/material/styles';
import { professionalLightTheme } from '@/theme/theme-factory';

export function App() {
  return (
    <ThemeProvider theme={professionalLightTheme}>
      <YourApp />
    </ThemeProvider>
  );
}
```

### 2. Switchable Theme with Dark Mode

```typescript
import { getTheme } from '@/theme/theme-factory';

export function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('light');
  const [themeName, setThemeName] = useState<'professional' | 'corporate' | 'construction' | 'minimal'>('professional');

  const theme = getTheme(themeName, mode);

  return (
    <ThemeProvider theme={theme}>
      <YourApp />
    </ThemeProvider>
  );
}
```

### 3. Using Theme Context

```typescript
import { AppProvider, useTheme } from '@/theme/theme-factory-examples';

function MyComponent() {
  const { theme, mode, setTheme, setMode } = useTheme();
  
  return (
    <div>
      <p>Current Theme: {theme} ({mode})</p>
      <button onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}>
        Toggle Dark Mode
      </button>
    </div>
  );
}

export function App() {
  return (
    <AppProvider>
      <MyComponent />
    </AppProvider>
  );
}
```

---

## Theme Options

### Light Themes

| Theme | Primary | Secondary | Best For |
|-------|---------|-----------|----------|
| **Professional** | Blue (#2196F3) | Teal (#009688) | General purpose, modern look |
| **Corporate** | Deep Blue (#1565C0) | Gray (#616161) | Formal presentations, enterprise |
| **Construction** | Orange (#FF6F00) | Blue (#1565C0) | Construction industry, branding |
| **Minimal** | Blue (#2196F3) | Gray (#9E9E9E) | Data-focused, clean interface |

### Dark Themes

| Theme | Primary | Secondary | Best For |
|-------|---------|-----------|----------|
| **Professional** | Light Blue (#64B5F6) | Light Teal | Reduced eye strain, evening use |
| **Corporate** | Light Blue (#BBDEFB) | Light Gray | Dark presentations, accessibility |
| **Construction** | Amber (#FFB74D) | Light Blue | Night mode, construction sites |

### Import Examples

```typescript
// Light themes
import {
  professionalLightTheme,
  corporateLightTheme,
  constructionLightTheme,
  minimalLightTheme,
} from '@/theme/theme-factory';

// Dark themes
import {
  professionalDarkTheme,
  corporateDarkTheme,
  constructionDarkTheme,
} from '@/theme/theme-factory';

// Dynamic theme selection
import { getTheme } from '@/theme/theme-factory';
const theme = getTheme('professional', 'light');
```

---

## Typography System

### Font Stack

```typescript
// Primary (Body text, UI)
Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, ...

// Monospace (Code)
Menlo, Monaco, Courier New, monospace

// Headings
Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif
```

### Text Styles

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| **h1** | 2.5rem | 700 | Page titles |
| **h2** | 2rem | 700 | Section titles |
| **h3** | 1.75rem | 600 | Subsection titles |
| **h4** | 1.5rem | 600 | Card titles |
| **h5** | 1.25rem | 600 | Subheadings |
| **h6** | 1rem | 600 | Minor headings |
| **subtitle1** | 1rem | 500 | Primary subtitles |
| **subtitle2** | 0.875rem | 500 | Secondary subtitles |
| **body1** | 1rem | 400 | Primary body text |
| **body2** | 0.875rem | 400 | Secondary body text |
| **caption** | 0.75rem | 500 | Image captions, labels |
| **button** | 0.875rem | 600 | Button labels |
| **overline** | 0.75rem | 700 | Section overlines |

### Usage in Components

```typescript
import { useTheme } from '@mui/material/styles';
import { Typography, Box } from '@mui/material';

export function MyComponent() {
  const theme = useTheme();

  return (
    <Box sx={{ fontFamily: theme.typography.fontFamily }}>
      <Typography variant="h1">Page Title</Typography>
      <Typography variant="body1">Body text with professional font</Typography>
    </Box>
  );
}
```

---

## Color Palettes

### Primary Palette (Blue)

```
50:  #E3F2FD
100: #BBDEFB
200: #90CAF9
300: #64B5F6
400: #42A5F5
500: #2196F3  ← Main color
600: #1E88E5
700: #1976D2
800: #1565C0
900: #0D47A1
```

**Best for:** Primary actions, main UI elements, focus states

### Secondary Palette (Teal)

```
50:  #E0F2F1
100: #B2DFDB
200: #80CBC4
300: #4DB6AC
400: #26A69A
500: #009688  ← Main color
600: #00897B
700: #00796B
800: #00695C
900: #004D40
```

**Best for:** Secondary actions, accents, alternative interactions

### Status Colors

```
Success:  #00C853 (Bright green)
Warning:  #FF6D00 (Deep orange)
Error:    #D32F2F (Deep red)
Info:     #0288D1 (Light blue)
Disabled: #BDBDBD (Gray)
```

### Neutral Palette (Gray)

```
50:  #FAFAFA (Off-white)
100: #F5F5F5
200: #EEEEEE
300: #E0E0E0
400: #BDBDBD
500: #9E9E9E
600: #757575
700: #616161
800: #424242
900: #212121 (Near black)
```

**Best for:** Borders, dividers, backgrounds, text hierarchy

### Discipline-Specific Colors

```typescript
const disciplines = {
  structural:          '#0D47A1',  // Deep blue
  mep:                 '#FF6F00',  // Deep orange
  architectural:       '#6A1B9A',  // Deep purple
  civil:               '#00695C',  // Deep teal
  electrical:          '#FFB300',  // Bright amber
  mechanical:          '#0277BD',  // Cyan
  plumbing:            '#1565C0',  // Primary blue
  fire_safety:         '#D32F2F',  // Deep red
  general_contractor:  '#455A64',  // Blue gray
  sustainability:      '#00C853',  // Bright green
};
```

### Access Colors Programmatically

```typescript
import { palettes } from '@/theme/theme-factory';

const primaryColor = palettes.primary[500];      // #2196F3
const dangerColor = palettes.status.error;       // #D32F2F
const structuralColor = palettes.disciplines.structural; // #0D47A1
```

---

## Component Styling

### Buttons

```typescript
<Button variant="contained">
  Primary Action
</Button>

<Button variant="outlined">
  Secondary Action
</Button>

<Button variant="text">
  Tertiary Action
</Button>
```

**Styling:**
- Border radius: 6px
- Font weight: 600 (bold)
- Padding: 8px 16px
- Hover effect: Subtle lift (translateY -2px)
- Smooth transitions: 0.2s ease

### Cards

```typescript
<Card>
  <CardContent>
    <Typography>Card content</Typography>
  </CardContent>
</Card>
```

**Styling:**
- Border radius: 12px
- Box shadow: 0 2px 8px (subtle)
- Hover shadow: 0 8px 24px (enhanced)
- Smooth transitions: 0.3s ease

### Input Fields

```typescript
<TextField
  variant="outlined"
  label="Input field"
/>
```

**Styling:**
- Border radius: 6px
- Consistent with button styling
- Clear focus states
- Accessible contrast ratios

### Chips & Badges

```typescript
<Chip label="Badge" />
```

**Styling:**
- Border radius: 6px (consistent)
- Font weight: 500 (readable)
- Proper spacing and padding

---

## Utility Functions

### Get Discipline Color

```typescript
import { getDisciplineColor } from '@/theme/theme-factory';

const color = getDisciplineColor('structural');      // #0D47A1
const color = getDisciplineColor('Mechanical MEP');  // #0277BD
```

### Get Severity Color

```typescript
import { getSeverityColor } from '@/theme/theme-factory';

const color = getSeverityColor(85, 80);  // Exceeds threshold → Error color
const color = getSeverityColor(75, 80);  // Within threshold → Warning color
const color = getSeverityColor(40, 80);  // Below threshold → Success color
```

### Get Sequential Color

```typescript
import { getSequentialColor } from '@/theme/theme-factory';

const color = getSequentialColor(0.2);   // #E0E0E0 (gray)
const color = getSequentialColor(0.5);   // #FFC107 (yellow)
const color = getSequentialColor(0.9);   // #00C853 (green)
```

---

## Integration Guide

### Step 1: Update Main App Component

**File:** `frontend/src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppProvider } from '@/theme/theme-factory-examples'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </React.StrictMode>,
)
```

### Step 2: Access Theme in Components

```typescript
import { useTheme } from '@/theme/theme-factory-examples';

export function MyComponent() {
  const { theme, mode, setTheme, setMode } = useTheme();

  return (
    <div>
      <p>Using {theme} theme in {mode} mode</p>
      <button onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}>
        Toggle Dark Mode
      </button>
    </div>
  );
}
```

### Step 3: Use Direct Theme Values

```typescript
import { useTheme } from '@mui/material/styles';

export function StyledComponent() {
  const theme = useTheme();

  return (
    <div style={{
      backgroundColor: theme.palette.background.paper,
      color: theme.palette.text.primary,
      borderRadius: theme.shape.borderRadius,
      padding: theme.spacing(2),
    }}>
      Content with theme styling
    </div>
  );
}
```

### Step 4: Add Theme Settings to Dashboard

Create a settings panel to allow users to switch themes:

```typescript
import { AVAILABLE_THEMES, AVAILABLE_MODES } from '@/theme/theme-factory-examples';
import { useTheme } from '@/theme/theme-factory-examples';

export function ThemeSettings() {
  const { theme, mode, setTheme, setMode } = useTheme();

  return (
    <div>
      <h3>Theme Settings</h3>
      
      <div>
        <label>Theme:</label>
        <select value={theme} onChange={(e) => setTheme(e.target.value as any)}>
          {AVAILABLE_THEMES.map(t => (
            <option key={t.id} value={t.id}>{t.name}</option>
          ))}
        </select>
      </div>

      <div>
        <label>Mode:</label>
        <select value={mode} onChange={(e) => setMode(e.target.value as any)}>
          {AVAILABLE_MODES.map(m => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
```

---

## Best Practices

### ✅ DO

- **Use theme colors** via Material-UI theme provider
- **Leverage utility functions** for dynamic coloring
- **Maintain consistent spacing** using `theme.spacing()`
- **Respect typography hierarchy** - don't overuse heading styles
- **Test accessibility** - use theme contrast ratios
- **Save user preferences** - persist theme choices to localStorage

### ❌ DON'T

- **Hardcode colors** - always use `theme.palette`
- **Override component styles** unnecessarily
- **Mix font families** - stick to theme font stack
- **Ignore WCAG standards** - verify contrast ratios
- **Use deprecated colors** - refer to palettes export
- **Create custom colors** - use existing palette instead

### Accessibility Guidelines

1. **Text Contrast** - All text meets WCAG AA standards (4.5:1 for body text)
2. **Color Not Alone** - Don't use color as sole indicator (add icons/text)
3. **Focus States** - All interactive elements have visible focus indicators
4. **Status Indicators** - Use semantic colors (success, warning, error)

### Performance Tips

1. **Lazy load themes** - Import only needed themes
2. **Memoize theme context** - Prevent unnecessary re-renders
3. **Use sx prop** - More performant than inline styles
4. **Cache computed colors** - Store color calculations in useMemo

---

## File Structure

```
frontend/src/theme/
├── theme.ts                      (Original theme - for backwards compatibility)
├── theme-factory.ts              (Main theme factory system)
├── theme-factory-examples.tsx    (Example components and usage)
├── THEME_FACTORY_GUIDE.md        (This file)
└── README.md                     (Quick reference)
```

---

## Migration from Old Theme

If migrating from the original `theme.ts`:

```typescript
// Old way
import { theme } from '@/theme/theme';
<ThemeProvider theme={theme}>

// New way - recommended
import { professionalLightTheme } from '@/theme/theme-factory';
<ThemeProvider theme={professionalLightTheme}>

// Or use dynamic selection
import { getTheme } from '@/theme/theme-factory';
const theme = getTheme('professional', 'light');
<ThemeProvider theme={theme}>
```

---

## Troubleshooting

### Fonts Not Loading

Check `frontend/index.html` or `main.tsx` for Inter font import:

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Colors Not Applied

Verify ThemeProvider wraps your app:

```typescript
<ThemeProvider theme={theme}>
  <CssBaseline />
  <App />
</ThemeProvider>
```

### Dark Mode Not Working

Ensure `CssBaseline` component is included (resets browser defaults).

---

## Support & Customization

For custom color palettes or additional themes, modify `theme-factory.ts`:

1. Add new palette object in `LIGHT_PALETTES` or `DARK_PALETTES`
2. Create new theme export using `createProfessionalTheme()`
3. Add to `themeRegistry` and `getTheme()` function

---

## Version History

- **v2.0.0** - Theme Factory System Launch
  - 8 professional themes
  - Enterprise typography system
  - Semantic color palettes
  - Utility functions and helpers

---

**Last Updated:** January 2026  
**Maintained By:** Design Systems Team
