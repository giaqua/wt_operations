# External Site Settings

External Site Settings

## Fields

| Field | Type | Description |
|-------|------|-------------|
| Site Name | Data | Unique identifier for the external site |
| Site URL | Data | URL of the external ERPNext site |
| API Key | Password | API key for authentication |
| API Secret | Password | API secret for authentication |
| Enabled | Check | Whether this site integration is active |
| Test Connection | Button | Test the connection to external site |
| Connection Status | Data | Status of the last connection test |

## Usage

This doctype is used to configure external ERPNext site integration for the WWTP Technical Questionnaire. When a site visit is required, the system will automatically create a site visit request on the configured external site.

## Setup

1. Create a new External Site Settings record
2. Fill in the Site Name (unique identifier)
3. Enter the Site URL of the external ERPNext site
4. Provide API Key and API Secret for authentication
5. Enable the integration by checking the "Enabled" field
6. Test the connection using the "Test Connection" button
7. Save the record

## API Integration

The system uses ERPNext's REST API to:
- Test connection to the external site
- Create site visit requests automatically
- Handle authentication securely
- Provide error handling and user feedback
