# WWTP Technical Questionnaire - Site Visit Integration

This feature automatically creates site visit requests on an external ERPNext site when the "Site visit required" checkbox is checked in the WWTP Technical Questionnaire.

## Setup Instructions

### 1. Configure External Site Settings

1. Go to **External Site Settings** doctype
2. Create a new record with the following information:
   - **Site Name**: A unique identifier for the external site
   - **Site URL**: The URL of the external ERPNext site (e.g., `https://example.erpnext.com`)
   - **API Key**: The API key for authentication
   - **API Secret**: The API secret for authentication
   - **Enabled**: Check this box to activate the integration
3. Click **Test Connection** to verify the credentials
4. Save the record

### 2. Using the Feature

1. Open a WWTP Technical Questionnaire document
2. Fill in the required fields (Lead, Opportunity, etc.)
3. Check the **Site visit required** checkbox
4. Save the document
5. The system will automatically:
   - Create a site visit request on the external ERPNext site
   - Store the external site visit request name in the `external_site_visit_request` field
   - Display a success message with the created request name

## Technical Details

### Files Created/Modified

1. **External Site Settings Doctype**:
   - `external_site_settings.json` - Doctype definition
   - `external_site_settings.py` - Python logic with API integration
   - `external_site_settings.js` - Client-side JavaScript for test connection

2. **WWTP Technical Questionnaire Updates**:
   - Added `external_site_visit_request` field to store the created request name
   - Updated Python logic to handle site visit request creation
   - Added validation hooks to trigger the integration

### API Integration

The system uses ERPNext's REST API to create site visit requests. The integration:

1. Authenticates using API Key and Secret
2. Creates a "Site Visit Request" document on the external site
3. Maps relevant fields from the WWTP Technical Questionnaire
4. Handles errors gracefully without preventing document submission

### Error Handling

- If external site settings are not configured, a warning message is displayed
- If the external site is unreachable, an error is logged but document submission continues
- Connection status is tracked and displayed in the External Site Settings

## Troubleshooting

### Common Issues

1. **"External Site Settings not found"**
   - Ensure you have created an External Site Settings record
   - Check that the record is enabled

2. **"Connection failed"**
   - Verify the Site URL is correct and accessible
   - Check that API Key and Secret are valid
   - Ensure the external site has API access enabled

3. **"Failed to create site visit request"**
   - Check if the external site has a "Site Visit Request" doctype
   - Verify the API user has permission to create documents
   - Check the external site's API logs for detailed error messages

### Testing

Run the test script to verify the integration:

```bash
cd /home/frappe/frappe-bench
bench --site your-site-name console
```

Then run:
```python
exec(open('/home/frappe/frappe-bench/apps/wt_operations/test_site_visit_integration.py').read())
```

## Security Considerations

- API credentials are stored as password fields and are encrypted
- The integration only creates site visit requests, it doesn't expose sensitive data
- All API calls are made over HTTPS
- Error messages don't expose sensitive information

## Future Enhancements

- Add support for multiple external sites
- Implement webhook notifications for status updates
- Add field mapping configuration
- Support for custom doctypes on external sites
