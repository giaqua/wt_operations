# Site Visit

## Purpose

The Site Visit document captures the actual on-site technical assessment conducted by technical personnel. It includes site conditions, existing equipment inventory, technical measurements, and recommendations based on the site visit findings.

## When to Use

- **Technical Assessments**: Document on-site technical assessments
- **Data Collection**: Record site visit findings and measurements
- **Equipment Inventory**: Document existing equipment and infrastructure
- **Recommendations**: Provide technical recommendations based on site findings

## Status & Workflow

### Document States
- **Draft (0)**: Visit report being prepared
- **Submitted (1)**: Visit report completed and submitted
- **Cancelled (2)**: Visit report cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete visit report and submit
- **Submitted → Cancelled**: Cancel submitted visit report
- **Cancelled → Draft**: Restore cancelled visit report

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Site Visit Request | `site_visit_request` | Link | Link to Site Visit Request |
| Visit Date | `visit_date` | Date | Actual visit date |
| Visit Status | `visit_status` | Select | Visit status (Scheduled, In Progress, Completed, Cancelled) |
| Visit Type | `visit_type` | Select | Type of visit |
| Visit Purpose | `visit_purpose` | Data | Purpose of visit |
| Special Requirements | `special_requirements` | Small Text | Special requirements |
| Equipment Needed | `equipment_needed` | Small Text | Required equipment |
| Estimated Duration | `estimated_duration` | Data | Estimated visit duration |
| Follow-up Required | `follow_up_required` | Check | Follow-up required flag |
| Site Conditions | `site_conditions` | Small Text | Site condition assessment |
| Existing Equipment | `existing_equipment` | Small Text | Existing equipment inventory |
| Access and Utilities | `access_utilities` | Small Text | Access and utility assessment |
| Environmental Factors | `environmental_factors` | Small Text | Environmental factors |
| Safety Considerations | `safety_considerations` | Small Text | Safety considerations |
| Recommendations | `recommendations` | Small Text | Technical recommendations |
| Visit Summary | `visit_summary` | Text Editor | Visit summary |
| Risk Level | `risk_level` | Select | Risk level assessment |
| Compliance Status | `compliance_status` | Select | Compliance status |
| Next Steps | `next_steps` | Small Text | Next steps |
| Follow-up Date | `follow_up_date` | Date | Follow-up date |
| Follow-up Required | `follow_up_required` | Check | Follow-up required flag |

## Child Tables & Relations

### Site Visit Tracking Table
- **Purpose**: Track multiple visits for the same request
- **Fields**: Visit Date, Status, Notes, Completed By

## Actions & Automations

### Auto-Fill Functions
- **From STP**: Auto-populate from Technical Questionnaire
- **From SVR**: Auto-populate from Site Visit Request
- **Lead Details**: Auto-populate from linked Lead
- **Contact Details**: Auto-populate contact information

### Custom Buttons
- **Auto-fill from STP**: Populate data from Technical Questionnaire
- **Auto-fill from SVR**: Populate data from Site Visit Request
- **Get Lead Details**: Get lead information
- **Auto-fill Contact Details**: Populate contact details
- **Calculate Risk Level**: Calculate risk level
- **Generate Visit Summary**: Generate visit summary

### Client Scripts
- **File**: `site_visit.js`
- **Functions**:
  - `site_visit_request`: Auto-fill from SVR
  - `visit_date`: Validate visit date
  - `visit_status`: Update status
  - `on_submit`: Update related documents

### Server Methods
- **File**: `site_visit.py`
- **Methods**:
  - `get_stp_details`: Get Technical Questionnaire details
  - `auto_fill_from_stp`: Auto-populate from Technical Questionnaire
  - `get_lead_details`: Get lead information
  - `auto_fill_contact_details`: Auto-populate contact details
  - `calculate_risk_level`: Calculate risk level
  - `generate_visit_summary`: Generate visit summary
  - `auto_fill_from_svr`: Auto-populate from Site Visit Request

## Permissions & Roles

| Role | Create | Read | Update | Delete | Submit |
|------|--------|------|--------|--------|--------|
| System Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Site Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Technician | ✓ | ✓ | ✓ | ✓ | ✓ |
| Account Manager | - | ✓ | - | - | - |

## Data Validation

### Required Fields
- Site Visit Request must be linked
- Visit date must be set
- Visit status must be selected
- Visit type must be selected
- Visit purpose must be specified

### Business Rules
- Visit date must be realistic
- Risk level must be calculated based on findings
- Follow-up date must be in the future if follow-up required
- Visit status must be updated appropriately

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Date validation**: Ensure visit date is realistic

## Common Tasks

### Creating a Site Visit
1. Navigate to WT Operations → Site Visit
2. Click "New" to create new visit
3. Link to Site Visit Request
4. Use "Auto-fill from SVR" button
5. Set visit date and status
6. Complete site assessment
7. Document findings
8. Add recommendations
9. Review and submit

### Auto-Filling from Site Visit Request
1. Select Site Visit Request
2. Click "Auto-fill from SVR" button
3. System automatically populates:
   - Visit details
   - Special requirements
   - Equipment needed
   - Visit purpose
4. Review and customize as needed

### Auto-Filling from Technical Questionnaire
1. Link to Technical Questionnaire
2. Click "Auto-fill from STP" button
3. System automatically populates:
   - Project details
   - Technical requirements
   - Site conditions
   - Equipment requirements
4. Review and customize as needed

### Conducting Site Assessment
1. **Site Conditions**:
   - Document site layout
   - Assess accessibility
   - Note environmental factors
   - Record safety considerations
2. **Equipment Inventory**:
   - List existing equipment
   - Assess condition
   - Note capacity and specifications
   - Identify maintenance needs
3. **Technical Measurements**:
   - Record flow rates
   - Measure dimensions
   - Assess utilities
   - Document constraints
4. **Recommendations**:
   - Provide technical recommendations
   - Identify risks and mitigation
   - Suggest improvements
   - Define next steps

### Risk Assessment
1. Click "Calculate Risk Level" button
2. System calculates risk based on:
   - Site conditions
   - Environmental factors
   - Safety considerations
   - Technical complexity
3. Review risk assessment
4. Add mitigation strategies

## Site Assessment Checklist

### Pre-Visit Preparation
- [ ] Review Technical Questionnaire
- [ ] Prepare equipment checklist
- [ ] Coordinate with customer
- [ ] Plan visit logistics
- [ ] Prepare safety equipment

### Site Assessment
- [ ] Document site conditions
- [ ] Inventory existing equipment
- [ ] Assess access and utilities
- [ ] Record environmental factors
- [ ] Note safety considerations
- [ ] Take photographs
- [ ] Collect samples (if needed)

### Post-Visit Activities
- [ ] Complete visit report
- [ ] Calculate risk level
- [ ] Generate recommendations
- [ ] Define next steps
- [ ] Schedule follow-up (if needed)
- [ ] Update related documents

## Tips & Pitfalls

### Best Practices
- **Prepare Thoroughly**: Review all project documents before visit
- **Document Everything**: Record all findings and observations
- **Take Photos**: Document site conditions with photographs
- **Safety First**: Always prioritize safety considerations
- **Follow Up**: Schedule follow-up activities as needed

### Common Issues
- **Missing Auto-Fill**: Ensure Site Visit Request is linked
- **Incomplete Assessment**: Ensure all sections are completed
- **Risk Assessment**: Calculate risk level based on findings
- **Follow-up Planning**: Plan follow-up activities appropriately

### Troubleshooting
- **Auto-Fill Not Working**: Check Site Visit Request linkage
- **Risk Calculation Errors**: Review risk assessment criteria
- **Date Validation Errors**: Ensure visit date is realistic
- **Status Update Issues**: Update visit status appropriately
