# Permissions

## Role-Based Access Control

The WT Operations module uses role-based permissions to control access to different DocTypes and functions.

## Permission Matrix

| DocType | System Manager | Site Manager | Operations Manager | Operations Technician | Account Manager |
|---------|---------------|--------------|-------------------|---------------------|-----------------|
| **WWTP Technical Questionnaire** | CRUDES | CRUDES | CRUDES | R | R |
| **WWTP Technical Proposal** | CRUDES | CRUDES | CRUDES | R | R |
| **Site Visit Request** | CRUDES | CRUDES | CRUDES | CRUD | R |
| **Site Visit** | CRUDES | CRUDES | CRUDES | CRUD | R |
| **Water Sample** | CRUDES | CRUDES | CRUDES | CRUDES | R |
| **Lab Test Result** | CRUDES | CRUDES | CRUDES | CRUDES | R |
| **Customer Proposal** | CRUDES | CRUDES | CRUDES | R | CRUDES |
| **Request for Proposal** | CRUDES | CRUDES | CRUDES | R | CRUDES |
| **Daily Operation Report** | CRUDES | CRUDES | CRUDES | CRUDES | R |
| **Project Unit Assignment** | CRUDES | CRUDES | CRUDES | R | R |
| **Scope of Work** | CRUDES | R | R | R | R |
| **Wastewater Generator Type** | CRUDES | R | R | R | R |
| **Treatment Parameter** | CRUDES | R | R | R | R |
| **External Site Settings** | CRUDES | - | - | - | - |

**Legend:**
- **C** = Create
- **R** = Read
- **U** = Update
- **D** = Delete
- **E** = Export
- **S** = Submit

## Role Definitions

### System Manager
- **Full Access**: Complete control over all DocTypes and system configuration
- **Responsibilities**:
  - Configure External Site Settings
  - Manage master data (Scope of Work, Wastewater Generator Types)
  - Set up user roles and permissions
  - Handle system-level troubleshooting
  - Manage cross-site integrations

### Site Manager
- **Project Management**: Full control over project-related DocTypes
- **Responsibilities**:
  - Create and manage WWTP Technical Questionnaires
  - Handle Site Visit Requests and Site Visits
  - Generate Technical Proposals
  - Manage Customer Proposals
  - Coordinate with Operations teams

### Operations Manager
- **Operations Oversight**: Full control over operational DocTypes
- **Responsibilities**:
  - Review and approve operational reports
  - Manage complex technical assessments
  - Handle escalated operational issues
  - Coordinate cross-site operations
  - Oversee compliance monitoring

### Operations Technician
- **Daily Operations**: Control over operational and data collection DocTypes
- **Responsibilities**:
  - Create Daily Operation Reports
  - Manage Water Samples and Lab Test Results
  - Update Site Visit information
  - Handle routine operational tasks
  - Monitor treatment parameters

### Account Manager
- **Commercial Management**: Control over commercial DocTypes
- **Responsibilities**:
  - Manage Customer Proposals
  - Handle Request for Proposals
  - Coordinate with technical teams
  - Manage customer relationships
  - Track commercial opportunities

## Permission Configuration

### Setting Up Roles

1. **Navigate to User Management**
   - Go to Setup → Users and Permissions → Role
   - Create or edit roles as needed

2. **Assign DocType Permissions**
   - Go to Setup → Users and Permissions → DocType
   - Select DocType and configure permissions
   - Set appropriate permissions for each role

3. **Assign Users to Roles**
   - Go to Setup → Users and Permissions → User
   - Edit user and assign appropriate roles
   - Save changes

### Custom Permission Rules

#### Field-Level Permissions
Some fields have additional restrictions:
- **External Site Settings**: Only System Managers can modify
- **Financial Fields**: Limited to Account Managers and System Managers
- **Technical Parameters**: Restricted to technical roles

#### Document State Permissions
- **Draft Documents**: Creators and assigned roles can edit
- **Submitted Documents**: Only System Managers can cancel/amend
- **Cancelled Documents**: Only System Managers can restore

## Security Considerations

### Data Protection
- Sensitive data (API credentials) restricted to System Managers
- Financial information limited to commercial roles
- Technical data accessible to technical roles

### Audit Trail
- All document changes are tracked
- User actions are logged
- Cross-site operations are monitored

### Access Control
- Role-based access prevents unauthorized data access
- Field-level permissions protect sensitive information
- Document state controls prevent unauthorized modifications

## Troubleshooting Permissions

### Common Issues

**Cannot access DocType**
- Check user role assignments
- Verify DocType permissions
- Ensure module access is granted

**Cannot edit submitted document**
- Only System Managers can modify submitted documents
- Use cancel/amend workflow if needed
- Check document state restrictions

**Missing custom buttons**
- Verify role permissions for DocType
- Check custom button visibility conditions
- Ensure proper role assignments

### Permission Audit

Regular permission audits should include:
1. Review user role assignments
2. Verify DocType permissions
3. Check field-level restrictions
4. Test cross-site access controls
5. Validate audit trail functionality

## Best Practices

### Role Design
- Follow principle of least privilege
- Create specific roles for specific functions
- Avoid overly broad permissions
- Regular review and updates

### User Management
- Assign users to appropriate roles
- Remove access for inactive users
- Regular permission reviews
- Document permission changes

### Security Monitoring
- Monitor access patterns
- Review audit logs regularly
- Track permission changes
- Investigate unusual access
