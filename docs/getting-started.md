# Getting Started

## User Roles and Permissions

### System Manager
- Full access to all DocTypes
- Can configure External Site Settings
- Manages master data (Scope of Work, Wastewater Generator Types)
- Handles system configuration and troubleshooting

### Site Manager
- Creates and manages WWTP Technical Questionnaires
- Handles Site Visit Requests and Site Visits
- Reviews and submits Technical Proposals
- Manages Customer Proposals

### Operations Technician
- Creates Daily Operation Reports
- Manages Water Samples and Lab Test Results
- Updates Site Visit information
- Handles routine operational tasks

### Operations Manager
- Reviews and approves operational reports
- Manages complex technical assessments
- Handles escalated issues
- Coordinates cross-site operations

## Navigation

### Main Menu Access
1. Navigate to **WT Operations** module in the main menu
2. Key DocTypes are accessible from the module dashboard:
   - WWTP Technical Questionnaire
   - Site Visit Request
   - Site Visit
   - Water Sample
   - WWTP Technical Proposal
   - Customer Proposal

### Common UI Elements

#### Auto-Fill Buttons
Many forms include auto-fill buttons that populate data from related documents:
- **Auto-fill from Technical Proposal** (Customer Proposal)
- **Auto-fill from STP** (Site Visit)
- **Refresh Effluent Parameters** (Technical Questionnaire)

#### Custom Buttons
Look for custom action buttons in the toolbar:
- **Create Site Visit Request** (Technical Questionnaire)
- **Open Local SVR** (Technical Questionnaire)
- **Test Connection** (External Site Settings)

#### Status Indicators
- **DocStatus**: Draft (0), Submitted (1), Cancelled (2)
- **Sync Status**: For cross-site integrations
- **Compliance Status**: For regulatory tracking

## Common Tasks

### Creating a New Project
1. Start with a **Lead** in CRM
2. Create **WWTP Technical Questionnaire** linked to the Lead
3. Fill in basic project information
4. Select effluent target type for auto-population
5. Submit the questionnaire

### Managing Site Visits
1. Create **Site Visit Request** from Technical Questionnaire
2. Schedule the visit
3. Conduct **Site Visit** and collect data
4. Create **Water Sample** records if needed
5. Update status and link to lab results

### Generating Proposals
1. Create **WWTP Technical Proposal** from Technical Questionnaire
2. Use auto-fill buttons to populate data
3. Review and customize technical details
4. Create **Customer Proposal** with commercial options
5. Generate **Request for Proposal** if needed

## Tips for Success

### Data Entry Best Practices
- Always link documents properly (Lead → Opportunity → Technical Questionnaire)
- Use auto-fill buttons to ensure data consistency
- Complete required fields before submitting
- Add comments when actual values differ from targets

### Cross-Site Operations
- Test External Site Settings connection before use
- Monitor sync status for cross-site documents
- Use retry buttons if sync fails
- Keep local and external data synchronized

### Troubleshooting Common Issues
- **Missing auto-fill data**: Ensure required links are set
- **Sync failures**: Check External Site Settings configuration
- **Permission errors**: Verify user role assignments
- **Validation errors**: Review required fields and business rules

## Next Steps

- Review [Workflows](workflows/) for detailed process documentation
- Explore [DocTypes](doctypes/) for specific document guidance
- Configure [Integrations](integrations/) for multi-site operations
- Set up [Permissions](setup/permissions.md) for your team
