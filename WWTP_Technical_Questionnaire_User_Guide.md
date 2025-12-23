# WWTP Technical Questionnaire - User Guide

## Overview
The WWTP (Wastewater Treatment Plant) Technical Questionnaire is a comprehensive form designed to collect detailed information about wastewater treatment requirements, facility specifications, and project parameters. This guide will walk you through each section step-by-step.

## Table of Contents
1. [Basic Information](#basic-information)
2. [Landscape and Facility](#landscape-and-facility)
3. [Design Parameters](#design-parameters)
4. [Influent Quality](#influent-quality)
5. [Effluent Quality](#effluent-quality)
6. [Roles and Responsibilities](#roles-and-responsibilities)
7. [Tips and Best Practices](#tips-and-best-practices)

---

## Basic Information

### Required Fields
- **Lead**: Select the lead contact for this project (required)
- **Date**: The date of questionnaire completion (defaults to today)
- **By**: Select the user completing the questionnaire

### Optional Fields
- **Opportunity**: Link to related opportunity (automatically filtered by lead)
- **Site Visit Required**: Check if a site visit is needed
- **Sample Collection Required**: Check if sample collection is needed

---

## Landscape and Facility

This section collects information about the physical characteristics and requirements of the wastewater treatment facility.

### Required Fields
- **Wastewater Generator (type)**: Select from dropdown options:
  - Domestic
  - Industrial
  - Slaughterhouse
  - Concrete
  - Oil and Gas
  - Leachate
  - Special Case

- **Capacity (m³/day)**: Enter the daily treatment capacity in cubic meters
- **Is it new WWTP or an upgrade?**: Specify whether this is a new facility or an upgrade to existing infrastructure
- **Number of streams**: Enter the number of influent streams (automatically creates corresponding table rows)

### Optional Fields
- **The available footprint dedicated for WWTP in SM**: Available space in square meters
- **Location of the WWTP needed**: Specific location details
- **Available equipment (tanks, pumps, etc.)**: List existing equipment
- **Design of the site condition**: Describe site conditions and constraints
- **Design of the site condition attach**: Upload relevant documents or drawings

### Special Case Generator Type
- **Note**: This field appears only when "Special Case" is selected as the wastewater generator type
- Provide specific details about the special case scenario

---

## Design Parameters

This section defines the operational parameters for the wastewater treatment plant.

### Flow Parameters
- **Daily Flow (m³/day)**: Maximum, minimum, or range of daily flow
- **Operation Hours (hr/day)**: Hours of operation per day
- **Average Hourly Flow (m³/hr)**: Calculated or specified average flow rate
- **Min Flow (m³/day)**: Minimum daily flow rate
- **Peak Factor**: Multiplier for peak flow conditions
- **Peak Hours**: Duration of peak flow conditions

### Tips for Design Parameters
- Ensure flow rates are consistent (daily flow should equal operation hours × average hourly flow)
- Peak factor typically ranges from 1.5 to 3.0 for most applications
- Consider seasonal variations in flow rates

---

## Influent Quality

This section captures the characteristics of incoming wastewater streams.

### Automatic Stream Management
- **Number of Streams**: When you enter a number, the system automatically creates corresponding rows in the influent stream table
- Each stream will be labeled as "Stream 1", "Stream 2", etc.

### Influent Stream Table
For each stream, provide the following parameters (all in mg/L unless specified):

#### Physical Parameters
- **pH**: Acidity/alkalinity level
- **TSS (mg/L)**: Total Suspended Solids
- **Turbidity (mg/L)**: Water clarity measure
- **Temperature (°C)**: Water temperature (range: 20-60°C)

#### Chemical Parameters
- **COD (mg/L)**: Chemical Oxygen Demand
- **BOD5 (mg/L)**: 5-day Biochemical Oxygen Demand
- **TDS (mg/L)**: Total Dissolved Solids
- **Total Chlorinates Hydrocarbons (mg/L)**: Chlorinated organic compounds
- **Oil & Grease (mg/L)**: Petroleum-based contaminants
- **Phenol (mg/L)**: Phenolic compounds
- **Arsenic (mg/L)**: Heavy metal content
- **PO4-P (mg/L)**: Phosphorus content
- **Sulphate (mg/L)**: Sulfate concentration
- **TKN (mg/L)**: Total Kjeldahl Nitrogen

### Tips for Influent Quality
- Provide realistic ranges rather than exact values
- Consider seasonal variations
- Include worst-case scenario values for design purposes
- If certain parameters are not applicable, leave them blank

---

## Effluent Quality

This section defines the required quality standards for treated wastewater.

### Effluent Parameters
All parameters are in mg/L unless specified:

- **pH**: Target pH range for effluent
- **TSS (mg/L)**: Maximum allowable suspended solids
- **BOD5 (mg/L)**: Maximum allowable biochemical oxygen demand
- **COD (mg/L)**: Maximum allowable chemical oxygen demand
- **Turbidity (NTU)**: Maximum allowable turbidity
- **Oil & Grease (mg/L)**: Maximum allowable oil and grease content
- **TDS (mg/L)**: Maximum allowable total dissolved solids
- **Free Chlorine (mg/L)**: Residual chlorine requirements
- **Ecoli (set/100mL)**: Maximum allowable E. coli count
- **Wormies (set/100mL)**: Maximum allowable worm count

### Target Effluent Type
Select the intended use of treated effluent:
- **Unusable (safe discharge)**: Safe discharge to environment
- **Irrigation (restricted)**: Limited agricultural use
- **Irrigation (unrestricted)**: Full agricultural use
- **Industrial - Washing**: Industrial washing applications
- **Industrial - Cooling**: Industrial cooling applications
- **Industrial - Manufacturing**: Manufacturing process water

### Tips for Effluent Quality
- Ensure effluent standards comply with local regulations
- Consider the intended reuse application
- Some parameters may not be applicable depending on effluent type

---

## Roles and Responsibilities

This section automatically populates with all available scope of work items, allowing you to assign responsibilities.

### Automatic Population
- The table automatically loads with all available scope of work items
- Use the "Refresh Scope of Work" button to update the list if new items are added

### For Each Scope of Work Item
- **Scope Of Work**: Pre-populated with available options
- **Responsible**: Select either "GI" (Government Institution) or "Customer"
- **Not Required**: Check if this item doesn't apply to your project
- **Remarks**: Add any specific notes or clarifications

### Tips for Roles and Responsibilities
- Mark items as "Not Required" if they don't apply to your specific project
- Be specific in remarks to avoid misunderstandings
- Consider both technical and administrative responsibilities

---

## Tips and Best Practices

### General Guidelines
1. **Complete Required Fields First**: Focus on mandatory fields before filling optional ones
2. **Save Frequently**: Use Ctrl+S to save your progress regularly
3. **Use Consistent Units**: Ensure all measurements use consistent units (metric system)
4. **Provide Realistic Values**: Use actual or realistic estimated values rather than theoretical maximums

### Data Quality
1. **Verify Calculations**: Double-check flow rate calculations and conversions
2. **Consider Seasonal Variations**: Account for seasonal changes in wastewater characteristics
3. **Include Safety Margins**: Design parameters should include appropriate safety factors
4. **Document Assumptions**: Use remarks fields to document assumptions and constraints

### Collaboration
1. **Coordinate with Stakeholders**: Ensure all relevant parties provide input
2. **Review Before Submission**: Have technical experts review the completed questionnaire
3. **Keep Records**: Maintain copies of supporting documents and calculations

### Troubleshooting
1. **Form Validation Errors**: Check that all required fields are completed
2. **Calculation Errors**: Verify that flow rates and parameters are mathematically consistent
3. **Missing Data**: Use remarks to explain why certain data is unavailable

---

## Form Submission

### Before Submitting
1. Review all sections for completeness
2. Verify that calculations are correct
3. Ensure all required fields are filled
4. Check that effluent standards are achievable with influent characteristics

### After Submission
1. The form will be reviewed by technical experts
2. Additional information may be requested
3. Site visits or sample collection may be scheduled if requested
4. A technical proposal will be prepared based on your inputs

---

## Support and Contact

For technical assistance or questions about completing this questionnaire:
- Contact your project manager
- Refer to technical documentation
- Consult with wastewater treatment experts

---

*This guide is designed to help you complete the WWTP Technical Questionnaire accurately and efficiently. Take your time to provide accurate information, as this data will be used to design an appropriate wastewater treatment solution for your needs.*
