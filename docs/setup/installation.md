# Installation

## Prerequisites

- ERPNext/Frappe framework installed and running
- Python 3.6+ environment
- MySQL/MariaDB database
- Node.js and npm (for frontend assets)

## Installation Steps

### 1. Install the WT Operations App

```bash
# Navigate to your Frappe bench
cd /path/to/your/frappe-bench

# Install the WT Operations app
bench get-app wt_operations

# Install the app on your site
bench --site your-site-name install-app wt_operations
```

### 2. Run Database Migrations

```bash
# Run any pending migrations
bench --site your-site-name migrate
```

### 3. Build Frontend Assets

```bash
# Build JavaScript and CSS assets
bench build --app wt_operations
```

### 4. Restart Services

```bash
# Restart Frappe services
bench restart
```

## Post-Installation Configuration

### 1. Create Master Data

Before using the system, create the following master data:

- **Scope of Work** records
- **Wastewater Generator Type** records  
- **Treatment Parameter** records
- **Parameter Type** records
- **Tank Type** records

### 2. Set Up User Roles

Configure the following roles:
- System Manager
- Site Manager
- Operations Technician
- Operations Manager
- Account Manager

### 3. Configure System Settings

- Set default company
- Configure naming series
- Set up email settings for notifications

### 4. Cross-Site Integration (Optional)

If using multi-site setup:
- Configure External Site Settings
- Test API connections
- Set up sync schedules

## Verification

### 1. Check DocTypes

Verify all DocTypes are created:
- WWTP Technical Questionnaire
- WWTP Technical Proposal
- Site Visit Request
- Site Visit
- Water Sample
- Lab Test Result
- Customer Proposal
- Request for Proposal
- Scope of Work
- Wastewater Generator Type
- External Site Settings

### 2. Test Basic Functionality

1. Create a test Lead
2. Create a WWTP Technical Questionnaire
3. Test auto-fill functions
4. Create a Site Visit Request
5. Verify permissions and access

### 3. Test Cross-Site Integration (If Applicable)

1. Configure External Site Settings
2. Test connection
3. Create a Site Visit Request
4. Test sync functionality

## Troubleshooting Installation Issues

### Common Issues

**App installation fails**
- Check Frappe bench version compatibility
- Verify database connectivity
- Check file permissions

**Migration errors**
- Review error messages
- Check database schema
- Contact support if needed

**Frontend build fails**
- Check Node.js version
- Clear npm cache
- Rebuild assets

**Permission errors**
- Check file ownership
- Verify Frappe user permissions
- Restart services

## Support

For installation support:
1. Check [Troubleshooting Guide](../troubleshooting.md)
2. Review Frappe documentation
3. Contact system administrator
4. Submit support ticket if needed
