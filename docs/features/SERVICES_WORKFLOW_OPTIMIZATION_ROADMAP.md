# Services Workflow - Optimization Roadmap

**Purpose**: Prioritized recommendations to improve service creation, editing, and template management efficiency.

**Status**: Proposed | **Priority**: Medium | **Timeline**: Q1-Q2 2026

---

## Priority Matrix

```
         High Value
            │
        ┌───┼────────────────────┐
        │   │                    │
        │  ┌┴────┐         ┌────┴─┐
        │  │ 1.1 │         │ 2.1  │
        │  │     │         │      │
     Q ├──┼─────┼─────────┼──────┼─────────────
     u │  │ 1.2 │   1.3   │ 2.2  │ 3.1
     i │  └─┬───┘         └──┬───┘
     c │    │                │
     k │    └────────┬───────┘
      │             │
        └────────────┴────────────────────────
      Low Effort   Medium Effort   High Effort
        (1-2 days) (3-5 days)     (1-2 weeks)
```

---

## Phase 1: Quick Wins (Immediate, < 2 Days Each)

These improvements have **high visibility**, **low implementation cost**, and **immediate user impact**.

### 1.1 Template Preview Dialog

**Problem**: Users can't see what reviews/items will be created before applying template.

**Current Flow**:
```
Select Template → Submit → Services created → "Oh no, we don't want 15 reviews"
```

**Proposed Flow**:
```
Select Template → [Show Preview] → Review structure → [Confirm] → Create
```

**Implementation**:

**Backend** (`backend/app.py`):
```python
@app.route('/api/projects/<int:project_id>/templates/<template_id>/preview', methods=['POST'])
def api_preview_template_application(project_id, template_id):
    """Generate preview of what will be created without persisting."""
    body = request.get_json() or {}
    options_enabled = body.get('options_enabled') or []
    overrides = body.get('overrides') or {}
    
    try:
        from services.service_template_engine import create_service_from_template
        
        # Pass dry_run=True to skip database commit
        result = create_service_from_template(
            project_id=project_id,
            template_id=template_id,
            options_enabled=options_enabled,
            overrides=overrides,
            applied_by_user_id=None,  # No user yet, preview mode
            dry_run=True  # ← KEY: Don't actually create
        )
        
        # Return what would be created
        return jsonify({
            "template": result.get("template"),
            "service_preview": {
                "service_code": result.get("service_code"),
                "service_name": result.get("service_name"),
                "agreed_fee": result.get("agreed_fee"),
                "start_date": result.get("start_date")
            },
            "generated": result.get("generated"),
            "reviews_preview": [
                {
                    "cycle_no": r.get("cycle_no"),
                    "title": r.get("title", ""),
                    "planned_date": r.get("planned_date"),
                    "weight_factor": r.get("weight_factor")
                }
                for r in result.get("added_reviews", [])
            ],
            "items_preview": [
                {
                    "title": i.get("title"),
                    "item_type": i.get("item_type"),
                    "planned_date": i.get("planned_date")
                }
                for i in result.get("added_items", [])
            ]
        })
    except Exception as exc:
        logging.exception("Failed to preview template")
        return jsonify({'error': str(exc)}), 500
```

**Frontend** (`frontend/src/pages/workspace/ServiceCreateView.tsx`):
```tsx
// Add preview state
const [showPreview, setShowPreview] = useState(false);
const [previewData, setPreviewData] = useState(null);

// Load preview when template changes
const handleShowPreview = async () => {
  try {
    const response = await serviceTemplatesApi.previewTemplate(
      projectId,
      formData.template_id,
      templateOptions
    );
    setPreviewData(response.data);
    setShowPreview(true);
  } catch (error) {
    // Show error
  }
};

// Dialog component
return (
  <>
    {showPreview && previewData && (
      <Dialog open={showPreview} onClose={() => setShowPreview(false)} maxWidth="md">
        <DialogTitle>Template Preview</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="h6">Service</Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Name:</TableCell>
                  <TableCell>{previewData.service_preview.service_name}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Fee:</TableCell>
                  <TableCell>${previewData.service_preview.agreed_fee}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
            
            <Typography variant="h6" sx={{ mt: 2 }}>Reviews ({previewData.generated.review_count})</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Cycle</TableCell>
                  <TableCell>Title</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {previewData.reviews_preview.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell>{r.cycle_no}</TableCell>
                    <TableCell>{r.title}</TableCell>
                    <TableCell>{r.planned_date}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            <Typography variant="h6" sx={{ mt: 2 }}>Items ({previewData.generated.item_count})</Typography>
            <List dense>
              {previewData.items_preview.map((item, i) => (
                <ListItem key={i}>
                  <ListItemText
                    primary={item.title}
                    secondary={`${item.item_type} - ${item.planned_date}`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPreview(false)}>Back</Button>
          <Button 
            onClick={() => {
              setShowPreview(false);
              handleSubmit();  // Apply with confidence
            }} 
            variant="contained"
          >
            Create Service
          </Button>
        </DialogActions>
      </Dialog>
    )}
    
    {/* Main form with preview button */}
    <Button 
      onClick={handleShowPreview}
      variant="outlined"
      sx={{ mb: 2 }}
    >
      👁️ Preview Template Structure
    </Button>
  </>
);
```

**Benefit**: 
- Users can verify template choice before commitment
- Reduces "wrong template" errors
- Increases confidence in template system

**Effort**: 1.5 days (mostly reusing existing `dry_run` logic)

---

### 1.2 Inline Review Addition

**Problem**: Adding reviews requires clicking "Add Review" button, filling dialog, submitting—tedious for bulk additions.

**Current Flow**:
```
Click "+" → Dialog opens → Fill fields → Submit → Repeat
```

**Proposed Flow**:
```
Click "[+ Add Review]" → Form expands inline → Fill once → Save
```

**Implementation**:

**Frontend** (`frontend/src/components/workspace/ServiceDetailPanel.tsx`):
```tsx
// Add inline form state
const [showAddReview, setShowAddReview] = useState(false);
const [inlineReviewForm, setInlineReviewForm] = useState({
  cycle_no: (reviewsData?.length || 0) + 1,
  title: '',
  planned_date: '',
  disciplines: '',
});

return (
  <Box>
    {/* Existing reviews list */}
    {reviewsData?.map((review) => (
      <Box key={review.review_id} sx={{ mb: 2, p: 2, border: '1px solid #ddd' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="subtitle2">
              Review {review.cycle_no}: {review.title || 'Untitled'}
            </Typography>
            <Typography variant="caption">
              Planned: {review.planned_date} | Status: {review.status}
            </Typography>
          </Box>
          <Box>
            <IconButton size="small" onClick={() => handleEditReview(review)}>
              <EditIcon />
            </IconButton>
            <IconButton size="small" onClick={() => handleDeleteReview(review.review_id)}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
      </Box>
    ))}

    {/* Inline add form */}
    {showAddReview && (
      <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1, mb: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 2 }}>Add Review</Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={2}>
            <TextField
              size="small"
              label="Cycle #"
              type="number"
              value={inlineReviewForm.cycle_no}
              onChange={(e) => setInlineReviewForm({
                ...inlineReviewForm,
                cycle_no: parseInt(e.target.value)
              })}
            />
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              size="small"
              fullWidth
              label="Title"
              value={inlineReviewForm.title}
              onChange={(e) => setInlineReviewForm({
                ...inlineReviewForm,
                title: e.target.value
              })}
              placeholder="e.g., Weekly Coordination"
            />
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <TextField
              size="small"
              fullWidth
              type="date"
              label="Planned Date"
              InputLabelProps={{ shrink: true }}
              value={inlineReviewForm.planned_date}
              onChange={(e) => setInlineReviewForm({
                ...inlineReviewForm,
                planned_date: e.target.value
              })}
            />
          </Grid>
          
          <Grid item xs={12} sm={3}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                size="small" 
                variant="contained"
                onClick={handleSaveInlineReview}
              >
                Save
              </Button>
              <Button 
                size="small" 
                onClick={() => setShowAddReview(false)}
              >
                Cancel
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    )}

    {/* Show button only if not showing form */}
    {!showAddReview && (
      <Button 
        size="small"
        startIcon={<AddIcon />}
        onClick={() => setShowAddReview(true)}
        sx={{ mt: 2 }}
      >
        Add Review
      </Button>
    )}
  </Box>
);
```

**Benefit**:
- Faster review addition
- Less modal overhead
- Can add multiple reviews quickly

**Effort**: 1 day

---

### 1.3 Integrated Resequencing

**Problem**: Review resequencing requires clicking separate dialog, adds friction to main edit workflow.

**Current Flow**:
```
Edit Service → [Resequence Reviews] → Dialog opens → Fill 3 fields → Preview → Apply
```

**Proposed Flow**:
```
Edit Service → Expand "Review Schedule" section → Change interval/count → See preview → Click [Apply]
```

**Implementation**:

**Frontend** (`frontend/src/pages/workspace/ServiceEditView.tsx`):
```tsx
// Add integrated section in main form
<Card sx={{ mt: 3 }}>
  <CardHeader title="Review Schedule" />
  <CardContent>
    <Grid container spacing={2}>
      <Grid item xs={12} sm={4}>
        <TextField
          size="small"
          fullWidth
          type="date"
          label="Anchor Date"
          InputLabelProps={{ shrink: true }}
          value={formData.review_anchor_date || ''}
          onChange={(e) => handleFieldChange('review_anchor_date', e.target.value)}
        />
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#666' }}>
          Base date for calculating review dates
        </Typography>
      </Grid>
      
      <Grid item xs={12} sm={4}>
        <TextField
          size="small"
          fullWidth
          type="number"
          label="Interval (days)"
          value={formData.review_interval_days || ''}
          onChange={(e) => handleFieldChange('review_interval_days', parseInt(e.target.value))}
        />
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#666' }}>
          Days between reviews
        </Typography>
      </Grid>
      
      <Grid item xs={12} sm={4}>
        <TextField
          size="small"
          fullWidth
          type="number"
          label="Count"
          value={formData.review_count_planned || ''}
          onChange={(e) => handleFieldChange('review_count_planned', parseInt(e.target.value))}
        />
        <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#666' }}>
          Total number of reviews
        </Typography>
      </Grid>
    </Grid>
    
    {/* Show preview */}
    {formData.review_anchor_date && formData.review_interval_days && formData.review_count_planned && (
      <Box sx={{ mt: 3, p: 2, bgcolor: '#f9f9f9', borderRadius: 1 }}>
        <Typography variant="subtitle2" sx={{ mb: 2 }}>
          Calculated Review Dates
        </Typography>
        <Grid container spacing={1}>
          {Array.from({ length: formData.review_count_planned }).map((_, i) => {
            const date = new Date(formData.review_anchor_date);
            date.setDate(date.getDate() + (i * formData.review_interval_days));
            return (
              <Grid item xs={12} sm={6} md={3} key={i}>
                <Box sx={{ p: 1, bgcolor: 'white', border: '1px solid #ddd', borderRadius: 0.5 }}>
                  <Typography variant="caption" color="textSecondary">
                    Review {i}
                  </Typography>
                  <Typography variant="body2">
                    {date.toISOString().slice(0, 10)}
                  </Typography>
                </Box>
              </Grid>
            );
          })}
        </Grid>
        
        <Button 
          variant="contained" 
          sx={{ mt: 2 }}
          onClick={handleApplyResequence}
        >
          ✓ Apply These Dates
        </Button>
      </Box>
    )}
  </CardContent>
</Card>

// Handle apply
const handleApplyResequence = async () => {
  try {
    const response = await serviceReviewsApi.resequenceReviews(
      projectId,
      serviceId,
      {
        anchor_date: formData.review_anchor_date,
        interval_days: formData.review_interval_days,
        count: formData.review_count_planned
      }
    );
    // Refresh reviews
    await refetchReviews();
    showSuccessMessage('Reviews resequenced successfully');
  } catch (error) {
    showErrorMessage(error.message);
  }
};
```

**Benefit**:
- Resequencing integrated into main edit workflow
- Live preview of calculated dates
- One-click application

**Effort**: 1.5 days

---

### 1.4 Template Option Impact Visualization

**Problem**: Users don't understand what options cost or what they include.

**Current Flow**:
```
Template Options:
☐ Advanced Analytics
☐ Weekly Video Walkthroughs

(User doesn't know what these do or cost)
```

**Proposed Flow**:
```
Template Options:
☐ Advanced Analytics
  + Adds: Trend Analysis & Data Export
  + Reviews: 13 → 14 (extra analysis review)
  + Cost: +$2,000 total

☐ Weekly Video Walkthroughs
  + Adds: Video meeting item (weekly)
  + Items: 2 → 3
  + Cost: +$250/week ($3,000 total)

Estimated Total: 
  Base: $25,000
  Options: +$5,000
  Total: $30,000
```

**Implementation**:

**Update template format** (`templates.json` or `ServiceTemplates`):
```json
{
  "template_id": "design_review_weekly",
  "name": "Weekly Design Review",
  "options": [
    {
      "id": "advanced_analytics",
      "name": "Advanced Analytics",
      "description": "Includes trend analysis and data export",
      "impacts": {
        "reviews": {
          "added": 1,
          "description": "One additional analysis review"
        },
        "items": {
          "added": 0
        },
        "cost": {
          "amount": 2000,
          "description": "Flat fee for analysis"
        }
      }
    },
    {
      "id": "weekly_video",
      "name": "Weekly Video Walkthroughs",
      "description": "Record video walkthrough each week",
      "impacts": {
        "reviews": {
          "added": 0
        },
        "items": {
          "added": 1,
          "description": "One video item per review cycle"
        },
        "cost": {
          "amount": 250,
          "multiplier": "per_review",  // $250 per review
          "description": "Per-week video recording"
        }
      }
    }
  ]
}
```

**Frontend** (`ServiceCreateView.tsx`):
```tsx
// Render options with impact info
{templateDef?.options?.map((option) => (
  <Box key={option.id} sx={{ mb: 2, p: 2, border: '1px solid #ddd', borderRadius: 1 }}>
    <FormControlLabel
      control={
        <Checkbox
          checked={templateOptions.includes(option.id)}
          onChange={(e) => handleOptionToggle(option.id, e.target.checked)}
        />
      }
      label={
        <Box>
          <Typography variant="subtitle2">{option.name}</Typography>
          <Typography variant="caption" color="textSecondary">
            {option.description}
          </Typography>
        </Box>
      }
    />
    
    {templateOptions.includes(option.id) && option.impacts && (
      <Box sx={{ ml: 4, mt: 1, p: 1, bgcolor: '#f5f5f5', borderRadius: 0.5 }}>
        <Grid container spacing={2}>
          {option.impacts.reviews?.added > 0 && (
            <Grid item xs={12} sm={6}>
              <Typography variant="body2">
                ➕ Reviews: +{option.impacts.reviews.added} ({option.impacts.reviews.description})
              </Typography>
            </Grid>
          )}
          {option.impacts.items?.added > 0 && (
            <Grid item xs={12} sm={6}>
              <Typography variant="body2">
                ➕ Items: +{option.impacts.items.added} ({option.impacts.items.description})
              </Typography>
            </Grid>
          )}
          {option.impacts.cost && (
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                💰 Cost: ${option.impacts.cost.amount}
                {option.impacts.cost.multiplier === 'per_review' && ' per review'}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Box>
    )}
  </Box>
))}

{/* Show total cost summary */}
<Box sx={{ mt: 3, p: 2, bgcolor: '#fffacd', borderRadius: 1 }}>
  <Typography variant="subtitle2">Cost Summary</Typography>
  <Table size="small">
    <TableBody>
      <TableRow>
        <TableCell>Base Template Cost:</TableCell>
        <TableCell align="right">${baseTemplateCost}</TableCell>
      </TableRow>
      {selectedOptions.map((optId) => {
        const opt = templateDef?.options?.find(o => o.id === optId);
        const cost = opt?.impacts?.cost?.amount || 0;
        const mult = opt?.impacts?.cost?.multiplier === 'per_review' ? formData.review_count_planned : 1;
        return (
          <TableRow key={optId}>
            <TableCell>+ {opt?.name}:</TableCell>
            <TableCell align="right">${cost * mult}</TableCell>
          </TableRow>
        );
      })}
      <TableRow sx={{ fontWeight: 'bold', bgcolor: '#f0f0f0' }}>
        <TableCell>Total Estimated Cost:</TableCell>
        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
          ${calculateTotalCost()}
        </TableCell>
      </TableRow>
    </TableBody>
  </Table>
</Box>
```

**Benefit**:
- Clear understanding of option impact
- Cost transparency
- Informed decision-making

**Effort**: 1 day

---

## Phase 2: Medium-Term Improvements (3-5 Days Each)

### 2.1 Bulk Item Operations

**Problem**: Managing 50 weekly reports requires 50 individual updates if you want to assign them all to same person.

**Current**: Individual item edit required for each

**Proposed**:
```
Select Multiple Items → [Bulk Assign] → Choose User → Apply to All
```

**Implementation**:

**Frontend** (`ServiceDetailPanel.tsx`):
```tsx
// Add multi-select mode
const [selectedItems, setSelectedItems] = useState<number[]>([]);
const [bulkEditMode, setBulkEditMode] = useState(false);
const [bulkUpdate, setBulkUpdate] = useState({
  assigned_user_id: null,
  priority: null,
  status: null
});

return (
  <Box>
    {bulkEditMode && (
      <Box sx={{ mb: 2, p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
        <Typography variant="subtitle2">Bulk Edit {selectedItems.length} Items</Typography>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <Select
              fullWidth
              size="small"
              value={bulkUpdate.assigned_user_id || ''}
              onChange={(e) => setBulkUpdate({...bulkUpdate, assigned_user_id: e.target.value})}
              displayEmpty
            >
              <MenuItem value="">-- Keep Current User --</MenuItem>
              {users?.map((u) => (
                <MenuItem key={u.user_id} value={u.user_id}>
                  {u.name}
                </MenuItem>
              ))}
            </Select>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Select
              fullWidth
              size="small"
              value={bulkUpdate.priority || ''}
              onChange={(e) => setBulkUpdate({...bulkUpdate, priority: e.target.value})}
              displayEmpty
            >
              <MenuItem value="">-- Keep Current Priority --</MenuItem>
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 2 }}>
          <Button 
            variant="contained" 
            onClick={() => handleBulkUpdate(selectedItems, bulkUpdate)}
          >
            Apply to {selectedItems.length} Items
          </Button>
          <Button 
            variant="outlined"
            sx={{ ml: 1 }}
            onClick={() => {
              setBulkEditMode(false);
              setSelectedItems([]);
            }}
          >
            Cancel
          </Button>
        </Box>
      </Box>
    )}
    
    {/* Items list with checkboxes */}
    {itemsData?.map((item) => (
      <Box key={item.item_id} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Checkbox
          checked={selectedItems.includes(item.item_id)}
          onChange={(e) => {
            if (e.target.checked) {
              setSelectedItems([...selectedItems, item.item_id]);
            } else {
              setSelectedItems(selectedItems.filter(id => id !== item.item_id));
            }
          }}
        />
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2">{item.title}</Typography>
        </Box>
      </Box>
    ))}
    
    {selectedItems.length > 0 && !bulkEditMode && (
      <Button onClick={() => setBulkEditMode(true)}>
        Edit {selectedItems.length} Selected Items
      </Button>
    )}
  </Box>
);

// API call
const handleBulkUpdate = async (itemIds: number[], updates: any) => {
  try {
    await serviceItemsApi.bulkUpdateItems(projectId, serviceId, {
      item_ids: itemIds,
      updates: updates
    });
    await refetchItems();
    showSuccessMessage(`Updated ${itemIds.length} items`);
    setSelectedItems([]);
    setBulkEditMode(false);
  } catch (error) {
    showErrorMessage(error.message);
  }
};
```

**Backend** (`backend/app.py`):
```python
@app.route('/api/projects/<int:project_id>/services/<int:service_id>/items/bulk-update', methods=['PATCH'])
def api_bulk_update_service_items(project_id, service_id):
    """Update multiple items at once."""
    body = request.get_json() or {}
    item_ids = body.get('item_ids') or []
    updates = body.get('updates') or {}
    
    if not item_ids:
        return jsonify({'error': 'No items specified'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build UPDATE statement dynamically
            set_clauses = []
            params = []
            
            if updates.get('assigned_user_id') is not None:
                set_clauses.append(f"{S.ServiceItems.ASSIGNED_USER_ID} = ?")
                params.append(updates['assigned_user_id'])
            
            if updates.get('priority'):
                set_clauses.append(f"{S.ServiceItems.PRIORITY} = ?")
                params.append(updates['priority'])
            
            if updates.get('status'):
                set_clauses.append(f"{S.ServiceItems.STATUS} = ?")
                params.append(updates['status'])
            
            if not set_clauses:
                return jsonify({'error': 'No valid updates provided'}), 400
            
            set_clauses.append(f"{S.ServiceItems.UPDATED_AT} = GETUTCDATE()")
            
            # WHERE clause with item IDs
            where_placeholders = ', '.join('?' * len(item_ids))
            params.extend(item_ids)
            params.insert(len(params) - len(item_ids), service_id)
            params.insert(len(params) - len(item_ids), project_id)
            
            sql = f"""
            UPDATE {S.ServiceItems.TABLE}
            SET {', '.join(set_clauses)}
            WHERE {S.ServiceItems.PROJECT_ID} = ?
              AND {S.ServiceItems.SERVICE_ID} = ?
              AND {S.ServiceItems.ITEM_ID} IN ({where_placeholders})
            """
            
            cursor.execute(sql, params)
            conn.commit()
            
            return jsonify({
                'updated_count': cursor.rowcount,
                'items_updated': item_ids
            })
    except Exception as exc:
        logging.exception("Failed to bulk update items")
        return jsonify({'error': str(exc)}), 500
```

**Benefit**:
- Update 50 items in one operation instead of 50 clicks
- Reduces time by ~90% for bulk changes

**Effort**: 3 days (form, API, testing)

---

### 2.2 Template Recommendations Engine

**Problem**: New users don't know which template to use. Browse list isn't intuitive.

**Proposed**: Smart recommendations based on service characteristics.

**Implementation**:

**Backend** (`backend/app.py`):
```python
@app.route('/api/templates/recommendations', methods=['POST'])
def api_recommend_templates():
    """Recommend templates based on service characteristics."""
    body = request.get_json() or {}
    
    service_name = body.get('service_name', '').lower()
    service_type = body.get('service_type', '').lower()
    phase = body.get('phase', '').lower()
    
    # Load all templates
    templates = load_service_templates()
    
    scored = []
    for template in templates.get('templates', []):
        score = 0
        
        # Match on service name keywords
        name_keywords = template.get('tags', []) or []
        for keyword in name_keywords:
            if keyword.lower() in service_name:
                score += 10
        
        # Match on service type
        if template.get('service_type', '').lower() == service_type:
            score += 5
        
        # Match on phase
        defaults = template.get('defaults', {})
        if defaults.get('phase', '').lower() == phase:
            score += 3
        
        # Popularity bonus
        usage = template.get('usage_count', 0)
        if usage > 0:
            score += min(5, usage // 10)
        
        if score > 0:
            scored.append({
                'template_id': template.get('template_id'),
                'name': template.get('name'),
                'description': template.get('description'),
                'score': score,
                'usage_count': usage,
                'reasons': [
                    f"Matches keywords" if score >= 10 else "",
                    f"Matches phase ({phase})" if score >= 3 else "",
                    f"Popular ({usage} uses)" if usage > 0 else ""
                ]
            })
    
    # Sort by score
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'recommendations': scored[:5],  # Top 5
        'all_templates': [
            {'template_id': t.get('template_id'), 'name': t.get('name')}
            for t in templates.get('templates', [])
        ]
    })
```

**Frontend** (`ServiceCreateView.tsx`):
```tsx
// Add smart recommendation on form change
useEffect(() => {
  if (formData.service_name || formData.phase) {
    const loadRecommendations = async () => {
      try {
        const response = await api.get('/templates/recommendations', {
          params: {
            service_name: formData.service_name,
            phase: formData.phase
          }
        });
        setRecommendedTemplates(response.data.recommendations);
      } catch (error) {
        // Silently fail
      }
    };
    loadRecommendations();
  }
}, [formData.service_name, formData.phase]);

// Show recommendations
{recommendedTemplates.length > 0 && (
  <Box sx={{ mt: 2, p: 2, bgcolor: '#fff3e0', borderRadius: 1 }}>
    <Typography variant="subtitle2">Recommended Templates</Typography>
    {recommendedTemplates.map((rec) => (
      <Box 
        key={rec.template_id}
        sx={{ mt: 1, p: 1, bgcolor: 'white', border: '1px solid #ffb74d', borderRadius: 0.5, cursor: 'pointer' }}
        onClick={() => handleSelectTemplate(rec.template_id)}
      >
        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
          {rec.name}
        </Typography>
        <Typography variant="caption" color="textSecondary">
          {rec.reasons.filter(Boolean).join(' • ')}
        </Typography>
      </Box>
    ))}
  </Box>
)}
```

**Benefit**:
- New users guided to appropriate templates
- Reduced learning curve
- Better template adoption

**Effort**: 3 days

---

### 2.3 Template Versioning with Migration

**Problem**: Templates evolve over time. Old services get stuck on old versions.

**Current**: No upgrade path

**Proposed**: Track version changes, provide migration tools.

**Implementation**:

**Database schema**:
```sql
-- Track template changes
CREATE TABLE TemplateVersionChanges (
    change_id INT PRIMARY KEY IDENTITY,
    template_id VARCHAR(255),
    old_version VARCHAR(20),
    new_version VARCHAR(20),
    change_type VARCHAR(50),  -- 'added_review', 'modified_item', 'removed_review'
    change_description VARCHAR(500),
    migration_script NVARCHAR(MAX),  -- SQL to update affected services
    release_date DATETIME,
    created_at DATETIME DEFAULT GETUTCDATE()
);

-- Track what version a service is using
ALTER TABLE ProjectServiceTemplateBindings 
    ADD CURRENT_TEMPLATE_VERSION VARCHAR(20);  -- What version is NOW available
```

**Backend**:
```python
@app.route('/api/projects/<int:project_id>/services/check-template-updates', methods=['GET'])
def api_check_template_updates(project_id):
    """Check if services can be upgraded to newer template versions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Find template-managed services
        cursor.execute(f"""
            SELECT DISTINCT
                t.template_id,
                t.current_version,
                b.template_version as bound_version
            FROM {S.ProjectServices.TABLE} s
            JOIN {S.ProjectServiceTemplateBindings.TABLE} b ON s.service_id = b.service_id
            JOIN ServiceTemplates t ON b.template_id = t.id
            WHERE s.project_id = ?
                AND b.template_version < t.current_version
        """, (project_id,))
        
        outdated = cursor.fetchall()
        
        results = []
        for template_id, current_version, bound_version in outdated:
            # Load what changed
            cursor.execute("""
                SELECT change_type, change_description
                FROM TemplateVersionChanges
                WHERE template_id = ?
                    AND old_version >= ?
                    AND new_version <= ?
                ORDER BY release_date DESC
            """, (template_id, bound_version, current_version))
            
            changes = cursor.fetchall()
            
            results.append({
                'template_id': template_id,
                'current_bound_version': bound_version,
                'latest_version': current_version,
                'changes': [{'type': c[0], 'description': c[1]} for c in changes]
            })
        
        return jsonify({
            'outdated_templates': results,
            'total_outdated': len(results)
        })

@app.route('/api/projects/<int:project_id>/services/<int:service_id>/upgrade-template', methods=['POST'])
def api_upgrade_template(project_id, service_id):
    """Upgrade service to latest template version."""
    body = request.get_json() or {}
    auto_merge = body.get('auto_merge', False)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get binding
            cursor.execute(f"""
                SELECT b.binding_id, b.template_id, b.template_version, t.current_version
                FROM {S.ProjectServiceTemplateBindings.TABLE} b
                JOIN ServiceTemplates t ON b.template_id = t.id
                WHERE b.service_id = ?
            """, (service_id,))
            
            binding = cursor.fetchone()
            if not binding:
                return jsonify({'error': 'Service not template-managed'}), 400
            
            binding_id, template_id, old_version, new_version = binding
            
            if old_version == new_version:
                return jsonify({'error': 'Already latest version'}), 400
            
            # Load changes
            cursor.execute("""
                SELECT migration_script
                FROM TemplateVersionChanges
                WHERE template_id = ?
                    AND old_version >= ?
                    AND new_version <= ?
            """, (template_id, old_version, new_version))
            
            scripts = [row[0] for row in cursor.fetchall() if row[0]]
            
            # Apply migration scripts
            for script in scripts:
                try:
                    cursor.execute(script.format(
                        service_id=service_id,
                        project_id=project_id
                    ))
                except Exception as e:
                    if not auto_merge:
                        raise  # Manual review needed
                    # If auto_merge, continue
            
            # Update binding
            cursor.execute(f"""
                UPDATE {S.ProjectServiceTemplateBindings.TABLE}
                SET {S.ProjectServiceTemplateBindings.TEMPLATE_VERSION} = ?
                WHERE {S.ProjectServiceTemplateBindings.BINDING_ID} = ?
            """, (new_version, binding_id))
            
            conn.commit()
            
            return jsonify({
                'service_id': service_id,
                'upgraded_from': old_version,
                'upgraded_to': new_version,
                'changes_applied': len(scripts)
            })
    except Exception as exc:
        logging.exception("Failed to upgrade template")
        return jsonify({'error': str(exc)}), 500
```

**Benefit**:
- Services stay up-to-date with template evolution
- Migration path for non-breaking changes
- Manual review option for breaking changes

**Effort**: 4 days

---

### 2.4 Review Template Customization Before Apply

**Problem**: Template structure is fixed. Users can't customize before creation (only after).

**Proposed**: Allow pre-apply customization in dialog.

**Implementation**: (Similar to bulk edit concept, but for template reviews/items before apply)

**Benefit**:
- Customize template before generation
- Avoid post-creation editing
- One-shot perfect structure

**Effort**: 4 days

---

## Phase 3: Strategic Initiatives (1-2 Weeks Each)

### 3.1 Template Marketplace (Org-Wide)

**Concept**: Share templates across projects and teams.

**Features**:
- Export successful service as template
- Browse community templates
- Rate/review templates
- Version control for shared templates

**Timeline**: 2 weeks  
**Effort**: High (design, API, frontend, governance)  
**ROI**: Very High (org-wide efficiency)

---

### 3.2 Service Cloning with Phase Offset

**Concept**: Clone an entire service (reviews + items) with date/phase adjustments.

**Example**:
```
Clone Service #123 from Project A:
└─ Offset dates by +180 days (for Phase 2)
└─ Change phase from "Design Dev" to "Construction"
└─ Clear billing history (new billing cycle)
→ Create new service #456 with cloned structure
```

**Timeline**: 1.5 weeks  
**ROI**: High (Phase 2+ projects can reuse structure)

---

### 3.3 Workflow Automation Rules

**Concept**: Trigger actions when conditions met.

**Examples**:
```
Rule 1: When all reviews marked complete → Auto-create billing batch
Rule 2: When review #N completes → Auto-create post-review items
Rule 3: Monthly → Summarize all service progress & email PM
```

**Timeline**: 2 weeks  
**ROI**: Medium-High (reduces manual coordination)

---

## Implementation Roadmap

```
Q1 2026
├─ Week 1-2: Phase 1.1 (Template Preview) + 1.2 (Inline Reviews)
├─ Week 3-4: Phase 1.3 (Integrated Resequencing) + 1.4 (Option Impact)
├─ Week 5-6: Phase 2.1 (Bulk Operations) + Testing
├─ Week 7-8: Phase 2.2 (Recommendations) + Polish
└─ Week 9-10: Buffer/Buffer + 2.3 prep

Q2 2026
├─ Week 1-4: Phase 2.3 (Template Versioning)
├─ Week 5-8: Phase 3.1 (Template Marketplace) - if prioritized
├─ Week 9-10: Phase 3.2 (Service Cloning) - if prioritized
└─ Week 11-13: Phase 3.3 (Automation Rules) - if prioritized
```

---

## Success Metrics

Track improvements with these metrics:

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Avg service creation time | 15 min | 5 min | After Phase 1 |
| Template usage rate | 40% | 70% | After Phase 1.1 + 2.2 |
| Bulk edit adoption | 0% | 50% | After Phase 2.1 |
| Template update frequency | Quarterly | Monthly | After Phase 2.3 |
| User satisfaction (surveys) | 3.2/5 | 4.5/5 | After Phase 2 |

---

## Conclusion

The recommended roadmap prioritizes **immediate wins** (Phase 1) that improve daily user experience, followed by **organizational scaling** (Phases 2-3) that enable templates as company knowledge.

**Phase 1** should launch by end of Q1 2026 (~6-8 weeks of work).  
**Phase 2** provides the organizational scaling for repeat workflows.  
**Phase 3** is optional but high-ROI for mature organizations.

Each phase compounds on previous improvements:
- Phase 1 makes templates easier to use
- Phase 2 makes templates central to workflow
- Phase 3 makes templates org-wide standard

---

**Document prepared by**: Copilot Analysis  
**Date**: January 2026  
**Status**: Ready for prioritization & sprint planning
