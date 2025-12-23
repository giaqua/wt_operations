# Lab Test Result

## Purpose

The Lab Test Result document manages laboratory analysis results of water samples collected during site visits. It provides detailed water quality analysis data and compliance assessment for WWTP projects.

## When to Use

- **Water Quality Analysis**: Document laboratory analysis results
- **Compliance Verification**: Verify compliance with regulatory standards
- **Design Validation**: Validate treatment system design assumptions
- **Process Optimization**: Optimize treatment processes based on results

## Status & Workflow

### Document States
- **Draft (0)**: Test result being prepared
- **Submitted (1)**: Test result completed and submitted
- **Cancelled (2)**: Test result cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete test result and submit
- **Submitted → Cancelled**: Cancel submitted test result
- **Cancelled → Draft**: Restore cancelled test result

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Sample Tag | `sample_tag` | Data | Required - Unique sample identifier |
| Site Visit | `site_visit` | Link | Link to Site Visit |
| Site Visit Date | `site_visit_date` | Date | Auto-filled from Site Visit |
| Date Sample Received | `date_sample_received` | Date | Date sample received by lab |
| Report Date | `report_date` | Date | Test report date |
| Test By | `test_by` | Link | Person who conducted tests |
| Approved By | `approved_by` | Link | Person who approved results |
| Test Method | `test_method` | Data | Test method used |
| Quality Control | `quality_control` | Small Text | Quality control measures |
| Test Report | `test_report` | Data | Test report reference |
| Compliance Status | `compliance_status` | Select | Compliance status |
| Test Summary | `test_summary` | Text Editor | Test summary |
| Recommendations | `recommendations` | Small Text | Recommendations based on results |
| Follow-up Required | `follow_up_required` | Check | Follow-up required flag |
| Follow-up Date | `follow_up_date` | Date | Follow-up date |
| Notes | `notes` | Small Text | Additional notes |

## Child Tables & Relations

### Lab Test Results Parameters
- **Purpose**: Detailed test parameter results
- **Fields**: Parameter, Inlet, Outlet, UOM

## Actions & Automations

### Auto-Fill Functions
- **From Site Visit**: Auto-populate from Site Visit
- **From Water Sample**: Auto-populate from Water Sample
- **Test Summary**: Generate test summary

### Custom Buttons
- **Auto-fill from Site Visit**: Populate data from Site Visit
- **Auto-fill from Water Sample**: Populate data from Water Sample
- **Generate Test Summary**: Generate test summary
- **Calculate Compliance**: Calculate compliance status

### Client Scripts
- **File**: `lab_test_result.js`
- **Functions**:
  - `site_visit`: Auto-fill from Site Visit
  - `report_date`: Validate report date
  - `on_submit`: Update related documents

### Server Methods
- **File**: `lab_test_result.py`
- **Methods**:
  - `auto_fill_from_site_visit`: Auto-populate from Site Visit
  - `auto_fill_from_water_sample`: Auto-populate from Water Sample
  - `generate_test_summary`: Generate test summary
  - `calculate_compliance`: Calculate compliance status

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
- Sample tag must be unique
- Site Visit must be linked
- Report date must be set
- Test by must be specified
- Approved by must be specified

### Business Rules
- Sample tag must be unique across all test results
- Report date must be realistic
- Test parameters must be specified
- Compliance status must be calculated
- Quality control measures must be documented

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Uniqueness**: Ensure sample tag uniqueness

## Common Tasks

### Creating a Lab Test Result
1. Navigate to WT Operations → Lab Test Result
2. Click "New" to create new test result
3. Enter unique sample tag
4. Link to Site Visit
5. Use "Auto-fill from Site Visit" button
6. Set test dates
7. Enter test parameters
8. Calculate compliance status
9. Generate test summary
10. Review and submit

### Auto-Filling from Site Visit
1. Select Site Visit
2. Click "Auto-fill from Site Visit" button
3. System automatically populates:
   - Visit details
   - Sample information
   - Test requirements
   - Compliance criteria
4. Review and customize as needed

### Auto-Filling from Water Sample
1. Link to Water Sample
2. Click "Auto-fill from Water Sample" button
3. System automatically populates:
   - Sample details
   - Collection information
   - Test parameters
   - Preservation requirements
4. Review and customize as needed

### Entering Test Parameters
1. **Physical Parameters**:
   - pH, Temperature, Turbidity
   - Total Suspended Solids (TSS)
   - Total Dissolved Solids (TDS)
2. **Chemical Parameters**:
   - Biochemical Oxygen Demand (BOD5)
   - Chemical Oxygen Demand (COD)
   - Oil and Grease
   - Nutrients (Nitrogen, Phosphorus)
   - Heavy metals
3. **Biological Parameters**:
   - E. coli, Total Coliform
   - Helminth eggs
   - Pathogens

### Compliance Assessment
1. **Compare Results**: Compare test results with regulatory limits
2. **Calculate Compliance**: Determine compliance status
3. **Identify Issues**: Identify non-compliance issues
4. **Recommend Actions**: Recommend corrective actions
5. **Document Findings**: Document compliance findings

## Test Parameters

### Physical Parameters
- **pH**: Acidity/alkalinity measurement
- **Temperature**: Water temperature
- **Turbidity**: Water clarity measurement
- **TSS**: Total suspended solids
- **TDS**: Total dissolved solids

### Chemical Parameters
- **BOD5**: Biochemical oxygen demand (5-day)
- **COD**: Chemical oxygen demand
- **Oil & Grease**: Hydrocarbon content
- **Nitrogen**: Total nitrogen content
- **Phosphorus**: Total phosphorus content
- **Heavy Metals**: Metal concentrations

### Biological Parameters
- **E. coli**: Fecal coliform bacteria
- **Total Coliform**: Total coliform bacteria
- **Helminth Eggs**: Parasitic worm eggs
- **Pathogens**: Disease-causing organisms

## Compliance Standards

### Regulatory Limits
- **Discharge Standards**: Regulatory discharge limits
- **Reuse Standards**: Water reuse standards
- **Irrigation Standards**: Irrigation water standards
- **Environmental Standards**: Environmental protection standards

### Compliance Categories
- **Compliant**: Meets all regulatory requirements
- **Non-Compliant**: Exceeds regulatory limits
- **Partially Compliant**: Meets some requirements
- **Under Review**: Compliance status being reviewed

## Quality Control

### Laboratory Quality
- **Accredited Laboratory**: Use accredited laboratory
- **Standard Methods**: Follow standard test methods
- **Quality Control**: Implement quality control measures
- **Proficiency Testing**: Participate in proficiency testing
- **Audit Trail**: Maintain audit trail

### Sample Integrity
- **Chain of Custody**: Maintain chain of custody
- **Sample Preservation**: Follow preservation requirements
- **Storage Conditions**: Maintain proper storage conditions
- **Transportation**: Ensure proper transportation

## Tips & Pitfalls

### Best Practices
- **Use Accredited Labs**: Use accredited laboratories
- **Follow Standards**: Follow standard test methods
- **Quality Control**: Implement quality control measures
- **Document Everything**: Record all test details
- **Verify Results**: Verify test results

### Common Issues
- **Missing Auto-Fill**: Ensure Site Visit is linked
- **Sample Tag Duplicates**: Ensure unique sample tags
- **Compliance Issues**: Review compliance criteria
- **Quality Control**: Implement quality control measures

### Troubleshooting
- **Auto-Fill Not Working**: Check Site Visit linkage
- **Sample Tag Duplicates**: Ensure unique sample tags
- **Compliance Issues**: Review compliance criteria
- **Quality Control**: Verify quality control measures
