# External Site Settings

## Purpose

External Site Settings configures the connection and authentication parameters for cross-site integration between multiple ERPNext installations. It enables seamless data synchronization and collaboration between Site 1 and Site 2.

## When to Use

- **Multi-Site Operations**: Organizations with multiple ERPNext installations
- **Cross-Site Collaboration**: Technical and commercial teams on different sites
- **Data Synchronization**: Synchronize Site Visit Requests and Technical Proposals
- **Centralized Management**: Manage cross-site operations from one location

## Status & Workflow

### Document States
- **Draft (0)**: Configuration being prepared
- **Submitted (1)**: Configuration active and ready for use

### Workflow Transitions
- **Draft → Submitted**: Complete configuration and submit
- **Submitted → Draft**: Modify configuration (System Manager only)

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Site Name | `site_name` | Data | Required - Unique identifier for external site |
| Site URL | `site_url` | Data | Required - URL of external ERPNext site |
| API Key | `api_key` | Password | Required - API key for authentication |
| API Secret | `api_secret` | Password | Required - API secret for authentication |
| Enabled | `enabled` | Check | Enable/disable integration |
| Test Connection | `test_connection` | Button | Test connection to external site |
| Connection Status | `connection_status` | Data | Read-only - Status of last connection test |

## Actions & Automations

### Custom Buttons
- **Test Connection**: Test connection to external site
- **Create Site Visit Request**: Create SVR on external site
- **Create Technical Proposal**: Create Technical Proposal on external site

### Client Scripts
- **File**: `external_site_settings.js`
- **Functions**:
  - `test_connection`: Test API connection

### Server Methods
- **File**: `external_site_settings.py`
- **Methods**:
  - `test_connection`: Test connection to external site
  - `get_api_headers`: Get API headers for requests
  - `create_site_visit_request`: Create SVR on external site
  - `create_technical_proposal_from_local`: Create Technical Proposal on external site
  - `attach_tq_pdf_to_external_svr`: Attach TQ PDF to external SVR
  - `post_resource`: Generic POST method for external site

## Permissions & Roles

| Role | Create | Read | Update | Delete | Submit |
|------|--------|------|--------|--------|--------|
| System Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Site Manager | - | ✓ | - | - | - |
| Operations Manager | - | ✓ | - | - | - |
| Operations Technician | - | - | - | - | - |
| Account Manager | - | - | - | - | - |

## Data Validation

### Required Fields
- Site name must be unique
- Site URL must be valid
- API Key must be provided
- API Secret must be provided

### Business Rules
- Site name must be unique across all configurations
- Site URL must be accessible
- API credentials must be valid
- Connection must be testable

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Connection testing**: Test API connection before saving

## Common Tasks

### Setting Up External Site Integration
1. Navigate to WT Operations → External Site Settings
2. Click "New" to create new configuration
3. Enter unique site name
4. Enter external site URL
5. Generate API Key and Secret on external site
6. Enter API credentials
7. Enable integration
8. Test connection
9. Save and submit configuration

### Testing Connection
1. Open External Site Settings
2. Click "Test Connection" button
3. System tests API connection
4. Review connection status
5. Address any connection issues

### Creating Site Visit Request on External Site
1. Complete Site Visit Request on local site
2. Submit the request
3. System automatically creates SVR on external site
4. Monitor sync status
5. Handle any sync errors

### Creating Technical Proposal on External Site
1. Complete Technical Proposal on local site
2. Use "Sync to External Site" button
3. System creates Technical Proposal on external site
4. Monitor sync status
5. Handle any sync errors

## API Integration Details

### Authentication
- **Method**: Token-based authentication
- **Format**: `Authorization: token {api_key}:{api_secret}`
- **Content-Type**: `application/json`

### Connection Testing
- **Endpoint**: `/api/method/frappe.auth.get_logged_user`
- **Method**: GET
- **Timeout**: 10 seconds

### Site Visit Request Creation
- **Endpoint**: `/api/resource/Site Visit Request`
- **Method**: POST
- **Timeout**: 30 seconds

### Technical Proposal Creation
- **Endpoint**: `/api/resource/WWTP Technical Proposal`
- **Method**: POST
- **Timeout**: 30 seconds

### File Upload
- **Endpoint**: `/api/resource/File`
- **Method**: POST
- **Timeout**: 30 seconds

## Error Handling

### Connection Errors
- **Invalid URL**: Check site URL format
- **Network Timeout**: Check network connectivity
- **Authentication Failed**: Verify API credentials
- **Permission Denied**: Check API permissions

### Sync Errors
- **Field Validation**: Check field mappings
- **Required Fields**: Ensure all required fields are provided
- **Data Format**: Verify data format compatibility
- **Business Rules**: Check business rule compliance

### Error Response Handling
- **HTTP 200**: Success
- **HTTP 400**: Bad Request (validation errors)
- **HTTP 401**: Unauthorized (invalid credentials)
- **HTTP 403**: Forbidden (insufficient permissions)
- **HTTP 500**: Internal Server Error

## Security Considerations

### API Credentials
- **Storage**: Credentials stored securely in database
- **Access**: Only System Managers can view/modify credentials
- **Rotation**: Regular credential rotation recommended
- **Audit**: All credential changes logged

### Data Transmission
- **Encryption**: All data transmitted over HTTPS
- **Validation**: Input validation on both ends
- **Sanitization**: Data sanitization before processing
- **Logging**: Comprehensive logging of all operations

### Access Control
- **Role-based**: Role-based access control
- **Permission Checks**: Permission validation on both sites
- **Audit Trail**: Complete audit trail of all operations
- **Monitoring**: Continuous monitoring of access patterns

## Troubleshooting

### Common Issues

**Connection Test Fails**
- Check site URL format and accessibility
- Verify API credentials are correct
- Check network connectivity
- Verify external site is running

**Sync Operations Fail**
- Test connection first
- Check field mappings
- Verify required fields
- Review error messages

**Permission Errors**
- Check API user permissions on external site
- Verify role assignments
- Check document permissions
- Review API access settings

### Resolution Steps
1. **Test Connection**: Use Test Connection button
2. **Check Logs**: Review system logs for detailed errors
3. **Verify Credentials**: Confirm API credentials are correct
4. **Check Permissions**: Verify permissions on both sites
5. **Contact Support**: Escalate persistent issues

## Best Practices

### Configuration
- **Unique Names**: Use descriptive, unique site names
- **Secure Credentials**: Keep API credentials secure
- **Regular Testing**: Test connections regularly
- **Documentation**: Document configuration details

### Operations
- **Monitor Status**: Monitor sync status regularly
- **Handle Errors**: Address sync errors promptly
- **Update Credentials**: Rotate credentials regularly
- **Backup Configuration**: Maintain backup of configuration

### Security
- **HTTPS Only**: Use HTTPS for all communications
- **Credential Security**: Protect API credentials
- **Access Control**: Implement proper access controls
- **Audit Logging**: Maintain comprehensive audit logs
