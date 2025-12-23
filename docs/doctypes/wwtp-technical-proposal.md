# WWTP Technical Proposal

## Purpose

The WWTP Technical Proposal is a comprehensive technical solution document that presents the recommended treatment technology, process design, and implementation plan based on the Technical Questionnaire assessment and site visit findings.

## When to Use

- **Technical Solutions**: Present technical solutions to customers
- **Design Basis**: Foundation for detailed engineering design
- **Cost Estimation**: Basis for cost estimation and budgeting
- **Implementation Planning**: Guide for project implementation

## Status & Workflow

### Document States
- **Draft (0)**: Proposal being prepared
- **Submitted (1)**: Proposal completed and submitted
- **Cancelled (2)**: Proposal cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete proposal and submit
- **Submitted → Cancelled**: Cancel submitted proposal
- **Cancelled → Draft**: Restore cancelled proposal

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Lead | `lead` | Link | Link to Lead |
| Opportunity | `opportunity` | Link | Link to Opportunity |
| Technical Questionnaire | `wwtp_technical_questionnaire` | Link | Link to Technical Questionnaire |
| Site Visit | `site_visit` | Link | Link to Site Visit |
| Water Sample | `water_sample` | Link | Link to Water Sample |
| Proposal Date | `proposal_date` | Date | Proposal issue date |
| Valid Until | `valid_until` | Date | Proposal validity date |
| Prepared By | `prepared_by` | Link | User who prepared proposal |
| Technical Manager | `technical_manager` | Link | Technical manager |
| Project Title | `project_title` | Data | Project title |
| Project Description | `project_description` | Text Editor | Project description |
| Wastewater Generator Type | `wastewater_generator_type` | Data | Type of wastewater source |
| Design Capacity | `design_capacity` | Float | Design treatment capacity |
| Current Capacity | `current_capacity` | Float | Current treatment capacity |
| Treatment Technology | `treatment_technology` | Data | Recommended treatment technology |
| Process Description | `process_description` | Text Editor | Process description |
| Treatment Stages | `treatment_stages` | Text Editor | Treatment stages |
| Civil Requirements | `civil_requirements` | Text Editor | Civil requirements |
| Site Preparation Needs | `site_preparation_needs` | Text Editor | Site preparation needs |
| Utility Connections | `utility_connections` | Text Editor | Utility connections |
| Operation Hours | `operation_hours` | Data | Operation hours |
| Maintenance Requirements | `maintenance_requirements` | Text Editor | Maintenance requirements |
| Chemical Consumption | `chemical_consumption` | Text Editor | Chemical consumption |
| Energy Consumption | `energy_consumption` | Text Editor | Energy consumption |
| Environmental Permits Required | `environmental_permits_required` | Text Editor | Required permits |
| Discharge Permit Status | `discharge_permit_status` | Select | Permit status |
| Environmental Monitoring | `environmental_monitoring` | Text Editor | Monitoring requirements |
| Equipment Cost | `equipment_cost` | Currency | Equipment cost |
| Civil Works Cost | `civil_works_cost` | Currency | Civil works cost |
| Electrical Cost | `electrical_cost` | Currency | Electrical cost |
| Total Project Cost | `total_project_cost` | Currency | Total project cost |
| Design Period | `design_period` | Int | Design period (weeks) |
| Procurement Period | `procurement_period` | Int | Procurement period (weeks) |
| Construction Period | `construction_period` | Int | Construction period (weeks) |
| Commissioning Period | `commissioning_period` | Int | Commissioning period (weeks) |
| Total Implementation Time | `total_implementation_time` | Int | Total implementation time (weeks) |
| Technical Risks | `technical_risks` | Text Editor | Technical risks |
| Environmental Risks | `environmental_risks` | Text Editor | Environmental risks |
| Mitigation Strategies | `mitigation_strategies` | Text Editor | Risk mitigation strategies |
| Technical Recommendations | `technical_recommendations` | Text Editor | Technical recommendations |
| Next Steps | `next_steps` | Text Editor | Next steps |
| Follow-up Required | `follow_up_required` | Check | Follow-up required flag |

## Child Tables & Relations

### Roles and Responsibilities Table
- **Purpose**: Define roles and responsibilities for project scope
- **Auto-population**: From Technical Questionnaire
- **Fields**: Scope of Work, Responsible, Not Required, Remarks

### Technical Specifications Table
- **Purpose**: Detailed technical specifications
- **Fields**: Parameter, Value, Unit, Notes

### Equipment Details Table
- **Purpose**: Equipment specifications and details
- **Fields**: Equipment, Specification, Quantity, Unit, Notes

### Effluent Quality Table
- **Purpose**: Effluent quality parameters and limits
- **Fields**: Parameter, Limit, Unit, Notes

## Actions & Automations

### Auto-Fill Functions
- **From Technical Questionnaire**: Auto-populate project details
- **From Site Visit**: Auto-populate site conditions
- **From Water Sample**: Auto-populate water quality data
- **Roles and Responsibilities**: Auto-populate from Technical Questionnaire

### Custom Buttons
- **Auto-fill from TQ**: Populate data from Technical Questionnaire
- **Auto-fill from Site Visit**: Populate data from Site Visit
- **Auto-fill from Water Sample**: Populate data from Water Sample
- **Sync to External Site**: Sync to external site
- **Generate Proposal Summary**: Generate proposal summary

### Client Scripts
- **File**: `wwtp_technical_proposal.js`
- **Functions**:
  - `wwtp_technical_questionnaire`: Auto-fill from TQ
  - `site_visit`: Auto-fill from Site Visit
  - `water_sample`: Auto-fill from Water Sample
  - `on_submit`: Trigger cross-site sync

### Server Methods
- **File**: `wwtp_technical_proposal.py`
- **Methods**:
  - `auto_fill_from_tq`: Auto-populate from Technical Questionnaire
  - `populate_roles_and_responsibilities_from_tq`: Populate roles table
  - `auto_fill_from_site_visit`: Auto-populate from Site Visit
  - `auto_fill_from_water_sample`: Auto-populate from Water Sample
  - `sync_to_external_site`: Sync to external site
  - `generate_proposal_summary`: Generate proposal summary
  - `validate_proposal_completeness`: Validate proposal completeness

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
- Technical Questionnaire must be linked
- Proposal date must be set
- Valid until date must be set
- Project title must be specified
- Treatment technology must be selected

### Business Rules
- Valid until date must be after proposal date
- Total implementation time must be sum of individual periods
- Cost fields must be positive numbers
- Capacity fields must be positive numbers

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Cross-field**: Validation between related fields

## Common Tasks

### Creating a Technical Proposal
1. Navigate to WT Operations → WWTP Technical Proposal
2. Click "New" to create new proposal
3. Select Lead from dropdown
4. Select Opportunity if available
5. Link to Technical Questionnaire
6. Use "Auto-fill from TQ" button
7. Complete technical specifications
8. Add equipment details
9. Define implementation timeline
10. Calculate costs
11. Review and submit

### Auto-Filling from Technical Questionnaire
1. Select Technical Questionnaire
2. Click "Auto-fill from TQ" button
3. System automatically populates:
   - Project details
   - Technical specifications
   - Site conditions
   - Roles and responsibilities
4. Review and customize as needed

### Auto-Filling from Site Visit
1. Link to Site Visit
2. Click "Auto-fill from Site Visit" button
3. System automatically populates:
   - Site conditions
   - Existing equipment
   - Access and utilities
   - Environmental factors
4. Review and customize as needed

### Auto-Filling from Water Sample
1. Link to Water Sample
2. Click "Auto-fill from Water Sample" button
3. System automatically populates:
   - Water quality data
   - Compliance status
   - Treatment requirements
4. Review and customize as needed

### Cross-Site Sync
1. Complete Technical Proposal
2. Submit the proposal
3. Use "Sync to External Site" button
4. Monitor sync status
5. Handle any sync errors

## Tips & Pitfalls

### Best Practices
- **Use Auto-Fill**: Leverage auto-fill functions for consistency
- **Complete All Sections**: Ensure all sections are completed
- **Review Calculations**: Verify all calculations and costs
- **Add Comments**: Add comments for special requirements
- **Validate Data**: Use validation functions before submitting

### Common Issues
- **Missing Auto-Fill**: Ensure required links are set
- **Validation Errors**: Check required fields and business rules
- **Cost Calculations**: Verify cost calculations
- **Sync Failures**: Check External Site Settings for cross-site operations

### Troubleshooting
- **Auto-Fill Not Working**: Check Technical Questionnaire linkage
- **Cost Calculation Errors**: Verify cost field values
- **Sync Issues**: Test External Site Settings connection
- **Validation Failures**: Review required fields and business rules
