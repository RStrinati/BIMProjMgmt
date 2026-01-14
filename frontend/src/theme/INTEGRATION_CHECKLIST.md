# Theme Factory - Integration Checklist

## 📋 Pre-Integration Setup

- [ ] Review `THEME_FACTORY_GUIDE.md` for complete overview
- [ ] Review `QUICKSTART.md` for quick reference
- [ ] Review `VISUAL_REFERENCE.md` for color palette
- [ ] Confirm Material-UI 5.x is installed (`npm list @mui/material`)
- [ ] Confirm Inter font is available

## 🔧 Installation Steps

### Step 1: Verify Font Loading

In `frontend/public/index.html` or `frontend/src/main.tsx`:

```html
<head>
  <!-- Add Inter font from Google Fonts -->
  <link 
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" 
    rel="stylesheet"
  >
</head>
```

- [ ] Inter font link added
- [ ] Font loads without errors (check DevTools Network tab)

### Step 2: Update App Entry Point

File: `frontend/src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppProvider } from '@/theme/theme-factory-examples'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </React.StrictMode>,
)
```

- [ ] Import `AppProvider` added
- [ ] `AppProvider` wraps `<App />`
- [ ] `CssBaseline` included in AppProvider

### Step 3: Test Theme Loading

Run the development server:

```bash
cd frontend
npm run dev
```

- [ ] App loads without errors
- [ ] No console errors in DevTools
- [ ] Theme colors visible in UI
- [ ] Fonts display as Inter

### Step 4: Update Components

Replace hardcoded colors with theme utilities:

#### Before:
```typescript
<Card sx={{ backgroundColor: '#2196F3' }}>
  <Typography style={{ color: '#1976d2' }}>Text</Typography>
</Card>
```

#### After:
```typescript
import { useTheme } from '@mui/material/styles';

<Card sx={{ backgroundColor: theme.palette.primary.main }}>
  <Typography sx={{ color: theme.palette.primary.dark }}>Text</Typography>
</Card>
```

- [ ] Identify all hardcoded colors
- [ ] Replace with `theme.palette.*` values
- [ ] Test light and dark modes
- [ ] Verify contrast ratios with DevTools

### Step 5: Add Discipline-Based Colors

For components showing discipline information:

```typescript
import { getDisciplineColor } from '@/theme/theme-factory';

const MyDisciplineComponent = ({ discipline }) => {
  const color = getDisciplineColor(discipline);
  
  return (
    <Chip 
      label={discipline}
      sx={{ backgroundColor: `${color}20`, color: color }}
    />
  );
};
```

- [ ] Identify discipline-displaying components
- [ ] Implement `getDisciplineColor()` utility
- [ ] Test all 8 discipline types
- [ ] Verify colors match design guide

### Step 6: Add Severity-Based Colors

For components showing issue severity:

```typescript
import { getSeverityColor } from '@/theme/theme-factory';

const SeverityIndicator = ({ value, threshold }) => {
  const color = getSeverityColor(value, threshold);
  
  return (
    <Box sx={{ backgroundColor: color, color: '#fff', padding: 1 }}>
      Severity Level
    </Box>
  );
};
```

- [ ] Identify severity-displaying components
- [ ] Implement `getSeverityColor()` utility
- [ ] Test color thresholds
- [ ] Verify status semantics

### Step 7: Add Theme Switcher UI (Optional)

Create a theme settings component:

```typescript
import { useTheme } from '@/theme/theme-factory-examples';
import { AVAILABLE_THEMES, AVAILABLE_MODES } from '@/theme/theme-factory-examples';

export function ThemeSelector() {
  const { theme, mode, setTheme, setMode } = useTheme();

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <FormControl>
        <InputLabel>Theme</InputLabel>
        <Select 
          value={theme} 
          onChange={(e) => setTheme(e.target.value as any)}
        >
          {AVAILABLE_THEMES.map(t => (
            <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl>
        <InputLabel>Mode</InputLabel>
        <Select 
          value={mode} 
          onChange={(e) => setMode(e.target.value as any)}
        >
          {AVAILABLE_MODES.map(m => (
            <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
```

- [ ] Create theme selector component
- [ ] Add to app settings/preferences page
- [ ] Test theme switching
- [ ] Save preferences to localStorage (optional)

## 🧪 Testing Checklist

### Visual Testing

- [ ] Light mode displays correctly
- [ ] Dark mode displays correctly
- [ ] All 4 light themes render properly
- [ ] All 3 dark themes render properly
- [ ] Theme switching is smooth (no flashing)
- [ ] Fonts display as Inter throughout app

### Accessibility Testing

- [ ] All text meets WCAG AA contrast ratios
- [ ] Focus states are visible on all interactive elements
- [ ] Color is not the only way to convey information
- [ ] Semantic status colors used consistently
- [ ] Screen readers work with themed components

### Component Testing

- [ ] Buttons display with theme colors
- [ ] Cards have proper shadow and borders
- [ ] Inputs display correctly
- [ ] Chips and badges show theme colors
- [ ] AppBar styling is consistent

### Discipline Color Testing

```
- [ ] Structural = #0D47A1 (deep blue)
- [ ] MEP = #FF6F00 (deep orange)
- [ ] Architectural = #6A1B9A (deep purple)
- [ ] Civil = #00695C (deep teal)
- [ ] Electrical = #FFB300 (bright amber)
- [ ] Mechanical = #0277BD (cyan)
- [ ] Fire Safety = #D32F2F (deep red)
- [ ] General Contractor = #455A64 (blue gray)
```

### Severity Color Testing

```
- [ ] Critical (≥150%) = #D32F2F (red)
- [ ] High (100-150%) = #FF6D00 (orange)
- [ ] Medium (70-100%) = #FF9800 (light orange)
- [ ] Low (50-70%) = #FBC02D (yellow)
- [ ] Success (<50%) = #00C853 (green)
```

## 📱 Browser Testing

Test in all supported browsers:

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Chrome
- [ ] Mobile Safari

## 📄 Documentation

- [ ] Team notified of theme factory system
- [ ] Design guide shared with team
- [ ] Color palette provided to designers
- [ ] Integration steps documented
- [ ] Usage examples added to component storybook (if applicable)

## 🚀 Deployment

### Pre-Deployment

- [ ] All tests passing
- [ ] No console errors
- [ ] Dark mode tested end-to-end
- [ ] Theme switcher works (if implemented)
- [ ] Performance verified (no slowdowns)

### Deployment

- [ ] Build succeeds: `npm run build`
- [ ] No build warnings related to theming
- [ ] Production fonts load correctly
- [ ] Theme works in production environment

### Post-Deployment

- [ ] Verify theme in production
- [ ] Check no regressions
- [ ] Monitor user feedback
- [ ] Track theme preference analytics (optional)

## 🔄 Maintenance

### Regular Tasks

- [ ] Review unused colors quarterly
- [ ] Update theme if brand guidelines change
- [ ] Add new discipline colors if needed
- [ ] Monitor accessibility compliance

### Version Updates

- [ ] Document any theme changes
- [ ] Update CHANGELOG
- [ ] Notify team of changes
- [ ] Test with updated Material-UI versions

## 📚 Reference Files

All necessary files are in `frontend/src/theme/`:

1. **theme-factory.ts** (Main system)
   - All theme definitions
   - Color palettes
   - Utility functions
   - 800+ lines, fully documented

2. **theme-factory-examples.tsx** (Implementation examples)
   - Component examples
   - Context provider
   - Theme switcher
   - 200+ lines

3. **THEME_FACTORY_GUIDE.md** (Complete documentation)
   - Detailed overview
   - Usage patterns
   - Best practices
   - Troubleshooting

4. **QUICKSTART.md** (Quick reference)
   - Available themes
   - Color codes
   - Quick setup
   - Common patterns

5. **VISUAL_REFERENCE.md** (Color reference)
   - Color palettes
   - Discipline colors
   - Severity scales
   - Contrast ratios

## ❓ Support

### Common Issues

**Problem:** Fonts not loading
- Solution: Check Google Fonts link in HTML head
- Check: `frontend/public/index.html`

**Problem:** Dark mode not working
- Solution: Verify `CssBaseline` is rendered
- Check: AppProvider includes `<CssBaseline />`

**Problem:** Colors not updating
- Solution: Wrap app in `ThemeProvider` or `AppProvider`
- Check: Component hierarchy

**Problem:** Theme context undefined
- Solution: Use `AppProvider` instead of `ThemeProvider`
- Check: Import from `theme-factory-examples`

### Getting Help

1. Review `THEME_FACTORY_GUIDE.md`
2. Check `QUICKSTART.md` for common patterns
3. Review component examples in `theme-factory-examples.tsx`
4. Examine existing component usage in codebase

## ✅ Sign-Off

- [ ] Theme factory system installed
- [ ] All tests passing
- [ ] Team trained on usage
- [ ] Documentation reviewed
- [ ] Ready for production deployment

---

**Completed By:** _________________  
**Date:** _________________  
**Review Date:** _________________

---

**Questions?** Reference the THEME_FACTORY_GUIDE.md or check existing component implementations.
