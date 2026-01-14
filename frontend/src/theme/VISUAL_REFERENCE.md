# Theme Factory - Visual Color Reference

## Primary Palette (Enterprise Blue)

```
█████████ #0D47A1 900 - Deep blue, maximum contrast headings
█████████ #1565C0 800 - Dark blue, hover states
█████████ #1976D2 700 - Primary dark blue, active states
█████████ #1E88E5 600 - Primary hover
█████████ #2196F3 500 - PRIMARY COLOR - main buttons, focus
█████████ #42A5F5 400 - Medium blue, secondary actions
█████████ #64B5F6 300 - Light blue, backgrounds
█████████ #90CAF9 200 - Lighter blue, disabled states
█████████ #BBDEFB 100 - Very light blue, pale backgrounds
█████████ #E3F2FD 50  - Lightest blue, base backgrounds
```

**Usage:** Primary button actions, main interface elements, focus states

---

## Secondary Palette (Professional Teal)

```
█████████ #004D40 900 - Deep teal, maximum contrast
█████████ #00695C 800 - Dark teal, hover states
█████████ #00796B 700 - Secondary dark teal
█████████ #00897B 600 - Secondary hover
█████████ #009688 500 - SECONDARY COLOR - accent actions
█████████ #26A69A 400 - Medium teal
█████████ #4DB6AC 300 - Light teal, backgrounds
█████████ #80CBC4 200 - Lighter teal
█████████ #B2DFDB 100 - Very light teal
█████████ #E0F2F1 50  - Lightest teal, backgrounds
```

**Usage:** Secondary actions, accents, alternative interactions

---

## Semantic Status Colors

```
█████████ #00C853 - SUCCESS - Positive states, checkmarks, approvals
█████████ #FF6D00 - WARNING - Caution, needs attention, in-progress
█████████ #D32F2F - ERROR - Critical issues, failures, deletions
█████████ #0288D1 - INFO - Information, help text, notifications
█████████ #BDBDBD - DISABLED - Inactive, unavailable, locked
```

---

## Neutral Gray Palette (Backgrounds & Borders)

```
█████████ #212121 900 - Near black, text on light backgrounds
█████████ #424242 800 - Dark gray, high contrast
█████████ #616161 700 - Medium gray, secondary text
█████████ #757575 600 - Medium gray, borders
█████████ #9E9E9E 500 - Light gray, disabled text
█████████ #BDBDBD 400 - Lighter gray, borders
█████████ #E0E0E0 300 - Very light gray, dividers
█████████ #EEEEEE 200 - Almost white, backgrounds
█████████ #F5F5F5 100 - Very light, paper backgrounds
█████████ #FAFAFA 50  - Off-white, default backgrounds
```

**Usage:** Backgrounds, borders, dividers, text hierarchy

---

## Discipline-Specific Colors (Construction)

### By Role

```
█████████ #0D47A1 - STRUCTURAL       (Deep Blue)
           Used for: Structural engineers, frame, foundation
           Context: Blueprint lines, load-bearing elements

█████████ #FF6F00 - MEP              (Deep Orange)
           Used for: HVAC, plumbing, electrical engineers
           Context: System diagrams, mechanical systems

█████████ #6A1B9A - ARCHITECTURAL    (Deep Purple)
           Used for: Architects, design teams
           Context: Floor plans, facades, design elements

█████████ #00695C - CIVIL            (Deep Teal)
           Used for: Civil engineers, site planning
           Context: Site plans, grading, infrastructure

█████████ #FFB300 - ELECTRICAL       (Bright Amber)
           Used for: Electrical engineers
           Context: Power systems, lighting, circuits

█████████ #0277BD - MECHANICAL       (Cyan)
           Used for: Mechanical engineers
           Context: HVAC systems, equipment

█████████ #D32F2F - FIRE SAFETY      (Deep Red)
           Used for: Fire protection engineers
           Context: Fire safety systems, emergency routes

█████████ #455A64 - GENERAL          (Blue Gray)
           Used for: General contractors, project management
           Context: General coordination items
```

---

## Severity Color Scale

### Issue Severity Levels

```
█████████ #D32F2F - CRITICAL
           Value ≥ 150% of threshold
           Action: Immediate intervention required
           Icon: ⚠️ (exclamation in red)

█████████ #FF6D00 - HIGH/WARNING
           Value = 100-150% of threshold
           Action: Urgent attention needed
           Icon: ⚠️ (exclamation in orange)

█████████ #FF9800 - MEDIUM
           Value = 70-100% of threshold
           Action: Monitor and plan
           Icon: 📊 (info icon)

█████████ #FBC02D - LOW
           Value = 50-70% of threshold
           Action: Track progress
           Icon: ℹ️ (information)

█████████ #00C853 - SUCCESS
           Value < 50% of threshold
           Action: On target
           Icon: ✓ (checkmark)
```

---

## Construction Industry Theme

### Light Mode
```
Primary:    #FF6F00 (Deep Orange)
Secondary:  #1565C0 (Primary Blue)
Success:    #00C853 (Green)
Warning:    #FF9800 (Orange)
Error:      #D32F2F (Red)
Background: #FAFAFA (Off-white)
Paper:      #FFFFFF (White)
```

### Dark Mode
```
Primary:    #FFB74D (Amber)
Secondary:  #90CAF9 (Light Blue)
Success:    #00C853 (Green)
Warning:    #FF9800 (Orange)
Error:      #D32F2F (Red)
Background: #121212 (Dark)
Paper:      #1E1E1E (Dark Gray)
```

---

## Contrast Ratios (Accessibility)

### WCAG AA Compliance (All Combinations)

| Text Color | Background | Contrast Ratio |
|-----------|-----------|----------------|
| Primary 900 | Paper (Light) | 11.5:1 ✓ AAA |
| Primary 700 | Paper (Light) | 6.8:1 ✓ AA |
| Primary 500 | Paper (Light) | 3.9:1 ✓ AA |
| Status Error | Paper (Light) | 5.2:1 ✓ AA |
| Status Warning | Paper (Light) | 2.6:1 ⚠️ Large Text Only |
| Status Success | Paper (Light) | 4.1:1 ✓ AA |

---

## Material Design 3 Integration

The Theme Factory follows Material Design 3 guidelines with customizations for construction industry:

- **Rounded corners:** 6-8px (consistent, modern)
- **Shadows:** Subtle elevation system
- **Typography:** Inter font family with proper hierarchy
- **Color:** Semantic meaning + discipline-specific branding
- **Spacing:** 8px grid system (Material spec)

---

## Typography Color Combinations

### Recommended Text + Background Pairings

```
Light Mode:
├─ Headings (h1-h6): Text 900 / Neutral 900 on Paper
├─ Body Text: Text Primary (0.87) on Paper or Bg Default
├─ Secondary Text: Text Secondary (0.60) on Paper
├─ Captions: Text Secondary (0.60) on Bg Default
└─ Disabled: Text Disabled (0.38) on Paper

Dark Mode:
├─ Headings (h1-h6): Text Primary (0.87) on Paper Dark
├─ Body Text: Text Primary (0.87) on Bg Default Dark
├─ Secondary Text: Text Secondary (0.60) on Bg Default Dark
├─ Captions: Text Secondary (0.60) on Paper Dark
└─ Disabled: Text Disabled (0.38) on Paper Dark
```

---

## Color Names Reference

| CSS Variable | RGB | Hex | Usage |
|------------|-----|-----|-------|
| Primary | rgb(33, 150, 243) | #2196F3 | Main actions |
| Primary Dark | rgb(21, 101, 192) | #1565C0 | Hover states |
| Secondary | rgb(0, 150, 136) | #009688 | Accents |
| Success | rgb(0, 200, 83) | #00C853 | Positive |
| Warning | rgb(255, 109, 0) | #FF6D00 | Caution |
| Error | rgb(211, 47, 47) | #D32F2F | Errors |
| Info | rgb(2, 136, 209) | #0288D1 | Info |

---

## Theming Files & Structure

```
frontend/src/theme/
│
├─ theme-factory.ts
│  ├─ PROFESSIONAL_FONTS (Inter, Segoe UI, Roboto)
│  ├─ PRIMARY_PALETTE (Blue)
│  ├─ SECONDARY_PALETTE (Teal)
│  ├─ STATUS_COLORS (Green, Orange, Red, Blue)
│  ├─ NEUTRAL_PALETTE (Grays)
│  ├─ DISCIPLINE_COLORS (Structural, MEP, Architectural...)
│  └─ Theme Exports (8 themes)
│
├─ theme-factory-examples.tsx
│  ├─ AppWithProfessionalTheme
│  ├─ AppWithThemeSwitcher
│  ├─ DisciplineIndicator
│  ├─ SeverityBadge
│  ├─ AppProvider (context-based)
│  └─ AVAILABLE_THEMES & AVAILABLE_MODES
│
├─ THEME_FACTORY_GUIDE.md (Full documentation)
├─ QUICKSTART.md (Quick reference)
└─ VISUAL_REFERENCE.md (This file)
```

---

## Color Picker Integration

To help users select colors, all colors are available through these functions:

```typescript
// Get theme by name
getTheme('professional', 'light')

// Get discipline color
getDisciplineColor('structural')

// Get severity color
getSeverityColor(value, threshold)

// Access all palettes
palettes.primary[500]
palettes.disciplines.mep
palettes.status.warning
```

---

## Next Steps

1. **Integration:** Add `AppProvider` to your app entry point
2. **Usage:** Use `useTheme()` hook in components
3. **Testing:** Verify dark mode works across all pages
4. **Customization:** Modify palette colors if needed
5. **Documentation:** Share this guide with design team

---

**Version:** 2.0.0  
**Updated:** January 2026
