# WT Operations (WWTP) Module Documentation

## Overview

The WT Operations module manages the complete lifecycle of wastewater treatment plant (WWTP) projects from initial technical assessment through customer proposals and implementation. This system supports both standalone operations and cross-site integrations for multi-location organizations.

## Key Features

- **Technical Assessment**: Comprehensive WWTP Technical Questionnaires with automated effluent quality parameter population
- **Site Management**: Site Visit Requests, Site Visits, and Water Sample collection workflows
- **Proposal Generation**: Automated Technical Proposals and Customer Proposals with multiple commercial options
- **Cross-Site Integration**: Seamless data synchronization between Site 1 and Site 2 installations
- **Compliance Tracking**: Lab Test Results and regulatory compliance monitoring
- **Project Management**: Request for Proposals and Scope of Work management

## Prerequisites

- ERPNext/Frappe framework installed
- WT Operations app installed and configured
- Appropriate user roles assigned (System Manager, Site Manager, Operations Technician, Operations Manager)
- Master data configured (Scope of Work, Wastewater Generator Types, Treatment Parameters)

## Quick Start

1. **Configure Master Data**: Set up Scope of Work, Wastewater Generator Types, and Treatment Parameters
2. **Set Up Cross-Site Integration**: Configure External Site Settings if using multi-site setup
3. **Create Your First Project**: Start with a Lead → WWTP Technical Questionnaire → Site Visit Request workflow
4. **Review Permissions**: Ensure users have appropriate role assignments

## Documentation Structure

- **[Getting Started](getting-started.md)**: User roles, navigation, and common UI elements
- **[Workflows](workflows/)**: End-to-end business processes
- **[DocTypes](doctypes/)**: Detailed documentation for each document type
- **[Integrations](integrations/)**: Cross-site synchronization and API documentation
- **[Setup](setup/)**: Installation, configuration, and permissions
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions

## Core Workflows

### Primary Workflow
**Lead → WWTP Technical Questionnaire → Site Visit Request → Site Visit → Water Sample → Lab Test Result → WWTP Technical Proposal → Customer Proposal → Request For Proposal**

### Alternative Entry Points
- **Ad-hoc Site Visit**: Start from Site Visit Request → Link to Technical Questionnaire
- **Lab-First Approach**: Start from Water Sample → Link to Site Visit or Technical Questionnaire

## Support

For technical support or questions about this module, refer to:
- [Troubleshooting Guide](troubleshooting.md)
- [Setup Documentation](setup/)
- System Administrator for role and permission issues
