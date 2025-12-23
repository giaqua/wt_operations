# Customer Proposal

## Purpose

The Customer Proposal is a comprehensive commercial document that presents technical solutions with pricing and commercial terms to customers. It includes multiple commercial options (Supply & Installation, Design-Build, BOOT) and serves as the basis for customer decision-making.

## When to Use

- **Commercial Presentations**: Present commercial proposals to customers
- **Multiple Options**: Offer different commercial models
- **Pricing Proposals**: Include detailed pricing and terms
- **Contract Basis**: Foundation for contract negotiations

## Status & Workflow

### Document States
- **Draft (0)**: Proposal being prepared
- **Submitted (1)**: Proposal completed and submitted
- **Cancelled (2)**: Proposal cancelled

### Workflow Transitions
- **Draft → Submitted**: Complete proposal and submit
- **Submitted → Cancelled**: Cancel submitted proposal
- **Cancelled → Draft**: Restore cancelled proposal

## Key Fields

| Label | Fieldname | Type | Notes |
|-------|-----------|------|-------|
| Customer | `customer` | Link | Required - Final customer |
| Customer Contact | `customer_contact` | Link | Customer contact person |
| Lead | `lead` | Link | Link to Lead |
| Opportunity | `opportunity` | Link | Link to Opportunity |
| Technical Proposal | `wwtp_technical_proposal` | Link | Required - Link to Technical Proposal |
| Technical Questionnaire | `wwtp_technical_questionnaire` | Link | Auto-filled from Technical Proposal |
| Site Visit | `site_visit` | Link | Auto-filled from Technical Proposal |
| Water Sample | `water_sample` | Link | Auto-filled from Technical Proposal |
| Issue Date | `issue_date` | Date | Required - Proposal issue date |
| Valid Up To | `valid_up_to` | Date | Required - Proposal validity date |
| Account Manager | `account_manager` | Link | Account manager |
| Prepared By | `prepared_by` | Link | User who prepared proposal |
| Technical Manager | `technical_manager` | Link | Technical manager |
| Project Title | `project_title` | Data | Auto-filled from Technical Proposal |
| Project Description | `project_description` | Text Editor | Auto-filled from Technical Proposal |
| Wastewater Generator Type | `wastewater_generator_type` | Data | Auto-filled from Technical Proposal |
| Design Capacity | `design_capacity` | Float | Auto-filled from Technical Proposal |
| Current Capacity | `current_capacity` | Float | Auto-filled from Technical Proposal |
| Treatment Technology | `treatment_technology` | Data | Auto-filled from Technical Proposal |
| Process Description | `process_description` | Text Editor | Auto-filled from Technical Proposal |
| Treatment Stages | `treatment_stages` | Text Editor | Auto-filled from Technical Proposal |
| Scope of Work | `scope_of_work` | Text Editor | Scope of work details |
| Termination Points | `termination_points` | Text Editor | Termination points |
| Exclusions | `exclusions` | Text Editor | Exclusions |
| Daily Flow | `daily_flow` | Data | Auto-filled from Technical Proposal |
| Operation Hours | `operation_hours` | Data | Auto-filled from Technical Proposal |
| Average Hourly Flow | `average_hourly_flow` | Data | Auto-filled from Technical Proposal |
| Site Conditions Summary | `site_conditions_summary` | Text Editor | Auto-filled from Technical Proposal |
| Site Accessibility Rating | `site_accessibility_rating` | Select | Auto-filled from Technical Proposal |
| Power Availability Rating | `power_availability_rating` | Select | Auto-filled from Technical Proposal |
| Ground Conditions Rating | `ground_conditions_rating` | Select | Auto-filled from Technical Proposal |
| Environmental Impact Assessment | `environmental_impact_assessment` | Text Editor | Auto-filled from Technical Proposal |
| Influent Characteristics | `influent_characteristics` | Text Editor | Auto-filled from Technical Proposal |
| Effluent Requirements | `effluent_requirements` | Text Editor | Auto-filled from Technical Proposal |
| Treatment Challenges | `treatment_challenges` | Text Editor | Auto-filled from Technical Proposal |
| Compliance Status | `compliance_status` | Select | Auto-filled from Technical Proposal |
| Civil Requirements | `civil_requirements` | Text Editor | Auto-filled from Technical Proposal |
| Site Preparation Needs | `site_preparation_needs` | Text Editor | Auto-filled from Technical Proposal |
| Utility Connections | `utility_connections` | Text Editor | Auto-filled from Technical Proposal |
| Equalization Tank Minimum Capacity | `equalization_tank_minimum_capacity` | Data | Auto-filled from Technical Proposal |
| Sludge Holding Tank Minimum Capacity | `sludge_holding_tank_minimum_capacity` | Data | Auto-filled from Technical Proposal |
| Product Tank Minimum Capacity | `product_tank_minimum_capacity` | Data | Auto-filled from Technical Proposal |
| Concrete Pads for STP | `concrete_pads_for_stp` | Data | Auto-filled from Technical Proposal |
| Design Period | `design_period` | Int | Auto-filled from Technical Proposal |
| Procurement Period | `procurement_period` | Int | Auto-filled from Technical Proposal |
| Construction Period | `construction_period` | Int | Auto-filled from Technical Proposal |
| Commissioning Period | `commissioning_period` | Int | Auto-filled from Technical Proposal |
| Total Implementation Time | `total_implementation_time` | Int | Auto-filled from Technical Proposal |
| Option 1 Title | `option_1_title` | Data | Default: "Supply & Installation" |
| Option 2 Title | `option_2_title` | Data | Default: "Design-Build" |
| Option 3 Title | `option_3_title` | Data | Default: "BOOT (Build-Own-Operate-Transfer)" |
| BOOT Concession Period | `boot_concession_period` | Int | BOOT concession period (years) |
| BOOT Operation Period | `boot_operation_period` | Int | BOOT operation period (years) |
| BOOT Transfer Terms | `boot_transfer_terms` | Text Editor | BOOT transfer terms |
| Warranty Text | `warranty_text` | Text Editor | Warranty terms |
| Maintenance Requirements | `maintenance_requirements` | Text Editor | Auto-filled from Technical Proposal |
| Chemical Consumption | `chemical_consumption` | Text Editor | Auto-filled from Technical Proposal |
| Energy Consumption | `energy_consumption` | Text Editor | Auto-filled from Technical Proposal |
| Environmental Permits Required | `environmental_permits_required` | Text Editor | Auto-filled from Technical Proposal |
| Discharge Permit Status | `discharge_permit_status` | Select | Auto-filled from Technical Proposal |
| Environmental Monitoring | `environmental_monitoring` | Text Editor | Auto-filled from Technical Proposal |
| Technical Risks | `technical_risks` | Text Editor | Auto-filled from Technical Proposal |
| Environmental Risks | `environmental_risks` | Text Editor | Auto-filled from Technical Proposal |
| Mitigation Strategies | `mitigation_strategies` | Text Editor | Auto-filled from Technical Proposal |

## Child Tables & Relations

### Roles and Responsibilities Table
- **Purpose**: Define roles and responsibilities for project scope
- **Auto-population**: From Technical Proposal
- **Fields**: Scope of Work, Responsible, Not Required, Remarks

### Influent Quality Table
- **Purpose**: Expected influent quality parameters
- **Fields**: Parameter, Expected Value, Unit, Notes

### Proposal Effluent Quality Table
- **Purpose**: Guaranteed effluent quality parameters
- **Fields**: Parameter, Guaranteed Value, Unit, Notes

### Option 1 Table (Supply & Installation)
- **Purpose**: Equipment and services for Option 1
- **Fields**: Item Code, Item Name, Description, Quantity, Rate, Amount

### Option 2 Table (Design-Build)
- **Purpose**: Equipment and services for Option 2
- **Fields**: Item Code, Item Name, Description, Quantity, Rate, Amount

### Option 3 Table (BOOT)
- **Purpose**: Equipment and services for BOOT option
- **Fields**: Item Code, Item Name, Description, Quantity, Rate, Amount

### Operation and Maintenance Table
- **Purpose**: Ongoing operation and maintenance services
- **Fields**: Item Code, Item Name, Description, Quantity, Rate, Amount

## Actions & Automations

### Auto-Fill Functions
- **From Technical Proposal**: Auto-populate all technical details
- **Roles and Responsibilities**: Auto-populate from Technical Proposal
- **Proposal Summary**: Generate proposal summary

### Custom Buttons
- **Auto-fill from Technical Proposal**: Populate data from Technical Proposal
- **Fetch Roles & Responsibilities**: Populate roles table
- **Proposal Summary**: Generate proposal summary

### Client Scripts
- **File**: `customer_proposal.js`
- **Functions**:
  - `wwtp_technical_proposal`: Auto-fill from Technical Proposal
  - `boot_concession_period`: Validate BOOT periods
  - `boot_operation_period`: Validate BOOT periods
  - `valid_up_to`: Validate validity period
  - `issue_date`: Auto-suggest validity period

### Server Methods
- **File**: `customer_proposal.py`
- **Methods**:
  - `auto_fill_from_technical_proposal`: Auto-populate from Technical Proposal
  - `populate_roles_and_responsibilities_from_tp`: Populate roles table
  - `generate_proposal_summary`: Generate proposal summary

## Permissions & Roles

| Role | Create | Read | Update | Delete | Submit |
|------|--------|------|--------|--------|--------|
| System Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Site Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Operations Technician | - | ✓ | - | - | - |
| Account Manager | ✓ | ✓ | ✓ | ✓ | ✓ |

## Data Validation

### Required Fields
- Customer must be selected
- Technical Proposal must be linked
- Issue date must be set
- Valid up to date must be set
- Account manager must be assigned

### Business Rules
- Valid up to date must be after issue date
- BOOT operation period must be ≤ concession period
- All commercial options must have items if selected
- Warranty terms must be specified

### Validation Methods
- **Client-side**: Real-time validation in forms
- **Server-side**: Validation on save and submit
- **Cross-field**: Validation between related fields

## Common Tasks

### Creating a Customer Proposal
1. Navigate to WT Operations → Customer Proposal
2. Click "New" to create new proposal
3. Select Customer from dropdown
4. Link to Technical Proposal
5. Use "Auto-fill from Technical Proposal" button
6. Complete commercial details
7. Add commercial options (1, 2, 3)
8. Define terms and conditions
9. Review and submit

### Auto-Filling from Technical Proposal
1. Select Technical Proposal
2. Click "Auto-fill from Technical Proposal" button
3. System automatically populates:
   - Project details
   - Technical specifications
   - Site conditions
   - Implementation timeline
   - Roles and responsibilities
4. Review and customize as needed

### Setting Up Commercial Options
1. **Option 1 (Supply & Installation)**:
   - Add equipment items
   - Set pricing
   - Define terms
2. **Option 2 (Design-Build)**:
   - Add design-build items
   - Set pricing
   - Define terms
3. **Option 3 (BOOT)**:
   - Add BOOT items
   - Set concession and operation periods
   - Define transfer terms

### BOOT Configuration
1. Set BOOT concession period
2. Set BOOT operation period
3. Ensure operation period ≤ concession period
4. Define transfer terms
5. Add BOOT-specific items

## Commercial Options

### Option 1: Supply & Installation
- **Description**: Equipment supply and installation services
- **Advantages**: Lower upfront cost, customer control
- **Disadvantages**: Customer responsible for operation
- **Suitable for**: Customers with technical expertise

### Option 2: Design-Build
- **Description**: Complete design and construction services
- **Advantages**: Single point of responsibility, faster delivery
- **Disadvantages**: Higher upfront cost, vendor dependency
- **Suitable for**: Customers wanting turnkey solution

### Option 3: BOOT (Build-Own-Operate-Transfer)
- **Description**: Build, own, operate, and transfer model
- **Advantages**: No upfront investment, guaranteed performance
- **Disadvantages**: Higher long-term cost, vendor dependency
- **Suitable for**: Customers wanting performance guarantee

## Tips & Pitfalls

### Best Practices
- **Use Auto-Fill**: Leverage auto-fill functions for consistency
- **Complete All Options**: Ensure all commercial options are complete
- **Validate BOOT Terms**: Check BOOT period relationships
- **Review Terms**: Review all terms and conditions
- **Add Comments**: Add comments for special requirements

### Common Issues
- **Missing Auto-Fill**: Ensure Technical Proposal is linked
- **BOOT Validation**: Check BOOT period relationships
- **Date Validation**: Ensure validity period is correct
- **Commercial Options**: Ensure all options have items

### Troubleshooting
- **Auto-Fill Not Working**: Check Technical Proposal linkage
- **BOOT Validation Errors**: Check BOOT period relationships
- **Date Validation Errors**: Ensure valid up to > issue date
- **Commercial Option Issues**: Verify all options have items
