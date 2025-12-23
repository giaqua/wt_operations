# WWTP Technical Questionnaire - Screen Recording Script

## Video Overview
**Duration**: 15-20 minutes  
**Target Audience**: Users filling out WWTP Technical Questionnaire  
**Format**: Screen recording with voice narration  
**Focus**: Step-by-step form completion guide

---

## Pre-Recording Setup Checklist
- [ ] Clear browser cache and close unnecessary tabs
- [ ] Have sample data prepared for demonstration
- [ ] Ensure good audio quality
- [ ] Set screen resolution to 1920x1080 for clarity
- [ ] Prepare backup data in case of errors

---

## Script Sections

### 1. INTRODUCTION (0:00 - 1:00)

**[Screen Action: Show Frappe login page or dashboard]**

**Narration:**
"Welcome to this tutorial on how to fill out the WWTP Technical Questionnaire form. I'm [Your Name], and today I'll walk you through each section of this comprehensive form step by step. This questionnaire is designed to collect detailed information about wastewater treatment requirements, facility specifications, and project parameters.

**[Screen Action: Navigate to WWTP Technical Questionnaire]**

Before we begin, let me show you where to find this form. Navigate to the WT Operations module and select 'WWTP Technical Questionnaire' from the list. Click on 'New' to create a fresh questionnaire.

**[Screen Action: Click 'New' button]**

The form will open with several sections that we'll complete systematically. Let's start with the basic information section."

---

### 2. BASIC INFORMATION SECTION (1:00 - 3:00)

**[Screen Action: Focus on the top section of the form]**

**Narration:**
"Let's begin with the basic information section at the top of the form. This section contains essential project details.

**[Screen Action: Click on Lead field]**

First, we have the Lead field, which is required. This should be linked to an existing lead in your system. Click on the dropdown and select the appropriate lead for this project.

**[Screen Action: Select a lead from dropdown]**

**[Screen Action: Click on Date field]**

The Date field defaults to today's date, but you can change it if needed. This represents when the questionnaire is being completed.

**[Screen Action: Click on 'By' field]**

The 'By' field should be set to the user completing the questionnaire - that's you.

**[Screen Action: Check Site Visit Required checkbox]**

Now, let's look at the checkboxes. 'Site Visit Required' - check this if you need our team to visit the site for assessment.

**[Screen Action: Check Sample Collection Required checkbox]**

'Sample Collection Required' - check this if you need us to collect wastewater samples for analysis.

**[Screen Action: Click on Opportunity field]**

The Opportunity field will automatically filter based on the lead you selected. If there's a related opportunity, select it here.

Let's move on to the main technical sections."

---

### 3. LANDSCAPE AND FACILITY SECTION (3:00 - 6:00)

**[Screen Action: Scroll to Landscape and Facility section]**

**Narration:**
"This section collects information about the physical characteristics and requirements of your wastewater treatment facility.

**[Screen Action: Click on Wastewater Generator Type dropdown]**

First, we have the Wastewater Generator Type, which is required. This tells us what kind of wastewater we'll be treating. Let me show you the options:

**[Screen Action: Open dropdown to show options]**

- Domestic: for residential wastewater
- Industrial: for manufacturing facilities
- Slaughterhouse: for meat processing plants
- Concrete: for concrete production facilities
- Oil and Gas: for petroleum industry
- Leachate: for landfill leachate treatment
- Special Case: for unique applications

**[Screen Action: Select 'Industrial']**

For this demonstration, I'll select 'Industrial'.

**[Screen Action: Click on Capacity field]**

Next, we have Capacity in cubic meters per day. This is a required field. Enter the daily treatment capacity your facility needs. For example, let's enter 1000.

**[Screen Action: Enter '1000' in Capacity field]**

**[Screen Action: Click on 'Is it new WWTP or an upgrade' field]**

This field asks whether you're building a new facility or upgrading an existing one. Enter 'New WWTP' or 'Upgrade' as appropriate.

**[Screen Action: Enter 'New WWTP']**

**[Screen Action: Click on Number of Streams field]**

Here's an important field - Number of Streams. When you enter a number here, the system will automatically create that many rows in the influent stream table below. Let's enter 2.

**[Screen Action: Enter '2' in Number of Streams field]**

**[Screen Action: Show how table rows are automatically created]**

Notice how the system automatically created 2 rows in the influent stream table, labeled 'Stream 1' and 'Stream 2'. This is one of the smart features of this form.

**[Screen Action: Fill in optional fields]**

Let's fill in some optional fields:

**[Screen Action: Click on footprint field]**

Available footprint - enter the space available for the WWTP in square meters.

**[Screen Action: Enter '500']**

**[Screen Action: Click on location field]**

Location - describe where the WWTP will be located.

**[Screen Action: Enter 'Industrial Zone, Block A']**

**[Screen Action: Click on available equipment field]**

Available equipment - list any existing tanks, pumps, or other equipment.

**[Screen Action: Enter 'Existing pump station, 2 storage tanks']**

**[Screen Action: Click on site condition field]**

Design of site condition - describe any constraints or special conditions.

**[Screen Action: Enter 'Flat terrain, good access, power available']**

**[Screen Action: Click on attach field]**

You can also attach relevant documents like site plans or drawings here.

Now let's move to the design parameters."

---

### 4. DESIGN PARAMETERS SECTION (6:00 - 8:00)

**[Screen Action: Scroll to Design Parameters section]**

**Narration:**
"The Design Parameters section defines the operational characteristics of your wastewater treatment plant.

**[Screen Action: Click on Daily Flow field]**

Daily Flow - enter the maximum, minimum, or range of daily flow in cubic meters per day. For example, let's enter '800-1200'.

**[Screen Action: Enter '800-1200']**

**[Screen Action: Click on Operation Hours field]**

Operation Hours - how many hours per day will the plant operate? Let's enter 24 for continuous operation.

**[Screen Action: Enter '24']**

**[Screen Action: Click on Average Hourly Flow field]**

Average Hourly Flow - this can be calculated by dividing daily flow by operation hours. With 1000 m³/day and 24 hours, that's about 42 m³/hr.

**[Screen Action: Enter '42']**

**[Screen Action: Click on Min Flow field]**

Min Flow - the minimum daily flow rate. Let's enter 400.

**[Screen Action: Enter '400']**

**[Screen Action: Click on Peak Factor field]**

Peak Factor - this multiplier accounts for peak flow conditions. Typical values are 1.5 to 3.0. Let's enter 2.0.

**[Screen Action: Enter '2.0']**

**[Screen Action: Click on Peak Hours field]**

Peak Hours - duration of peak flow conditions. Let's enter 4 hours.

**[Screen Action: Enter '4']**

These parameters help us design a system that can handle both normal and peak conditions."

---

### 5. INFLUENT QUALITY SECTION (8:00 - 12:00)

**[Screen Action: Scroll to Influent Quality section]**

**Narration:**
"This section captures the characteristics of your incoming wastewater streams. Remember, we set the number of streams to 2, so we have two rows to fill.

**[Screen Action: Click on first stream row]**

Let's start with Stream 1. I'll fill in the key parameters:

**[Screen Action: Click on pH field for Stream 1]**

pH - typical industrial wastewater pH ranges from 6 to 9. Let's enter 7.5.

**[Screen Action: Enter '7.5']**

**[Screen Action: Click on TSS field for Stream 1]**

TSS - Total Suspended Solids in mg/L. Industrial wastewater typically has 200-500 mg/L. Let's enter 300.

**[Screen Action: Enter '300']**

**[Screen Action: Click on COD field for Stream 1]**

COD - Chemical Oxygen Demand. For industrial wastewater, this might be 500-2000 mg/L. Let's enter 800.

**[Screen Action: Enter '800']**

**[Screen Action: Click on BOD5 field for Stream 1]**

BOD5 - Biochemical Oxygen Demand. This is typically 40-60% of COD. Let's enter 400.

**[Screen Action: Enter '400']**

**[Screen Action: Click on Temperature field for Stream 1]**

Temperature - wastewater temperature in Celsius. Normal range is 20-30°C. Let's enter 25.

**[Screen Action: Enter '25']**

**[Screen Action: Click on second stream row]**

Now let's fill Stream 2 with different characteristics to show variation:

**[Screen Action: Fill Stream 2 with different values]**

Stream 2 might have different characteristics - perhaps higher pH at 8.5, higher TSS at 500 mg/L, and higher COD at 1200 mg/L.

**[Screen Action: Show how to add more streams if needed]**

If you need more streams, simply change the Number of Streams field, and the system will automatically add or remove rows as needed.

**[Screen Action: Demonstrate changing number of streams]**

Let me change it to 3 streams to show how it works.

**[Screen Action: Change to '3' and show new row]**

See how Stream 3 was automatically added? This is the smart functionality we implemented.

**[Screen Action: Change back to '2']**

Let me change it back to 2 for our demonstration."

---

### 6. EFFLUENT QUALITY SECTION (12:00 - 14:00)

**[Screen Action: Scroll to Effluent Quality section]**

**Narration:**
"Now we define the required quality standards for your treated wastewater.

**[Screen Action: Click on pH field]**

Effluent pH - typically needs to be between 6.5 and 8.5. Let's enter 7.0.

**[Screen Action: Enter '7.0']**

**[Screen Action: Click on TSS field]**

Effluent TSS - maximum allowable suspended solids. For most applications, this is 30 mg/L or less. Let's enter 20.

**[Screen Action: Enter '20']**

**[Screen Action: Click on BOD5 field]**

Effluent BOD5 - maximum allowable biochemical oxygen demand. For discharge, this is often 30 mg/L or less. Let's enter 25.

**[Screen Action: Enter '25']**

**[Screen Action: Click on COD field]**

Effluent COD - maximum allowable chemical oxygen demand. Let's enter 100.

**[Screen Action: Enter '100']**

**[Screen Action: Click on Target Effluent Type dropdown]**

**[Screen Action: Open dropdown to show options]**

Most importantly, select your target effluent type:

**[Screen Action: Select 'Irrigation (restricted)']**

- Unusable (safe discharge): Safe discharge to environment
- Irrigation (restricted): Limited agricultural use
- Irrigation (unrestricted): Full agricultural use
- Industrial - Washing: Industrial washing applications
- Industrial - Cooling: Industrial cooling applications
- Industrial - Manufacturing: Manufacturing process water

For this example, I'll select 'Irrigation (restricted)'.

**[Screen Action: Fill remaining effluent parameters quickly]**

Let me quickly fill in the remaining parameters with typical values for irrigation use."

---

### 7. ROLES AND RESPONSIBILITIES SECTION (14:00 - 16:00)

**[Screen Action: Scroll to Roles and Responsibilities section]**

**Narration:**
"This section automatically populates with all available scope of work items. This is another smart feature of the form.

**[Screen Action: Show populated table]**

As you can see, the table is already populated with various scope of work items. Each row represents a different aspect of the project.

**[Screen Action: Click on first row's Responsible field]**

For each item, you need to specify who's responsible. Click on the Responsible dropdown and select either 'GI' for Government Institution or 'Customer'.

**[Screen Action: Select 'Customer']**

**[Screen Action: Click on Not Required checkbox]**

If an item doesn't apply to your project, check the 'Not Required' checkbox.

**[Screen Action: Click on Remarks field]**

You can add specific remarks for any item to provide clarification.

**[Screen Action: Enter 'To be confirmed with client']**

**[Screen Action: Show Refresh Scope of Work button]**

Notice the 'Refresh Scope of Work' button at the top. This updates the list if new scope of work items have been added to the system.

**[Screen Action: Demonstrate selecting different responsibilities]**

Let me show you how to assign different responsibilities to different items. Some might be GI responsibility, others Customer responsibility."

---

### 8. FORM VALIDATION AND SUBMISSION (16:00 - 18:00)

**[Screen Action: Scroll to top of form]**

**Narration:**
"Before submitting, let's review our form for completeness and accuracy.

**[Screen Action: Check required fields]**

Let me verify that all required fields are completed:
- Lead: ✓ Selected
- Wastewater Generator Type: ✓ Selected
- Capacity: ✓ Entered
- Number of Streams: ✓ Set
- Is it new WWTP: ✓ Specified

**[Screen Action: Save the form]**

Let's save our work first by pressing Ctrl+S or clicking the Save button.

**[Screen Action: Click Save button]**

**[Screen Action: Show successful save message]**

Great! The form has been saved successfully.

**[Screen Action: Show Submit button]**

Now we can submit the form if all information is complete and accurate.

**[Screen Action: Click Submit button]**

**[Screen Action: Show submission confirmation]**

The form has been submitted and will be reviewed by our technical team."

---

### 9. TROUBLESHOOTING AND TIPS (18:00 - 19:30)

**[Screen Action: Show form with some errors]**

**Narration:**
"Let me show you some common issues and how to resolve them:

**[Screen Action: Show validation error]**

If you see validation errors, check that all required fields are completed and that numeric values are reasonable.

**[Screen Action: Demonstrate fixing calculation errors]**

For flow calculations, ensure consistency. For example, if daily flow is 1000 m³/day and operation hours are 24, then average hourly flow should be about 42 m³/hr.

**[Screen Action: Show how to handle missing data]**

If you don't have certain data, you can leave optional fields blank or use the remarks field to explain why data is unavailable.

**[Screen Action: Show the refresh functionality]**

Remember to use the refresh buttons for both the influent streams and roles tables if you need to update the data."

---

### 10. CONCLUSION (19:30 - 20:00)

**[Screen Action: Show completed form]**

**Narration:**
"That concludes our walkthrough of the WWTP Technical Questionnaire form. Here's a summary of what we covered:

1. Basic information and project details
2. Landscape and facility specifications
3. Design parameters for flow rates
4. Influent quality characteristics for multiple streams
5. Effluent quality requirements
6. Roles and responsibilities assignment

The form includes several smart features:
- Automatic stream creation based on number of streams
- Auto-population of scope of work items
- Real-time validation and refresh capabilities

Remember to save your work frequently and review all information before submission. If you have any questions or need assistance, please contact our technical support team.

Thank you for watching this tutorial!"

---

## Post-Recording Checklist
- [ ] Review recording for clarity and completeness
- [ ] Check audio quality throughout
- [ ] Verify all screen actions are visible
- [ ] Ensure timing matches script
- [ ] Test video playback on different devices
- [ ] Prepare video description and tags

---

## Technical Notes for Recording
- **Screen Resolution**: 1920x1080 recommended
- **Frame Rate**: 30fps minimum
- **Audio**: Clear narration, no background noise
- **Browser**: Use Chrome or Firefox for best compatibility
- **Cursor**: Ensure cursor is visible and moves smoothly
- **Zoom**: Use browser zoom at 100% for best clarity

---

## Sample Data for Demonstration
- **Lead**: [Use existing lead from system]
- **Capacity**: 1000 m³/day
- **Streams**: 2
- **Daily Flow**: 800-1200 m³/day
- **Operation Hours**: 24 hours
- **Peak Factor**: 2.0
- **Effluent Type**: Irrigation (restricted)

This script provides a comprehensive guide for creating an effective screen recording tutorial that will help users understand and complete the WWTP Technical Questionnaire form successfully.
