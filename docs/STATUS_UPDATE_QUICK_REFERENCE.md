# Status Update - Quick Reference

## 🚀 Quick Start

```powershell
# Run application
python run_enhanced_ui.py

# Run backend tests
python tools\test_status_update_quick.py
```

## 📋 Status Options

| Status | Display | Progress | Use Case |
|--------|---------|----------|----------|
| `planned` | `[ ] Planned` | 0% | Service not yet started |
| `in_progress` | `[~] In Progress` | 50% | Service currently being delivered |
| `completed` | `[X] Completed` | 100% | Service fully delivered |

## 🎯 UI Workflow

1. **Open**: Review Management → Service Setup
2. **Select**: Click on non-review service (lump_sum, audit, etc.)
3. **Update**: Click "Update Status" button
4. **Choose**: Select radio button for new status
5. **Confirm**: Click "Update"
6. **Verify**: Check billing KPIs updated

## 🔒 Protection

- ❌ **Cannot update**: Review-type services (auto-calculated)
- ✅ **Can update**: Lump sum, audit, license services

## 💰 Billing Impact

```
Billed Amount = Agreed Fee × (Progress % / 100)

Examples:
- $100,000 @ 0% (planned)     = $0
- $100,000 @ 50% (in progress) = $50,000  
- $100,000 @ 100% (completed) = $100,000
```

## 📊 Where to See Updates

1. **Service Setup Tab**: Service table (progress_pct column)
2. **Project Setup Tab**: Billable by Stage table
3. **Billing Tab**: Total Billable by Stage & Month tables

## 🐛 Fixed Issues

1. ✅ Unicode emoji encoding errors → Replaced with ASCII
2. ✅ Database column mismatch → Removed `last_updated` reference

## ✅ Tests Available

```powershell
# Comprehensive tests
python tools\test_non_review_status.py

# Quick verification
python tools\test_status_update_quick.py
```

## 📚 Documentation

- **User Guide**: `docs/NON_REVIEW_STATUS_AND_BILLING_KPIS.md`
- **Testing Guide**: `docs/STATUS_UPDATE_TESTING_GUIDE.md`
- **Full Summary**: `docs/STATUS_UPDATE_IMPLEMENTATION_SUMMARY.md`

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Button disabled | Select a service first |
| "Cannot update review" error | Normal - reviews auto-calculate |
| "Failed to update" error | Check DB connection, run tests |
| Billing not updating | Refresh tab, verify agreed_fee set |

---

**Status**: ✅ Fully Functional  
**Last Tested**: Service 204 (BIM Strategy & Setup) - All transitions working
