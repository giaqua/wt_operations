# WWTP Technical Proposal

The WWTP Technical Proposal doctype is designed to gather all findings from the Technical Questionnaire (TQ), Site Visit, and Water Sample documents to prepare a comprehensive technical proposal that can be sent to leads proposing the technical aspects of a proposed wastewater treatment plant.

## Purpose

This document serves as a comprehensive technical proposal that:
- Consolidates findings from TQ, Site Visit, and Water Sample documents
- Includes additional technical team research and analysis
- Provides specific details about treated wastewater quality
- Offers detailed technical specifications and equipment requirements
- Includes cost estimation and implementation timeline
- Can be synced from Site 2 to Site 1 for review and approval

## Key Features

### 1. **Auto-fill Functionality**
- **From TQ**: Automatically populates basic project information, lead details, and capacity data
- **From Site Visit**: Auto-fills site conditions, accessibility ratings, and environmental assessments
- **From Water Sample**: Populates water quality analysis and compliance status

### 2. **Comprehensive Data Collection**
- **Project Summary**: Title, description, generator type, capacity details
- **Technical Findings**: Site conditions, existing facility assessment, environmental impact
- **Water Quality Analysis**: Influent characteristics, effluent requirements, treatment challenges
- **Proposed Solution**: Treatment technology, process description, treatment stages
- **Technical Specifications**: Detailed specifications via child table
- **Equipment Details**: Complete equipment list with specifications via child table
- **Effluent Quality**: Guaranteed effluent quality parameters via child table
- **Civil Works**: Site preparation, utility connections, civil requirements
- **Operational Considerations**: Operation hours, maintenance, chemical/energy consumption
- **Environmental Compliance**: Permits, discharge status, monitoring requirements
- **Cost Estimation**: Equipment, civil works, electrical costs with automatic total calculation
- **Implementation Timeline**: Design, procurement, construction, commissioning periods
- **Risks and Mitigation**: Technical and environmental risks with mitigation strategies
- **Recommendations**: Technical recommendations and next steps

### 3. **Child Tables**

#### **WWTP Technical Specifications Table**
- Specification Type (Process, Equipment, Civil, Electrical, Environmental)
- Parameter name and value
- Unit of measurement
- Description

#### **WWTP Equipment Details Table**
- Equipment name and type
- Quantity and capacity
- Power consumption
- Manufacturer and model
- Description

#### **WWTP Effluent Quality Table**
- Parameter name
- Target and guaranteed values
- Test method and frequency
- Unit of measurement

### 4. **External Site Integration**
- **Sync to Site 1**: Send proposal from Site 2 to Site 1 for review
- **PDF Attachment**: Automatically generates and attaches proposal PDF
- **Status Tracking**: Track sync status and handle errors
- **External Links**: Direct links to external proposal documents

### 5. **Validation and Quality Control**
- **Completeness Validation**: Check for required fields before submission
- **Cost Calculation**: Automatic total cost calculation
- **Timeline Calculation**: Automatic implementation time calculation
- **Capacity Validation**: Ensure design capacity meets requirements
- **Date Validation**: Ensure valid dates and logical sequences

## Workflow

### 1. **Creation**
1. Create new WWTP Technical Proposal
2. Select related TQ, Site Visit, and Water Sample documents
3. Use auto-fill buttons to populate data from related documents
4. Complete additional technical research and analysis

### 2. **Data Population**
1. **Auto-fill from TQ**: Populates basic project information
2. **Auto-fill from Site Visit**: Populates site conditions and assessments
3. **Auto-fill from Water Sample**: Populates water quality data
4. **Manual Entry**: Complete technical specifications, equipment details, and recommendations

### 3. **Validation**
1. Use "Validate Proposal" button to check completeness
2. Review calculated totals and timelines
3. Ensure all required fields are completed

### 4. **Submission**
1. Submit the proposal for internal review
2. Use "Sync to External Site" to send to Site 1
3. Track sync status and handle any errors

## Field Descriptions

### **Basic Information**
- **Lead**: Customer lead (required)
- **Opportunity**: Related sales opportunity
- **WWTP Technical Questionnaire**: Source TQ document (required)
- **Site Visit**: Related site visit document
- **Water Sample**: Related water sample document
- **Proposal Date**: Date of proposal creation (required)
- **Valid Until**: Proposal validity date (required)
- **Prepared By**: User who prepared the proposal (required)
- **Technical Manager**: Technical manager for review

### **Project Summary**
- **Project Title**: Descriptive title for the project (required)
- **Project Description**: Detailed project description
- **Wastewater Generator Type**: Type of wastewater generator (auto-filled)
- **Design Capacity**: Proposed treatment capacity in m³/day (required)
- **Current Capacity**: Existing capacity (auto-filled)

### **Technical Findings**
- **Site Conditions Summary**: Overall site assessment
- **Existing Facility Assessment**: Assessment of current facilities
- **Site Accessibility Rating**: Rating from Excellent to Poor
- **Power Availability Rating**: Rating from Excellent to Poor
- **Ground Conditions Rating**: Rating from Excellent to Poor
- **Environmental Impact Assessment**: Environmental considerations

### **Water Quality Analysis**
- **Influent Characteristics**: Characteristics of incoming wastewater
- **Effluent Requirements**: Required effluent quality standards
- **Treatment Challenges**: Identified treatment challenges
- **Compliance Status**: Current compliance status

### **Proposed Solution**
- **Treatment Technology**: Selected treatment technology (required)
- **Process Description**: Detailed process description (required)
- **Treatment Stages**: Description of treatment stages

### **Cost and Timeline**
- **Equipment Cost**: Cost of treatment equipment
- **Civil Works Cost**: Cost of civil construction
- **Electrical Cost**: Cost of electrical work
- **Total Project Cost**: Automatically calculated total
- **Design Period**: Design phase duration in weeks
- **Procurement Period**: Procurement phase duration in weeks
- **Construction Period**: Construction phase duration in weeks
- **Commissioning Period**: Commissioning phase duration in weeks
- **Total Implementation Time**: Automatically calculated total

## Auto-fill Functions

### **From Technical Questionnaire**
```javascript
frm.call('auto_fill_from_tq')
```
Populates: lead, opportunity, wastewater_generator_type, current_capacity, design_capacity, project_title

### **From Site Visit**
```javascript
frm.call('auto_fill_from_site_visit')
```
Populates: site_conditions_summary, site_accessibility_rating, power_availability_rating, ground_conditions_rating, environmental_impact_assessment, existing_facility_assessment

### **From Water Sample**
```javascript
frm.call('auto_fill_from_water_sample')
```
Populates: influent_characteristics, compliance_status

## Sync Functions

### **Sync to External Site**
```javascript
frm.call('sync_to_external_site')
```
- Creates proposal on external site (Site 1)
- Generates and attaches PDF
- Updates sync status and external links
- Returns external proposal name and URL

## Validation Functions

### **Validate Proposal Completeness**
```javascript
frm.call('validate_proposal_completeness')
```
Checks required fields and returns completion status

### **Generate Proposal Summary**
```javascript
frm.call('generate_proposal_summary')
```
Generates a summary of key proposal information

## Permissions

- **System Manager**: Full access (create, read, write, delete, submit, cancel)
- **Site Manager**: Full access (create, read, write, delete, submit, cancel)

## Integration Points

1. **WWTP Technical Questionnaire**: Source document for basic project data
2. **Site Visit**: Source document for site conditions and assessments
3. **Water Sample**: Source document for water quality analysis
4. **External Site Settings**: Configuration for external site sync
5. **Lead**: Customer information
6. **Opportunity**: Sales opportunity tracking

## Best Practices

1. **Complete Auto-fill First**: Use auto-fill functions before manual entry
2. **Validate Before Submission**: Always validate proposal completeness
3. **Review Calculations**: Verify automatic cost and timeline calculations
4. **Sync After Submission**: Sync to external site only after internal review
5. **Document Changes**: Use comments and notes for important decisions
6. **Regular Updates**: Update proposal as new information becomes available

## Troubleshooting

### **Auto-fill Issues**
- Ensure related documents are properly linked
- Check that source documents have required data
- Verify document permissions

### **Sync Issues**
- Check external site settings configuration
- Verify API credentials and connectivity
- Review sync error messages for specific issues

### **Validation Issues**
- Complete all required fields
- Ensure logical data relationships
- Check date validations and capacity constraints

## Future Enhancements

1. **Template System**: Pre-defined proposal templates
2. **Approval Workflow**: Multi-level approval process
3. **Version Control**: Track proposal versions and changes
4. **Integration with CRM**: Enhanced lead and opportunity integration
5. **Reporting**: Comprehensive proposal analytics and reporting
