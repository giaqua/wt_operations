# Water Sample

Water Sample Collection and Analysis Management

## Fields

### Basic Information
| Field | Type | Description |
|-------|------|-------------|
| WWTP Technical Questionnaire | Link | Related WWTP Technical Questionnaire (required) |
| Lead | Link | Associated lead (required) |
| Opportunity | Link | Associated opportunity |
| Date Collected | Date | Date when sample was collected (required) |
| Time Collected | Time | Time when sample was collected |
| Collected By | Link (User) | User who collected the sample |
| Related Visit | Link | Related site visit request |

### Sample Details
| Field | Type | Description |
|-------|------|-------------|
| Sample Type | Select | Type of sample (required) |
| Sample Location | Small Text | Location where sample was collected (required) |
| Sample Point | Data | Specific sampling point |
| Weather Conditions | Select | Weather during collection |
| Ambient Temperature | Float | Temperature during collection (°C) |
| Flow Rate | Float | Flow rate at time of collection (m³/hr) |

### Sample Preservation
| Field | Type | Description |
|-------|------|-------------|
| Preservation Method | Select | Method used to preserve sample |
| Preservation Chemicals | Small Text | Chemicals used for preservation |
| Storage Temperature | Float | Storage temperature (°C) |
| Transport Method | Select | Method of transport to lab |
| Transport Time | Data | Time taken for transport |
| Chain of Custody | Check | Whether chain of custody was maintained |

### Laboratory Details
| Field | Type | Description |
|-------|------|-------------|
| Laboratory Name | Data | Name of testing laboratory |
| Laboratory Contact | Data | Contact person at laboratory |
| Analysis Requested | Small Text | Specific analyses requested |

### Analysis Parameters

#### Basic Parameters
| Field | Type | Description |
|-------|------|-------------|
| pH | Float | pH value (precision: 2) |
| TSS | Float | Total Suspended Solids (mg/L) |
| Turbidity | Float | Turbidity (NTU) |
| Temperature | Float | Temperature (°C) |

#### Chemical Parameters
| Field | Type | Description |
|-------|------|-------------|
| COD | Float | Chemical Oxygen Demand (mg/L) |
| BOD5 | Float | Biochemical Oxygen Demand (mg/L) |
| TDS | Float | Total Dissolved Solids (mg/L) |
| Oil & Grease | Float | Oil and Grease (mg/L) |

#### Nutrients
| Field | Type | Description |
|-------|------|-------------|
| PO4-P | Float | Phosphate Phosphorus (mg/L) |
| TKN | Float | Total Kjeldahl Nitrogen (mg/L) |
| Nitrate | Float | Nitrate (mg/L) |
| Nitrite | Float | Nitrite (mg/L) |

#### Heavy Metals
| Field | Type | Description |
|-------|------|-------------|
| Arsenic | Float | Arsenic (mg/L) |
| Lead | Float | Lead (mg/L) |
| Mercury | Float | Mercury (mg/L) |
| Chromium | Float | Chromium (mg/L) |

#### Biological Parameters
| Field | Type | Description |
|-------|------|-------------|
| E.coli | Float | E.coli (CFU/100mL) |
| Total Coliform | Float | Total Coliform (CFU/100mL) |
| Fecal Coliform | Float | Fecal Coliform (CFU/100mL) |

### Analysis Results
| Field | Type | Description |
|-------|------|-------------|
| Analysis Completed Date | Date | Date when analysis was completed |
| Results Available | Check | Whether results are available |
| Compliance Status | Select | Compliance status of the sample |

### Notes
| Field | Type | Description |
|-------|------|-------------|
| Collection Notes | Small Text | Notes about sample collection |
| Laboratory Notes | Small Text | Notes from laboratory |
| Recommendations | Small Text | Recommendations based on results |

## Features

### Auto-fill from WWTP Technical Questionnaire
- Automatically fills lead, opportunity, and location when WWTP Technical Questionnaire is selected
- Sets appropriate sample type based on wastewater generator type
- Custom button to manually trigger auto-fill

### Compliance Calculation
- Automatic compliance calculation for effluent samples
- Checks against standard parameters (pH: 6-9, TSS: <100 mg/L, BOD5: <30 mg/L)
- Custom button to manually calculate compliance

### Sample Type Management
- Different sample types: Influent, Effluent, Process Water, Sludge, Composite, Grab Sample
- Automatic preservation method suggestions based on sample type
- Validation for chemical preservation requirements

### Data Validation
- Date validation to ensure analysis date is after collection date
- pH value validation (0-14 range)
- Temperature validation with warnings for unusual values
- Parameter-specific validations

### Sample Summary
- Generate comprehensive sample summary
- Include key results and compliance status
- Export-ready format for reporting

## Sample Types

### Influent
- Raw wastewater entering the treatment plant
- Typically requires refrigeration preservation
- Key parameters: BOD5, COD, TSS, pH

### Effluent
- Treated wastewater leaving the treatment plant
- Compliance-critical parameters
- Standard limits: pH 6-9, TSS <100 mg/L, BOD5 <30 mg/L

### Process Water
- Water from intermediate treatment processes
- Used for process optimization
- Parameters vary by treatment stage

### Sludge
- Solid material from treatment processes
- Requires chemical preservation
- Key parameters: Total Solids, Volatile Solids, pH

### Composite Sample
- Mixed sample collected over time
- Represents average conditions
- Requires careful collection protocol

### Grab Sample
- Single sample collected at specific time
- Represents instantaneous conditions
- Used for spot checks

## Compliance Standards

### Effluent Standards (Typical)
- **pH**: 6.0 - 9.0
- **TSS**: < 100 mg/L
- **BOD5**: < 30 mg/L
- **COD**: < 250 mg/L
- **Oil & Grease**: < 10 mg/L

### Heavy Metals (Typical Limits)
- **Arsenic**: < 0.1 mg/L
- **Lead**: < 0.1 mg/L
- **Mercury**: < 0.001 mg/L
- **Chromium**: < 0.1 mg/L

## Integration

### WWTP Technical Questionnaire Integration
- Links to WWTP Technical Questionnaire for context
- Auto-populates relevant fields
- Updates questionnaire when sample collection is completed

### Site Visit Request Integration
- Links to related site visits
- Provides context for sample collection
- Tracks sample collection activities

## Permissions
- **System Manager**: Full access (create, read, write, delete, submit)
- **Site Manager**: Limited access (create, read, write, submit)
- **Lab Technician**: Read and update analysis results
