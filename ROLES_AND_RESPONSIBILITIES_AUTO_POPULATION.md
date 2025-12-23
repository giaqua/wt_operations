# WWTP Technical Questionnaire - Roles and Responsibilities Auto-Population

This document explains the automatic population functionality for the "TQ Roles and Responsibilities" child table in the WWTP Technical Questionnaire.

## Overview

The system automatically populates the "TQ Roles and Responsibilities" child table with all existing "Scope of Work" documents, creating a comprehensive checklist for project responsibilities.

## How It Works

### Automatic Population
- **Trigger**: When a new WWTP Technical Questionnaire is created or when the roles and responsibilities table is empty
- **Process**: System fetches all "Scope of Work" documents and creates corresponding rows in the child table
- **Data Mapping**:
  - `scope_of_work`: Links to the Scope of Work document
  - `responsible`: Left empty for manual assignment
  - `not_required`: Defaults to "No" (0)
  - `remarks`: Auto-filled with scope of work details

### Manual Controls
- **Refresh Button**: Manually refresh the table with current scope of work documents
- **Clear & Repopulate**: Clear existing entries and repopulate with fresh data
- **Summary Button**: View statistics about responsibility assignments

## Python Methods

### `populate_roles_and_responsibilities()`
```python
def populate_roles_and_responsibilities(self):
    """Auto-populate roles and responsibilities table with all scope of work documents"""
```
- Fetches all Scope of Work documents
- Creates child table rows for each scope of work
- Provides user feedback on success/failure

### `refresh_roles_and_responsibilities()` (Whitelisted)
```python
@frappe.whitelist()
def refresh_roles_and_responsibilities(self):
    """Manually refresh the roles and responsibilities table"""
```
- Allows manual refresh from client-side
- Returns success message

### `get_scope_of_work_summary()` (Whitelisted)
```python
@frappe.whitelist()
def get_scope_of_work_summary(self):
    """Get a summary of scope of work items"""
```
- Returns statistics about responsibility assignments
- Includes counts for GI, Customer, and unassigned items

## JavaScript Functionality

### Custom Buttons
1. **Refresh Roles & Responsibilities**: Manually refresh the table
2. **Scope of Work Summary**: Display statistics in a formatted dialog
3. **Clear & Repopulate**: Clear and repopulate with confirmation

### Auto-Population on Load
- Automatically checks if table is empty when document loads
- Triggers population if no entries exist

### Table Field Interactions
- **Scope of Work Selection**: Auto-fills remarks with scope details
- **Responsibility Assignment**: Provides feedback when assigned
- **Not Required Toggle**: Tracks when items are marked as not required

## Data Flow

```
Scope of Work Documents → WWTP Technical Questionnaire → Roles & Responsibilities Table
```

1. **Scope of Work** documents are created with:
   - `scope_of_work`: Name/title of the work item
   - `scope_of_work_details`: Detailed description

2. **WWTP Technical Questionnaire** automatically creates child table rows:
   - Links to each scope of work document
   - Pre-fills remarks with scope details
   - Leaves responsibility assignment for manual input

3. **Roles & Responsibilities Table** allows:
   - Assignment of responsibility (GI/Customer)
   - Marking items as not required
   - Adding custom remarks

## Usage Examples

### Creating a New WWTP Technical Questionnaire
1. Create new WWTP Technical Questionnaire
2. Fill in basic information (Lead, Opportunity, etc.)
3. Save the document
4. System automatically populates roles and responsibilities table
5. Assign responsibilities as needed

### Managing Existing Questionnaire
1. Open existing WWTP Technical Questionnaire
2. Use "Refresh Roles & Responsibilities" button to update with new scope of work documents
3. Use "Scope of Work Summary" to view assignment statistics
4. Use "Clear & Repopulate" to start fresh with current scope of work documents

### Responsibility Assignment
1. Select scope of work from dropdown
2. Choose responsible party (GI/Customer)
3. Mark as "Not Required" if applicable
4. Add custom remarks if needed

## Error Handling

### No Scope of Work Documents
- System displays message: "No scope of work documents found. Please create scope of work documents first."
- User needs to create scope of work documents before proceeding

### Population Errors
- Errors are logged for debugging
- User-friendly error messages are displayed
- System continues to function even if population fails

## Integration Points

### Scope of Work Doctype
- Source of data for population
- Contains work item names and descriptions
- Must exist before population can occur

### TQ Roles and Responsibilities Child Table
- Target for population
- Links to scope of work documents
- Allows responsibility assignment and customization

### WWTP Technical Questionnaire
- Main document containing the child table
- Triggers automatic population
- Provides management interface

## Best Practices

1. **Create Scope of Work Documents First**: Ensure all scope of work documents exist before creating WWTP Technical Questionnaires

2. **Review Auto-Populated Data**: Always review the populated table and assign responsibilities appropriately

3. **Use Summary Feature**: Regularly check the scope of work summary to ensure proper assignment distribution

4. **Customize Remarks**: Add project-specific remarks to clarify requirements

5. **Mark Unnecessary Items**: Use "Not Required" checkbox for items that don't apply to specific projects

## Troubleshooting

### Table Not Populating
- Check if scope of work documents exist
- Verify user has read permissions on scope of work doctype
- Check error logs for detailed error messages

### Missing Scope of Work Items
- Use "Refresh Roles & Responsibilities" button to update with new documents
- Use "Clear & Repopulate" to start fresh

### Responsibility Assignment Issues
- Ensure responsible field is properly set
- Check that scope of work is selected before assigning responsibility
- Verify user has write permissions on the document
