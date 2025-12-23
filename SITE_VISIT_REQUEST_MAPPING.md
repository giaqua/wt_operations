# Site Visit Request - Field Mapping Documentation

This document outlines the field mappings between the WWTP Technical Questionnaire and the external Site Visit Request doctype.

## Core Required Fields

These fields are always sent and should exist in the external Site Visit Request doctype:

| Field Name | Data Type | Source | Description |
|------------|-----------|--------|-------------|
| `lead` | Link (Lead) | WWTP Technical Questionnaire.lead | The lead associated with the WWTP project |
| `site_visit_date` | Date | Current date | Date for the site visit |
| `status` | Select | "Open" | Initial status of the site visit request |
| `notes` | Small Text | Auto-generated | Reference to source document |

## Optional Fields (Sent if Available)

These fields are sent if they exist in the external Site Visit Request doctype:

| Field Name | Data Type | Source | Description |
|------------|-----------|--------|-------------|
| `opportunity` | Link (Opportunity) | WWTP Technical Questionnaire.opportunity | Associated opportunity |
| `source_document` | Data | WWTP Technical Questionnaire.name | Name of the source document |
| `source_doctype` | Data | "WWTP Technical Questionnaire" | Type of source document |
| `visit_purpose` | Small Text | Generated from wastewater_generator_type | Purpose of the visit |
| `priority` | Select | Based on sample_collection_required | High if sample collection needed, Medium otherwise |
| `visit_type` | Select | "Technical Survey" | Type of visit |
| `estimated_duration` | Data | "2-4 hours" | Estimated time for the visit |
| `special_requirements` | Small Text | Generated from capacity and footprint | Technical requirements |
| `equipment_needed` | Small Text | Based on sample_collection_required | Required equipment |
| `follow_up_required` | Check | Based on sample_collection_required | Whether follow-up is needed |

## Field Value Generation Logic

### Visit Purpose
```
"STP Technical Assessment - {wastewater_generator_type}"
```
- Uses the wastewater generator type from WWTP Technical Questionnaire
- Falls back to "Wastewater Treatment" if not specified

### Priority
```
"High" if sample_collection_required is checked
"Medium" otherwise
```

### Special Requirements
```
"STP Capacity: {capacity}, Footprint: {footprint} sqm"
```
- Includes capacity and footprint information
- Shows "TBD" for missing values

### Equipment Needed
```
If sample_collection_required:
    "Water quality testing equipment, measuring tools, camera"
Else:
    "Measuring tools, camera"
```

### Follow-up Required
```
1 if sample_collection_required is checked
0 otherwise
```

## Error Handling

The system includes robust error handling:

1. **Field Validation Errors (400)**: If optional fields don't exist in the external doctype, the system falls back to creating a minimal site visit request with only required fields.

2. **Minimal Fallback**: If the full request fails, the system attempts to create a site visit request with only these fields:
   - `doctype`: "Site Visit Request"
   - `lead`: From WWTP Technical Questionnaire
   - `site_visit_date`: Current date
   - `status`: "Open"
   - `notes`: Reference to source document

## External Site Requirements

For the integration to work properly, the external Site Visit Request doctype should have:

### Minimum Required Fields:
- `lead` (Link to Lead)
- `site_visit_date` (Date)
- `status` (Select with "Open" option)
- `notes` (Small Text)

### Recommended Optional Fields:
- `opportunity` (Link to Opportunity)
- `source_document` (Data)
- `source_doctype` (Data)
- `visit_purpose` (Small Text)
- `priority` (Select: Low, Medium, High, Urgent)
- `visit_type` (Select)
- `estimated_duration` (Data)
- `special_requirements` (Small Text)
- `equipment_needed` (Small Text)
- `follow_up_required` (Check)

## API Integration Details

- **Endpoint**: `{site_url}/api/resource/Site Visit Request`
- **Method**: POST
- **Authentication**: Token-based (API Key:API Secret)
- **Content-Type**: application/json
- **Timeout**: 30 seconds

## Testing

To test the integration:

1. Create an External Site Settings record with valid credentials
2. Test the connection using the "Test Connection" button
3. Create a WWTP Technical Questionnaire with "Site visit required" checked
4. Save the document to trigger the site visit request creation
5. Check the external site for the created Site Visit Request

## Troubleshooting

### Common Issues:

1. **"Field validation error"**: Some optional fields don't exist in the external doctype
   - Solution: The system automatically falls back to minimal fields

2. **"Connection failed"**: API credentials are incorrect
   - Solution: Verify API Key and Secret in External Site Settings

3. **"Failed to create site visit request"**: External site doesn't have Site Visit Request doctype
   - Solution: Ensure the external site has the Site Visit Request doctype installed
