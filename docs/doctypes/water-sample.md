# Water Sample

## Purpose

The Water Sample document manages the collection, handling, and analysis of water samples for WWTP projects. It tracks sample collection details, chain of custody, and links to laboratory test results.

## When to Use

- **Water Quality Analysis**: Collect samples for laboratory analysis
- **Compliance Testing**: Verify compliance with regulatory standards
- **Process Monitoring**: Monitor treatment process performance
- **Design Basis**: Provide data for treatment system design

## Status & Workflow

### Document States
- **Draft (0)**: Sample record being prepared
- **Submitted (1)**: Sample record completed and submitted
- **Cancelled (2)**: Sample record cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete sample record and submit
- **Submitted → Cancelled**: Cancel submitted sample record
- **Cancelled → Draft**: Restore cancelled sample record

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Site Visit | `site_visit` | Link | Link to Site Visit |
| Sample Date | `sample_date` | Date | Sample collection date |
| Sample Type | `sample_type` | Select | Type of sample (Influent, Effluent, Process) |
| Collection Location | `collection_location` | Data | Sample collection location |
| Collection Method | `collection_method` | Data | Collection method used |
| Sample Volume | `sample_volume` | Data | Sample volume collected |
| Preservation Requirements | `preservation_requirements` | Small Text | Preservation requirements |
| Chain of Custody | `chain_of_custody` | Small Text | Chain of custody information |
| Sample Tag | `sample_tag` | Data | Unique sample identifier |
| Collected By | `collected_by` | Link | Person who collected sample |
| Lab Test Result | `lab_test_result` | Link | Link to Lab Test Result |
| Compliance Status | `compliance_status` | Select | Compliance status |
| Test Parameters | `test_parameters` | Small Text | Parameters to be tested |
| Special Instructions | `special_instructions` | Small Text | Special testing instructions |
| Sample Condition | `sample_condition` | Select | Sample condition (Good, Poor, Contaminated) |
| Storage Location | `storage_location` | Data | Sample storage location |
| Storage Temperature | `storage_temperature` | Data | Storage temperature |
| Expiry Date | `expiry_date` | Date | Sample expiry date |
| Disposal Method | `disposal_method` | Data | Sample disposal method |
| Notes | `notes` | Small Text | Additional notes |

## Child Tables & Relations

### Samples Table
- **Purpose**: Track multiple samples in one collection
- **Fields**: Sample Tag, Sample Type, Collection Location, Volume, Notes

## Actions & Automations

### Auto-Fill Functions
- **From STP**: Auto-populate from Technical Questionnaire
- **From Site Visit**: Auto-populate from Site Visit
- **Sample Summary**: Generate sample summary

### Custom Buttons
- **Auto-fill from STP**: Populate data from Technical Questionnaire
- **Auto-fill from Site Visit**: Populate data from Site Visit
- **Get STP Details**: Get Technical Questionnaire details
- **Calculate Compliance**: Calculate compliance status
- **Get Sample Summary**: Generate sample summary

### Client Scripts
- **File**: `water_sample.js`
- **Functions**:
  - `site_visit`: Auto-fill from Site Visit
  - `sample_date`: Validate sample date
  - `sample_type`: Update collection requirements
  - `on_submit`: Update related documents

### Server Methods
- **File**: `water_sample.py`
- **Methods**:
  - `get_stp_details`: Get Technical Questionnaire details
  - `auto_fill_from_stp`: Auto-populate from Technical Questionnaire
  - `calculate_compliance`: Calculate compliance status
  - `get_sample_summary`: Generate sample summary

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
- Site Visit must be linked
- Sample date must be set
- Sample type must be selected
- Collection location must be specified
- Sample tag must be unique

### Business Rules
- Sample date must be realistic
- Sample tag must be unique across all samples
- Collection method must be appropriate for sample type
- Preservation requirements must be specified
- Chain of custody must be maintained

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Uniqueness**: Ensure sample tag uniqueness

## Common Tasks

### Creating a Water Sample
1. Navigate to WT Operations → Water Sample
2. Click "New" to create new sample
3. Link to Site Visit
4. Use "Auto-fill from Site Visit" button
5. Set sample date and type
6. Specify collection details
7. Add preservation requirements
8. Complete chain of custody
9. Review and submit

### Auto-Filling from Site Visit
1. Select Site Visit
2. Click "Auto-fill from Site Visit" button
3. System automatically populates:
   - Visit details
   - Collection requirements
   - Special instructions
   - Test parameters
4. Review and customize as needed

### Auto-Filling from Technical Questionnaire
1. Link to Technical Questionnaire
2. Click "Auto-fill from STP" button
3. System automatically populates:
   - Project details
   - Sample requirements
   - Test parameters
   - Compliance criteria
4. Review and customize as needed

### Sample Collection Process
1. **Preparation**:
   - Review sample requirements
   - Prepare collection equipment
   - Check preservation requirements
   - Plan collection logistics
2. **Collection**:
   - Follow proper collection procedures
   - Maintain chain of custody
   - Record collection details
   - Preserve samples appropriately
3. **Documentation**:
   - Complete sample record
   - Document collection details
   - Record preservation requirements
   - Maintain chain of custody
4. **Transportation**:
   - Ensure proper transportation
   - Maintain sample integrity
   - Follow safety procedures
   - Document transportation

### Chain of Custody Management
1. **Collection**: Record collector information
2. **Transportation**: Document transportation details
3. **Laboratory**: Record laboratory receipt
4. **Analysis**: Track analysis progress
5. **Disposal**: Document disposal method

## Sample Types

### Influent Sample
- **Purpose**: Analyze raw wastewater characteristics
- **Collection**: Before treatment process
- **Parameters**: BOD, COD, TSS, pH, nutrients
- **Frequency**: Daily or as required

### Effluent Sample
- **Purpose**: Verify treatment performance
- **Collection**: After treatment process
- **Parameters**: BOD, COD, TSS, pH, nutrients, pathogens
- **Frequency**: Daily or as required

### Process Sample
- **Purpose**: Monitor treatment process
- **Collection**: At various process stages
- **Parameters**: Process-specific parameters
- **Frequency**: As needed for process control

## Compliance Monitoring

### Regulatory Requirements
- **Discharge Standards**: Meet regulatory discharge limits
- **Monitoring Frequency**: Follow regulatory monitoring requirements
- **Reporting**: Submit compliance reports
- **Documentation**: Maintain compliance records

### Compliance Status
- **Compliant**: Meets all regulatory requirements
- **Non-Compliant**: Exceeds regulatory limits
- **Partially Compliant**: Meets some requirements
- **Under Review**: Compliance status being reviewed

## Tips & Pitfalls

### Best Practices
- **Follow Procedures**: Use standardized collection procedures
- **Maintain Chain of Custody**: Document all sample handling
- **Preserve Samples**: Follow preservation requirements
- **Document Everything**: Record all collection details
- **Safety First**: Follow safety procedures

### Common Issues
- **Missing Auto-Fill**: Ensure Site Visit is linked
- **Chain of Custody**: Maintain proper chain of custody
- **Sample Integrity**: Ensure sample integrity
- **Compliance**: Monitor compliance status

### Troubleshooting
- **Auto-Fill Not Working**: Check Site Visit linkage
- **Sample Tag Duplicates**: Ensure unique sample tags
- **Compliance Issues**: Review compliance criteria
- **Chain of Custody**: Verify chain of custody documentation
