# Theme Factory - Quick Reference

## 🎨 Available Themes

### Light Themes
- `professionalLightTheme` - Blue + Teal (default, modern)
- `corporateLightTheme` - Deep Blue + Gray (formal)
- `constructionLightTheme` - Orange + Blue (industry)
- `minimalLightTheme` - Blue + Gray (data-focused)

### Dark Themes
- `professionalDarkTheme` - Light Blue + Teal
- `corporateDarkTheme` - Light Blue + Light Gray
- `constructionDarkTheme` - Amber + Light Blue

## 🚀 Quick Setup

```typescript
import { ThemeProvider } from '@mui/material/styles';
import { professionalLightTheme } from '@/theme/theme-factory';
import { AppProvider } from '@/theme/theme-factory-examples';

// Option 1: Single theme
<ThemeProvider theme={professionalLightTheme}>
  <App />
</ThemeProvider>

// Option 2: Theme context (recommended)
<AppProvider>
  <App />
</AppProvider>
```

## 🎯 Access in Components

```typescript
// 1. Via hooks (theme context)
import { useTheme } from '@/theme/theme-factory-examples';
const { theme, mode, setTheme, setMode } = useTheme();

// 2. Via Material-UI hook (for styling)
import { useTheme } from '@mui/material/styles';
const theme = useTheme();

// 3. Via getTheme function
import { getTheme } from '@/theme/theme-factory';
const theme = getTheme('professional', 'light');
```

## 🌈 Color Utilities

```typescript
import { getDisciplineColor, getSeverityColor } from '@/theme/theme-factory';

// Discipline colors
getDisciplineColor('structural')  // #0D47A1
getDisciplineColor('mep')         // #FF6F00
getDisciplineColor('civil')       // #00695C

// Severity colors
getSeverityColor(95, 80)  // #D32F2F (critical - exceeds threshold)
getSeverityColor(75, 80)  // #FF6D00 (warning - at threshold)
getSeverityColor(50, 80)  // #00C853 (success - below threshold)
```

## 📝 Typography

```typescript
// Font stack (Inter primary, Segoe UI fallback)
theme.typography.fontFamily

// Predefined styles
<Typography variant="h1">Main title (2.5rem, bold)</Typography>
<Typography variant="h4">Card title (1.5rem, semibold)</Typography>
<Typography variant="body1">Body text (1rem, regular)</Typography>
<Typography variant="caption">Small text (0.75rem)</Typography>
```

## 🎨 Primary Colors

| Shade | Hex | Usage |
|-------|-----|-------|
| 300 | #64B5F6 | Light backgrounds |
| 500 | #2196F3 | Primary button, main UI |
| 700 | #1976D2 | Hover states |
| 900 | #0D47A1 | Deep emphasis |

## 🌍 Discipline Colors

| Discipline | Color | Hex |
|-----------|-------|-----|
| Structural | Blue | #0D47A1 |
| MEP | Orange | #FF6F00 |
| Architectural | Purple | #6A1B9A |
| Civil | Teal | #00695C |
| Electrical | Amber | #FFB300 |
| Mechanical | Cyan | #0277BD |
| Fire Safety | Red | #D32F2F |
| General | Gray | #455A64 |

## 🚨 Status Colors

| Status | Color | Hex |
|--------|-------|-----|
| Success | Green | #00C853 |
| Warning | Orange | #FF6D00 |
| Error | Red | #D32F2F |
| Info | Blue | #0288D1 |
| Disabled | Gray | #BDBDBD |

## 📦 Palettes Export

```typescript
import { palettes } from '@/theme/theme-factory';

palettes.primary[500]              // #2196F3
palettes.secondary[500]            // #009688
palettes.status.error              // #D32F2F
palettes.disciplines.structural    // #0D47A1
palettes.neutral[300]              // #E0E0E0
```

## 🎯 Common Patterns

### Colored Box
```typescript
const color = getDisciplineColor('structural');
<Box sx={{
  backgroundColor: `${color}20`,  // 20% opacity
  borderLeft: `4px solid ${color}`,
  padding: 2,
}}>
  Content
</Box>
```

### Status Badge
```typescript
const color = getSeverityColor(value, threshold);
<Chip
  label="Status"
  sx={{ backgroundColor: color, color: '#fff' }}
/>
```

### Themed Card
```typescript
<Card sx={{
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
}}>
  {/* content */}
</Card>
```

## 📖 Documentation

- Full guide: `THEME_FACTORY_GUIDE.md`
- Examples: `theme-factory-examples.tsx`
- Source: `theme-factory.ts`

## 🔄 Theme Switching

```typescript
<select onChange={(e) => setTheme(e.target.value as any)}>
  <option value="professional">Professional</option>
  <option value="corporate">Corporate</option>
  <option value="construction">Construction</option>
  <option value="minimal">Minimal</option>
</select>

<button onClick={() => setMode(mode === 'light' ? 'dark' : 'light')}>
  {mode === 'light' ? '🌙' : '☀️'} Toggle Mode
</button>
```

## ✨ Best Practices

✅ Use theme values, not hardcoded colors  
✅ Apply semantic status colors (success/error/warning)  
✅ Use discipline colors for role/team indication  
✅ Respect typography hierarchy  
✅ Test dark mode functionality  
✅ Verify accessibility (WCAG AA)  

---

**Files:** `theme-factory.ts` | `theme-factory-examples.tsx` | `THEME_FACTORY_GUIDE.md`
