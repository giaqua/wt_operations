# WWTP Technical Questionnaire

## Purpose

The WWTP Technical Questionnaire is a comprehensive assessment document that captures project requirements, site conditions, and technical specifications for wastewater treatment plant projects. It serves as the foundation for all subsequent technical and commercial activities.

## When to Use

- **New Projects**: Initial technical assessment for new WWTP projects
- **Upgrades**: Assessment of existing facilities for upgrades
- **Feasibility Studies**: Preliminary technical evaluation
- **Regulatory Compliance**: Documentation for regulatory requirements

## Status & Workflow

### Document States
- **Draft (0)**: Document being prepared
- **Submitted (1)**: Document completed and submitted
- **Cancelled (2)**: Document cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete all required fields and submit
- **Submitted → Cancelled**: Cancel submitted document (System Manager only)
- **Cancelled → Draft**: Restore cancelled document (System Manager only)

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Lead | `lead` | Link | Required - Link to Lead |
| Opportunity | `opportunity` | Link | Optional - Link to Opportunity |
| Date | `date` | Date | Required - Assessment date |
| By | `by` | Link | User who created the assessment |
| Wastewater Generator Type | `wastewater_generator_type` | Select | Required - Type of wastewater source |
| Capacity | `capacity` | Int | Required - Treatment capacity (m³/day) |
| Available Footprint | `the_available_footprint_dedicated_for_stp_in_sm` | Data | Available space for WWTP |
| Location | `location_of_the_wwtp_needed` | Data | WWTP location requirements |
| Available Equipment | `available_equipment__tanks_pumpsect` | Data | Existing equipment inventory |
| Site Conditions | `design_of_the_site_condition` | Small Text | Site condition assessment |
| Daily Flow | `daily_flow` | Data | Expected daily flow rate |
| Operation Hours | `operation_hours` | Data | Daily operation hours |
| Average Hourly Flow | `average_hourly_flow` | Data | Average hourly flow rate |
| Peak Factor | `peak_factor` | Data | Peak flow factor |
| Peak Hours | `peak_hours` | Data | Peak flow hours |
| Min Flow | `min_flow` | Data | Minimum flow rate |
| Effluent Target Type | `please_pick_the_target_effluent_type` | Select | Target effluent quality type |
| Site Visit Required | `site_visit_required` | Check | Flag for site visit requirement |
| Sample Collection Required | `sample_collection_required` | Check | Flag for water sampling |

## Child Tables & Relations

### TQ Influent Stream
- **Purpose**: Define influent streams and their characteristics
- **Auto-population**: Based on `number_of_streams` field
- **Fields**: Parameter, Value, Unit, Notes

### TQ Roles and Responsibilities
- **Purpose**: Define roles and responsibilities for project scope
- **Auto-population**: From Scope of Work master data
- **Fields**: Scope of Work, Responsible, Not Required, Remarks

## Actions & Automations

### Auto-Fill Functions
- **Effluent Parameters**: Auto-populate based on `please_pick_the_target_effluent_type`
- **Roles and Responsibilities**: Auto-populate from Scope of Work master data
- **Influent Streams**: Auto-create rows based on `number_of_streams`

### Custom Buttons
- **Create Site Visit Request**: Create Site Visit Request from TQ
- **Open Local SVR**: Open linked local Site Visit Request
- **Open External SVR**: Open external Site Visit Request
- **Refresh Effluent Parameters**: Re-populate effluent parameters

### Client Scripts
- **File**: `wwtp_technical_questionnaire.js`
- **Functions**:
  - `number_of_streams`: Update influent stream table
  - `please_pick_the_target_effluent_type`: Auto-populate effluent parameters
  - `before_save`: Validate table structure

### Server Methods
- **File**: `wwtp_technical_questionnaire.py`
- **Methods**:
  - `create_site_visit_request`: Create Site Visit Request
  - `populate_effluent_parameters`: Auto-populate effluent parameters

## Permissions & Roles

| Role | Create | Read | Update | Delete | Submit |
|------|--------|------|--------|--------|--------|
| System Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Site Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Technician | - | ✓ | - | - | - |
| Account Manager | - | ✓ | - | - | - |

## Data Validation

### Required Fields
- Lead must be selected
- Date must be set
- Wastewater generator type must be selected
- Capacity must be specified
- Effluent target type must be selected

### Business Rules
- Capacity must be positive number
- Number of streams must be non-negative
- Effluent parameters auto-populate based on target type
- Site visit and sample collection flags affect downstream processes

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Cross-field**: Validation between related fields

## Common Tasks

### Creating a New Technical Questionnaire
1. Navigate to WT Operations → WWTP Technical Questionnaire
2. Click "New" to create new document
3. Select Lead from dropdown
4. Select Opportunity if available
5. Set assessment date
6. Select wastewater generator type
7. Enter capacity requirements
8. Fill in site information
9. Select effluent target type (triggers auto-population)
10. Complete technical specifications
11. Review and submit

### Auto-Populating Effluent Parameters
1. Select effluent target type from dropdown
2. System automatically populates:
   - pH, TSS, BOD5, COD
   - Turbidity, Oil & Grease, TDS
   - Free Chlorine, E.coli, Wormies
3. Use "Refresh Effluent Parameters" button if needed

### Creating Site Visit Request
1. Complete Technical Questionnaire
2. Submit the document
3. Click "Create Site Visit Request" button
4. Review auto-populated information
5. Set visit date and priority
6. Submit Site Visit Request

### Managing Influent Streams
1. Set number of streams
2. System automatically creates stream rows
3. Fill in stream characteristics
4. Add notes and additional information

## Tips & Pitfalls

### Best Practices
- **Complete Required Fields**: Ensure all required fields are filled
- **Use Auto-Fill**: Leverage auto-population features for consistency
- **Link Documents**: Properly link Lead and Opportunity
- **Add Comments**: Add comments for special requirements
- **Review Before Submit**: Review all information before submitting

### Common Issues
- **Missing Auto-Fill**: Ensure required links are set
- **Validation Errors**: Check required fields and business rules
- **Permission Issues**: Verify user role assignments
- **Sync Failures**: Check External Site Settings for cross-site operations

### Troubleshooting
- **Effluent Parameters Not Populating**: Check effluent target type selection
- **Site Visit Request Creation Fails**: Ensure TQ is submitted
- **Influent Streams Not Updating**: Check number of streams field
- **Cross-Site Sync Issues**: Verify External Site Settings configuration
