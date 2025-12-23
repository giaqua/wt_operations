# Technical Questionnaire to Site Visit Request Integration - Quick Reference

## Overview
This guide explains how to create Site Visit Requests (SVR) directly from Technical Questionnaires (TQ) with intelligent field population and multi-site integration.

## Prerequisites
- ✅ Technical Questionnaire must be **submitted** (not draft)
- ✅ `Site Visit Required` checkbox must be checked
- ✅ Lead must be selected in the TQ

## Quick Steps

### 1. Complete and Submit TQ
```
TQ Form → Fill all fields → Check "Site Visit Required" → Submit
```

### 2. Create SVR from TQ
```
Submitted TQ → Click "Create Site Visit Request" → Review generated SVR
```

### 3. Complete SVR
```
Review auto-populated fields → Modify if needed → Save → Submit
```

### 4. Sync to External Site (Optional)
```
SVR → Click "Sync to External Site" → Confirm → External SVR created
```

## Auto-Generated Fields

### Visit Type Logic
| TQ Condition | Generated Visit Type |
|--------------|---------------------|
| WWTP Upgrade | Follow-up Visit |
| Industrial/Oil & Gas/Slaughterhouse | Technical Survey |
| Sample Collection Required | Initial Assessment |
| Other Cases | Technical Survey |

### Priority Calculation
| Factor | Points | Examples |
|--------|--------|----------|
| Capacity >1000 m³/day | +2 | Large industrial plants |
| Capacity >500 m³/day | +1 | Medium facilities |
| Industrial/Oil & Gas/Slaughterhouse | +2 | Complex wastewater types |
| Special Case | +3 | Custom requirements |
| Sample Collection Required | +1 | Water quality testing needed |
| Site Visit Required | +1 | Physical site assessment |

**Priority Levels:**
- **Urgent**: 4+ points
- **High**: 2-3 points  
- **Medium**: 1 point
- **Low**: 0 points

### Equipment Lists by Generator Type

#### Basic Equipment (All Visits)
- Measuring tape, Camera, Notebook, Safety equipment

#### Sample Collection Equipment
- Water sampling bottles, pH meter, Turbidity meter, Temperature probe, Sample preservation chemicals

#### Generator-Specific Equipment
| Generator Type | Additional Equipment |
|----------------|---------------------|
| Industrial | Chemical test strips, Conductivity meter |
| Oil & Gas | Oil detection kit, Hydrocarbon analyzer |
| Slaughterhouse | BOD test kit, Organic load analyzer |
| Special Case | Custom equipment based on requirements |

### Duration Estimation
| Factor | Time Addition |
|--------|---------------|
| Base Duration | 2 hours |
| Sample Collection | +1 hour |
| Industrial/Oil & Gas/Slaughterhouse | +1 hour |
| Special Case | +2 hours |
| Multiple Streams | +0.5 hours per stream |
| Large Capacity (>1000 m³/day) | +1 hour |
| Site Survey Required | +1 hour |

**Examples:**
- Simple domestic: 2-3 hours
- Industrial with samples: 4-5 hours
- Special case with 3 streams: 6-8 hours

## Field Mapping

### TQ → SVR Field Mapping
| TQ Field | SVR Field | Transformation |
|----------|-----------|----------------|
| `lead` | `lead` | Direct copy |
| `opportunity` | `opportunity` | Direct copy |
| `wastewater_generator_type` | `visit_purpose` | Context in purpose |
| `capacity` | `special_requirements` | Capacity details |
| `the_available_footprint_dedicated_for_stp_in_sm` | `special_requirements` | Footprint details |
| `location_of_the_wwtp_needed` | `special_requirements` | Location details |
| `sample_collection_required` | `equipment_needed` | Sample equipment added |
| `number_of_streams` | `special_requirements` | Multiple streams info |

## External Site Integration

### Sync Process
1. **Manual Trigger**: User clicks "Sync to External Site"
2. **API Call**: System calls external site API
3. **SVR Creation**: External SVR created with same data
4. **PDF Attachment**: TQ PDF automatically attached
5. **Status Update**: Local SVR marked as "Synced"

### Sync Status Fields
- `external_request_name`: Name of external SVR
- `external_request_url`: Direct link to external SVR
- `external_sync_status`: Pending/Synced/Failed
- `external_sync_error`: Error details if failed

## Troubleshooting

### Common Issues
| Issue | Cause | Solution |
|-------|-------|----------|
| Button not visible | TQ not submitted | Submit TQ first |
| Creation error | Missing required fields | Complete TQ fields |
| Sync failed | API credentials wrong | Check External Site Settings |
| Fields empty | TQ data insufficient | Verify TQ completion |

### Error Messages
- `"Technical Questionnaire must be submitted"` → Submit TQ first
- `"Not allowed to change Local Site Visit Request"` → Use sync button
- `"No external site settings configured"` → Setup External Site Settings
- `"Connection failed"` → Check API credentials

## Best Practices

### TQ Preparation
- ✅ Complete all required fields
- ✅ Provide detailed generator type information
- ✅ Include accurate capacity and footprint data
- ✅ Specify sample collection requirements
- ✅ Document special conditions

### SVR Review
- ✅ Verify auto-populated fields
- ✅ Add missing information
- ✅ Confirm equipment list completeness
- ✅ Validate duration estimate
- ✅ Check contact information

### External Sync
- ✅ Test external site connection first
- ✅ Verify API credentials
- ✅ Review sync status after operation
- ✅ Check external SVR creation

## Workflow Summary

```
TQ Creation → TQ Submission → SVR Generation → SVR Review → 
SVR Submission → External Sync (Optional) → Site Visit Execution
```

---

*Quick Reference Guide - Version 1.0*
*For detailed information, see the complete User Guide*
