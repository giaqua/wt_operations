# Troubleshooting

## Common Issues and Solutions

### Auto-Fill Functions Not Working

#### Problem: Auto-fill buttons don't populate data
**Causes:**
- Required links not set (Lead, Opportunity, Technical Questionnaire)
- Related documents not submitted
- Missing permissions

**Solutions:**
1. Verify all required links are populated
2. Ensure source documents are submitted
3. Check user permissions for related DocTypes
4. Refresh the form and try again

#### Problem: Effluent parameters not auto-populating
**Causes:**
- Effluent target type not selected
- Invalid effluent type selection

**Solutions:**
1. Select a valid effluent target type from dropdown
2. Use "Refresh Effluent Parameters" button
3. Check console for JavaScript errors

### Cross-Site Integration Issues

#### Problem: Site Visit Request sync fails
**Causes:**
- Invalid External Site Settings configuration
- Network connectivity issues
- Authentication failures
- Field validation errors on remote site

**Solutions:**
1. Test connection in External Site Settings
2. Verify API credentials (API Key, API Secret)
3. Check network connectivity to external site
4. Review sync error messages
5. Use "Retry Push" or "Manual Push" buttons

#### Problem: External sync status shows "Failed"
**Causes:**
- HTTP errors (400, 401, 403, 500)
- Field mapping issues
- Remote site validation failures

**Solutions:**
1. Check `external_sync_error` field for details
2. Verify field mappings in integration documentation
3. Test with minimal required fields
4. Contact remote site administrator

### Data Validation Errors

#### Problem: Date validation errors
**Causes:**
- Valid Up To date before Issue Date
- Follow-up dates in the past
- Invalid date formats

**Solutions:**
1. Ensure Valid Up To date is after Issue Date
2. Set realistic follow-up dates
3. Use proper date format (YYYY-MM-DD)

#### Problem: Required field validation
**Causes:**
- Missing mandatory fields
- Invalid field values
- Business rule violations

**Solutions:**
1. Complete all required fields (marked with *)
2. Use valid options from dropdowns
3. Follow business rules (e.g., BOOT operation period ≤ concession period)

### Permission and Access Issues

#### Problem: Cannot create or edit documents
**Causes:**
- Insufficient role permissions
- Document in submitted state
- Restricted access to certain fields

**Solutions:**
1. Check user role assignments
2. Verify DocType permissions
3. Cancel document if needed for editing
4. Contact System Manager for permission updates

#### Problem: Cannot see certain DocTypes
**Causes:**
- Missing module permissions
- Incorrect role assignments
- Hidden or disabled DocTypes

**Solutions:**
1. Verify WT Operations module access
2. Check role permissions for specific DocTypes
3. Enable DocType if disabled
4. Refresh user session

### Performance Issues

#### Problem: Slow form loading
**Causes:**
- Large child tables
- Complex queries
- Network latency

**Solutions:**
1. Optimize child table data
2. Use pagination for large datasets
3. Check network connectivity
4. Clear browser cache

#### Problem: Auto-fill functions timeout
**Causes:**
- Large datasets
- Complex calculations
- Server performance issues

**Solutions:**
1. Reduce data volume in related documents
2. Optimize server resources
3. Retry operation
4. Contact system administrator

## Error Messages Reference

### Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Customer is required" | Missing customer field | Select a customer from dropdown |
| "Valid Up To date must be after Issue Date" | Invalid date range | Set Valid Up To date after Issue Date |
| "Comments are required when Actual value does not match Target" | Missing comments for deviations | Add explanatory comments |
| "Connection failed. Please check your credentials." | Invalid API credentials | Verify API Key and Secret in External Site Settings |
| "Field validation error on external site" | Remote site field validation | Check field mappings and required fields |

### Sync Status Values

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| "Pending" | Sync not attempted | Manual trigger or automatic retry |
| "In Progress" | Sync in progress | Wait for completion |
| "Success" | Sync completed successfully | None |
| "Failed" | Sync failed | Check error message and retry |
| "Retry" | Retry scheduled | Wait for retry or manual intervention |

## Getting Help

### Self-Service Resources
1. Check this troubleshooting guide
2. Review [Setup Documentation](setup/)
3. Consult [Workflow Guides](workflows/)
4. Review [DocType Documentation](doctypes/)

### Escalation Path
1. **Level 1**: Check permissions and basic configuration
2. **Level 2**: Review integration settings and network connectivity
3. **Level 3**: Contact System Manager for advanced configuration
4. **Level 4**: Contact technical support for system-level issues

### Information to Provide When Seeking Help
- User role and permissions
- Specific error messages
- Steps to reproduce the issue
- Screenshots of error screens
- Sync status and error details (for integration issues)
- Browser and system information
