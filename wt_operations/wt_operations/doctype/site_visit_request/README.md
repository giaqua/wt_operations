# Site Visit Request

Site Visit Request

## Fields

### Basic Information
| Field | Type | Description |
|-------|------|-------------|
| Lead | Link (Lead) | Associated lead (required) |
| Opportunity | Link (Opportunity) | Associated opportunity |
| Site Visit Date | Date | Date for the site visit (required) |
| Status | Select | Current status of the request |
| Source Document | Data | Name of the source document |
| Source DocType | Data | Type of source document |
| Notes | Small Text | Additional notes |

### Visit Details
| Field | Type | Description |
|-------|------|-------------|
| Visit Type | Select | Type of visit (Technical Survey, etc.) |
| Priority | Select | Priority level (Low, Medium, High, Urgent) |
| Assigned To | Link (User) | User assigned to the visit |
| Contact Person | Data | Primary contact person |
| Contact Number | Data | Contact phone number |
| Email | Data | Contact email address |

### Site Location
| Field | Type | Description |
|-------|------|-------------|
| Site Address | Small Text | Full site address |
| City | Data | City name |
| State | Data | State name |
| Pincode | Data | Postal code |

### Visit Requirements
| Field | Type | Description |
|-------|------|-------------|
| Visit Purpose | Small Text | Purpose of the visit |
| Special Requirements | Small Text | Special requirements |
| Equipment Needed | Small Text | Required equipment |
| Estimated Duration | Data | Expected duration |
| Preferred Time Slot | Data | Preferred time for visit |

### Follow-up
| Field | Type | Description |
|-------|------|-------------|
| Follow-up Required | Check | Whether follow-up is needed |
| Follow-up Date | Date | Date for follow-up |
| Follow-up Notes | Small Text | Follow-up notes |

### Related Site Visits
| Field | Type | Description |
|-------|------|-------------|
| Site Visits | Table | Child table tracking all related Site Visits |
| Site Visit | Link | Link to Site Visit document |
| Visit Date | Date | Date of the visit (auto-filled) |
| Visit Status | Data | Status of the visit (auto-filled) |
| Visit By | Data | Person who conducted the visit (auto-filled) |

## Features

### Site Visit Creation
- **Create Site Visit Button**: Available for submitted SVRs
- **One-to-Many Relationship**: One SVR can have multiple Site Visits
- **Auto-population**: Site Visit fields are automatically populated from SVR data
- **Status Tracking**: SVR status updates to "Completed" when Site Visit is submitted

### Auto-fill Contact Details
- Automatically fills contact information when a lead is selected
- Uses lead's contact details to populate contact fields
- Custom button to manually trigger auto-fill

### Date Validation
- Ensures follow-up date is not before site visit date
- Automatic validation on field changes

### Status Management
- Automatic status updates based on document state
- Status changes on submit/cancel
- Status updates from related Site Visits

### Integration Ready
- Compatible with WWTP Technical Questionnaire integration
- Receives data from external sites via API
- Supports both manual and automated creation

## Usage

### Manual Creation
1. Create new Site Visit Request
2. Select Lead (required)
3. Set Site Visit Date (required)
4. Fill in visit details and requirements
5. Save and submit

### Creating Site Visits from SVR
1. Submit the Site Visit Request
2. Click "Create Site Visit" button
3. Site Visit is created with auto-populated fields
4. Complete Site Visit details and submit
5. SVR status automatically updates to "Completed"

### Automated Creation
- Created automatically when WWTP Technical Questionnaire has "Site visit required" checked
- Populated with data from the source questionnaire
- Includes technical requirements and equipment needs

## Field Mappings (SVR → Site Visit)

| SVR Field | Site Visit Field | Notes |
|-----------|------------------|-------|
| lead | lead | Direct copy |
| contact_person | contact_person | Direct copy |
| contact_number | contact_number | Direct copy |
| email | email | Direct copy |
| site_address | site_address | Direct copy |
| city | city | Direct copy |
| state | state | Direct copy |
| latitude_and_longitude | latitude_and_longitude | Direct copy |
| maps_location_link | maps_location_link | Direct copy |
| site_visit_date | date | Map to visit date |
| visit_purpose | site_observations | Context for visit |
| equipment_needed | equipment_used | Equipment list |
| assigned_to | visit_by | Map to employee if available |

## Status Workflow
- **Open**: Initial status when created
- **Scheduled**: When visit is scheduled
- **In Progress**: When visit is ongoing
- **Completed**: When visit is finished (auto-updated from Site Visit)
- **Cancelled**: When visit is cancelled

## Permissions
- **System Manager**: Full access (create, read, write, delete, submit)
- **Site Manager**: Limited access (create, read, write, submit)