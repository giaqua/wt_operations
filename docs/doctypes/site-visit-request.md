# Site Visit Request

## Purpose

The Site Visit Request is a formal request for conducting on-site technical assessments and data collection for WWTP projects. It serves as the coordination document between technical teams and customers for site visits.

## When to Use

- **Technical Assessments**: Formal request for site technical assessment
- **Data Collection**: Request for on-site data collection
- **Customer Coordination**: Coordinate site visits with customers
- **Cross-Site Operations**: Manage site visits across multiple locations

## Status & Workflow

### Document States
- **Draft (0)**: Request being prepared
- **Submitted (1)**: Request submitted and active
- **Cancelled (2)**: Request cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete request and submit
- **Submitted → Cancelled**: Cancel active request
- **Cancelled → Draft**: Restore cancelled request

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Lead | `lead` | Link | Link to Lead |
| Opportunity | `opportunity` | Link | Link to Opportunity |
| Technical Questionnaire | `technical_questionnaire` | Link | Link to Technical Questionnaire |
| Site Visit Date | `site_visit_date` | Date | Planned visit date |
| Status | `status` | Select | Request status (Open, Scheduled, Completed, Cancelled) |
| Priority | `priority` | Select | Visit priority (Low, Medium, High, Urgent) |
| Visit Type | `visit_type` | Select | Type of visit |
| Visit Purpose | `visit_purpose` | Data | Purpose of visit |
| Special Requirements | `special_requirements` | Small Text | Special requirements |
| Equipment Needed | `equipment_needed` | Small Text | Required equipment |
| Estimated Duration | `estimated_duration` | Data | Estimated visit duration |
| Follow-up Required | `follow_up_required` | Check | Flag for follow-up required |
| Source Document | `source_document` | Data | Source document reference |
| Source DocType | `source_doctype` | Data | Source document type |
| Notes | `notes` | Small Text | Additional notes |

## Child Tables & Relations

### Site Visit Tracking Table
- **Purpose**: Track multiple site visits for the same request
- **Fields**: Visit Date, Status, Notes, Completed By

## Actions & Automations

### Auto-Fill Functions
- **Lead Details**: Auto-populate from linked Lead
- **Contact Details**: Auto-populate contact information
- **Project Requirements**: Auto-populate from Technical Questionnaire

### Custom Buttons
- **Create Site Visit**: Create Site Visit from request
- **Push to External Site**: Sync to external site
- **Retry Push**: Retry failed sync operations
- **Manual Push**: Manual sync trigger

### Client Scripts
- **File**: `site_visit_request.js`
- **Functions**:
  - `lead`: Auto-populate lead details
  - `technical_questionnaire`: Auto-populate project requirements
  - `on_submit`: Trigger cross-site sync

### Server Methods
- **File**: `site_visit_request.py`
- **Methods**:
  - `get_lead_details`: Get lead information
  - `auto_fill_contact_details`: Auto-populate contact details
  - `create_site_visit`: Create Site Visit
  - `push_to_external_site`: Sync to external site
  - `retry_push`: Retry sync operation
  - `manual_push_to_external_site`: Manual sync

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
- Lead must be selected
- Site visit date must be set
- Priority must be selected
- Visit type must be selected
- Visit purpose must be specified

### Business Rules
- Site visit date must be in the future
- Priority affects scheduling and resource allocation
- Visit type determines required equipment and personnel
- Follow-up required flag affects downstream processes

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Date validation**: Ensure visit date is realistic

## Common Tasks

### Creating a Site Visit Request
1. Navigate to WT Operations → Site Visit Request
2. Click "New" to create new request
3. Select Lead from dropdown
4. Select Opportunity if available
5. Link to Technical Questionnaire
6. Set site visit date
7. Select priority and visit type
8. Fill in visit purpose
9. Add special requirements
10. Specify equipment needed
11. Set estimated duration
12. Review and submit

### Auto-Populating from Technical Questionnaire
1. Select Technical Questionnaire
2. System automatically populates:
   - Lead and opportunity details
   - Project requirements
   - Special requirements
   - Equipment needed
   - Visit purpose
3. Review and customize as needed

### Creating Site Visit
1. Complete Site Visit Request
2. Submit the request
3. Click "Create Site Visit" button
4. Review auto-populated information
5. Complete site visit details
6. Submit Site Visit

### Cross-Site Sync
1. Complete Site Visit Request
2. Submit the request
3. System automatically syncs to external site
4. Monitor sync status
5. Use retry functions if sync fails

## Cross-Site Integration

### Sync Process
1. **Document Creation**: Create Site Visit Request on Site 1
2. **Auto-Sync**: System automatically syncs to Site 2
3. **Status Tracking**: Track sync status and errors
4. **Retry Mechanism**: Retry failed sync operations

### Sync Fields
- **external_request_name**: Name of document on external site
- **external_request_url**: URL of document on external site
- **external_sync_status**: Current sync status
- **external_sync_error**: Error details if sync fails

### Error Handling
- **Authentication Errors**: Invalid API credentials
- **Network Errors**: Connection timeouts or failures
- **Validation Errors**: Field validation failures on remote site
- **Permission Errors**: Insufficient permissions on remote site

## Tips & Pitfalls

### Best Practices
- **Plan Ahead**: Schedule visits well in advance
- **Coordinate with Customer**: Confirm visit details with customer
- **Prepare Equipment**: Ensure all required equipment is available
- **Document Requirements**: Clearly document special requirements
- **Monitor Sync Status**: Monitor cross-site sync status

### Common Issues
- **Sync Failures**: Check External Site Settings configuration
- **Date Conflicts**: Ensure visit date is available
- **Missing Equipment**: Verify equipment availability
- **Permission Issues**: Check user role assignments

### Troubleshooting
- **Sync Not Working**: Test External Site Settings connection
- **Auto-Fill Issues**: Check Technical Questionnaire linkage
- **Date Validation Errors**: Ensure visit date is in future
- **Cross-Site Issues**: Verify API credentials and permissions
