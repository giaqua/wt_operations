# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

import frappe
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from frappe.utils import getdate, today
import json
from frappe.utils.data import nowdate



class EmployeeProjectAllocationTool(Document):
    @frappe.whitelist()
    def process_salary_allocation(self):
        """Process all employee allocations and create consolidated entries"""
        if not self.to_date:
            frappe.throw(_("Please set Target Date first"))
        
        if not self.department:
            frappe.throw(_("Please select Department first"))
        
        # Clear existing allocations
        self.set('employee_project_allocation_amounts', [])
        
        # Get all employee allocations for this tool
        employee_allocations = frappe.get_all(
            'Employee Project Allocation',
            filters={
                'employee_project_allocation_tool': self.name,
                'docstatus': 0
            },
            fields=['name', 'employee', 'employee_name', 'from_date', 'to_date']
        )
        
        if not employee_allocations:
            frappe.throw(_("No employee allocations found for this tool"))
        
        # Process each employee
        all_project_allocations = {}
        
        for emp_alloc in employee_allocations:
            # Get last salary slip before or on target date
            salary_slip = self.get_last_salary_slip(emp_alloc.employee, self.to_date)
            
            if not salary_slip:
                frappe.msgprint(_("No salary slip found for employee {0} before {1}").format(
                    emp_alloc.employee_name, self.to_date
                ), alert=True)
                continue
            
            # Get employee's allocation percentages with activity
            employee_percentages = self.get_employee_allocation_percentages(emp_alloc.name)
            
            if not employee_percentages:
                continue
            
            # Get salary components from the slip
            components = self.get_salary_components_from_slip(salary_slip.name)
            
            # Calculate allocated amounts for each project
            for component in components:
                for project_percentage in employee_percentages:
                    project = project_percentage['project']
                    activity = project_percentage['activity']
                    percentage = project_percentage['percentage']
                    allocated_amount = (component['amount'] * percentage) / 100
                    
                    if allocated_amount > 0:
                        # Include activity in the key to separate Operation and Installation
                        key = f"{project}_{activity}_{component['salary_component']}"
                        
                        if key not in all_project_allocations:
                            all_project_allocations[key] = {
                                'project': project,
                                'activity': activity,  # Added activity field
                                'salary_component': component['salary_component'],
                                'account': component.get('account'),
                                'amount': 0,
                                'employee_count': 0,
                                'details': []
                            }
                        
                        all_project_allocations[key]['amount'] += allocated_amount
                        all_project_allocations[key]['employee_count'] += 1
                        all_project_allocations[key]['details'].append({
                            'employee': emp_alloc.employee,
                            'employee_name': emp_alloc.employee_name,
                            'activity': activity,
                            'percentage': percentage,
                            'component_amount': component['amount'],
                            'allocated_amount': allocated_amount
                        })
        
        # Add to child table
        for key, data in all_project_allocations.items():
            self.append('employee_project_allocation_amounts', {
                'project': data['project'],
                'activity': data.get('activity'),  # Include activity in child table
                'salary_component': data['salary_component'],
                'account': data['account'],
                'amount': data['amount'],
                'employee_count': data['employee_count'],
                'allocation_details': frappe.as_json(data['details'])
            })
        
        self.save()
        return {
            'status': 'success',
            'message': f"Processed {len(all_project_allocations)} allocation entries",
            'allocations': all_project_allocations
        }
    
    def get_last_salary_slip(self, employee, to_date):
        """Get the last salary slip before or on target date"""
        last_slip = frappe.db.get_value(
            'Salary Slip',
            {
                'employee': employee,
                'docstatus': 1,
                'start_date': ['<=', to_date]
            },
            ['name', 'start_date', 'end_date', 'gross_pay', 'net_pay'],
            order_by='start_date desc'
        )
        
        if last_slip:
            return frappe.get_doc('Salary Slip', last_slip[0] if isinstance(last_slip, tuple) else last_slip)
        return None
    
    def get_employee_allocation_percentages(self, allocation_name):
        """Get project allocation percentages for an employee with activity"""
        allocation = frappe.get_doc('Employee Project Allocation', allocation_name)
        percentages = []
        
        for detail in allocation.employee_project_allocation_details:
            if detail.percentage and detail.percentage > 0:
                percentages.append({
                    'project': detail.project,
                    'activity': detail.activity,  # Include activity
                    'percentage': detail.percentage
                })
        
        return percentages
    
    def get_salary_components_from_slip(self, salary_slip_name):
        """Get all earning components from salary slip with their accounts"""
        salary_slip = frappe.get_doc('Salary Slip', salary_slip_name)
        components = []
        
        # Get earnings
        for earning in salary_slip.earnings:
            if earning.amount and earning.amount > 0:
                # Get the account from salary component
                account = frappe.db.get_all('Salary Component Account', {'parent': earning.salary_component}, 'account')
                account = account[0].account if account else None
                
                components.append({
                    'salary_component': earning.salary_component,
                    'amount': earning.amount,
                    'type': 'Earning',
                    'account': account
                })
        
        # Optionally include deductions (with negative sign)
        for deduction in salary_slip.deductions:
            if deduction.amount and deduction.amount > 0:
                account = frappe.db.get_all('Salary Component Account', {'parent': deduction.salary_component}, 'account')
                account = account[0].account if account else None
                
                components.append({
                    'salary_component': deduction.salary_component,
                    'amount': -deduction.amount,  # Negative for deductions
                    'type': 'Deduction',
                    'account': account
                })
        
        return components

    @frappe.whitelist()
    def create_journal_entry_from_allocations(self):
        """Create journal entry from processed salary allocations child table"""
        if not self.employee_project_allocation_amounts:
            frappe.throw(_("No processed salary allocations found. Please run 'Process Salary Allocation' first."))
        
        # Check if journal entry already exists
        if self.last_journal_entry:
            frappe.msgprint(_("Journal Entry {0} already created. Create a new one?").format(self.last_journal_entry))
        
        # Create Journal Entry
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "posting_date": getdate(nowdate()),
            "company": frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company"),
            "user_remark": f"Salary allocation for {self.department} department - Tool: {self.name}",
            "accounts": []
        })
        
        # Create entries from each row in employee_project_allocation_amounts
        for alloc in self.employee_project_allocation_amounts:
            if alloc.amount and alloc.amount > 0:
                # Build project name with activity
                project_display = f"{alloc.project} ({alloc.activity})" if alloc.activity else alloc.project
                
                # Debit entry using account, amount, project, and cost center from child table
                je.append("accounts", {
                    "account": alloc.account,
                    "debit_in_account_currency": alloc.amount,
                    "credit_in_account_currency": 0,
                    "cost_center": self.get_project_cost_center(alloc.project),
                    "party_type": None,
                    "party": None,
                    "project": alloc.project,
                    "user_remark": f"Debit: {alloc.salary_component} - {alloc.activity} - {alloc.employee_count} employees"
                })
                
                # Credit entry (matching amount) with project "All-Project" and same cost center
                je.append("accounts", {
                    "account": alloc.account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": alloc.amount,
                    "party_type": None,
                    "party": None,
                    "project": self.payroll_project if hasattr(self, 'payroll_project') else "All-Project",
                    "user_remark": f"Credit: {alloc.salary_component} - {alloc.activity} - {alloc.employee_count} employees"
                })
        
        # Validate that debits equal credits
        je.validate()
        
        # Save the journal entry
        je.save()
        
        # Link the journal entry to this tool
        self.last_journal_entry = je.name
        self.save()
        
        frappe.db.commit()
        
        return {
            "status": "success",
            "journal_entry": je.name,
            "message": f"Journal Entry {je.name} created successfully",
            "total_amount": sum([a.amount for a in self.employee_project_allocation_amounts]),
            "entries_count": len(self.employee_project_allocation_amounts) * 2
        }
    
    def get_project_cost_center(self, project_name):
        """Get cost center for a project"""
        if project_name:
            project = frappe.get_doc("Project", project_name)
            if project.cost_center:
                return project.cost_center
        
        # Return default cost center
        return frappe.db.get_single_value("Global Defaults", "cost_center")

    def get_employee_cost_center(self, employee):
        """Get employee's cost center from payroll"""
        cost_center = frappe.db.get_value('Employee', employee, 'payroll_cost_center')
        
        if not cost_center:
            salary_structure = frappe.db.get_value(
                'Salary Structure Assignment',
                {'employee': employee, 'docstatus': 1},
                'payroll_cost_center',
                order_by='from_date desc'
            )
            if salary_structure:
                cost_center = salary_structure
        
        if not cost_center:
            company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
            cost_center = frappe.db.get_value("Company", company, "cost_center")
        
        return cost_center
    
   
    def get_cost_center(self):
        """Get default cost center"""
        return frappe.db.get_single_value("Global Defaults", "cost_center")
    
    def get_salary_payable_account(self):
        """Get the salary payable account from company settings"""
        company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
        
        salary_payable_account = frappe.db.get_value("Company", company, "default_income_account")
        
        if not salary_payable_account:
            # Try to find Salary Payable account by name
            salary_payable_account = frappe.db.get_value("Account", 
                {"account_name": "Salary Payable", "company": company, "root_type": "Liability"}, "name")
            
            if not salary_payable_account:
                frappe.throw(_("Please set Salary Payable Account in Company settings or create a Salary Payable account"))
        
        return salary_payable_account
    

     # ... existing methods ...
    
    @frappe.whitelist()
    def duplicate_tool_with_allocations(self, new_department=None, new_from_date=None, new_to_date=None):
        """
        Duplicate the current tool with all its employee project allocations
        """
        try:
            # Create new tool
            new_tool = frappe.copy_doc(self)
            # new_tool.name = None  # Let system generate new name
            
            # Update fields if provided
            if new_department:
                new_tool.department = new_department
            if new_from_date:
                new_tool.from_date = getdate(new_from_date)
            if new_to_date:
                new_tool.to_date = getdate(new_to_date)
            
            # Clear processed allocations if they exist
            new_tool.set('employee_project_allocation_amounts', [])
            new_tool.last_journal_entry = None
            
            # Insert new tool
            new_tool.insert()
            new_tool.save()
            
            # Now duplicate all employee allocations linked to this tool
            self.duplicate_employee_allocations(new_tool.name, new_from_date, new_to_date)
            
            frappe.db.commit()
            
            return {
                'status': 'success',
                'new_tool_name': new_tool.name,
                'message': f'Tool duplicated successfully: {new_tool.name}'
            }
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error duplicating tool: {str(e)}", "Tool Duplication Error")
            frappe.throw(str(e))
    
    def duplicate_employee_allocations(self, new_tool_name, new_from_date=None, new_to_date=None):
        """
        Duplicate all employee project allocations linked to this tool
        """
        # Get all employee allocations for this tool
        employee_allocations = frappe.get_all(
            'Employee Project Allocation',
            filters={
                'employee_project_allocation_tool': self.name,
                'docstatus': 0
            },
            fields=['name', 'employee', 'employee_name', 'from_date', 'to_date', 'total_percentage']
        )
        
        if not employee_allocations:
            return
        
        for emp_alloc in employee_allocations:
            # Get the full document
            doc = frappe.get_doc('Employee Project Allocation', emp_alloc.name)
            
            # Create new document
            new_alloc = frappe.copy_doc(doc)
            new_alloc.name = None  # Let system generate new name
            new_alloc.employee_project_allocation_tool = new_tool_name  # Link to new tool
            
            # Update dates if provided
            if new_from_date:
                new_alloc.from_date = getdate(new_from_date)
            if new_to_date:
                new_alloc.to_date = getdate(new_to_date)
            
            # Insert new allocation
            new_alloc.insert()
            new_alloc.save()
        
        return True


@frappe.whitelist()
def duplicate_tool_with_allocations(tool_name, new_department=None, new_from_date=None, new_to_date=None):
    """
    Duplicate a tool with all its allocations
    """
    tool = frappe.get_doc('Employee Project Allocation Tool', tool_name)
    return tool.duplicate_tool_with_allocations(new_department, new_from_date, new_to_date)

@frappe.whitelist()
def get_employee_allocations_for_tool(tool_name):
    """
    Get all employee allocations for a tool
    """
    allocations = frappe.get_all(
        'Employee Project Allocation',
        filters={
            'employee_project_allocation_tool': tool_name,
            'docstatus': 0
        },
        fields=['name', 'employee', 'employee_name', 'from_date', 'to_date', 'total_percentage']
    )
    
    return allocations

# Updated server-side Python code for processing Excel files

import frappe
from frappe import _
import openpyxl
import io
import os
from frappe.utils import getdate, today, get_site_path
from frappe.utils.file_manager import get_file_path

@frappe.whitelist()
def get_child_table_data(parent_doctype, child_table_fieldname):
    """
    Get child table data for a parent document with activity
    """
    try:
        # Get the parent document
        parent_doc = frappe.get_doc("Employee Project Allocation", parent_doctype)
        
        # Get child table data
        child_table_data = parent_doc.get(child_table_fieldname, [])
        
        # Return as list of dicts with activity
        return [{
            "project": row.project,
            "activity": row.activity,
            "percentage": row.percentage
        } for row in child_table_data]
        
    except Exception as e:
        frappe.log_error(f"Error getting child table data: {str(e)}", "Employee Allocation Tool")
        return []


# Updated download template to include activity
@frappe.whitelist()
def download_allocation_template(department, tool_name):
    """Generate and return Excel template for employee allocations"""
    try:
        # Get employees from selected department
        employees = frappe.get_all('Employee',
            filters={
                'department': department,
                'status': 'Active'
            },
            fields=['name', 'employee_name', 'designation']
        )
        
        # Get projects with custom_include_employee_allocation filter
        projects = frappe.get_all('Project',
            fields=['name', 'custom_project_shortcut as project_name'],
            filters={'custom_include_employee_allocation': 1}
        )
        
        activities = ['Operation', 'Installation']
        
        if not employees:
            frappe.throw(_('No active employees found in the selected department'))
        
        if not projects:
            frappe.throw(_('No projects found in the system'))
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Employee Allocations"
        
        # Define styles
        header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        center_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Prepare header row
        headers = ['Employee ID', 'Employee Name', 'Designation']
        for project in projects:
            for activity in activities:
                project_name = project.get('project_name') or project.get('name')
                headers.append(f"{project_name} - {activity} (%)")
        
        headers.extend(['Total Percentage', 'Status'])
        
        # Write main headers
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = border
        
        # Write data rows
        current_row = 2
        for employee in employees:
            # Add employee info
            ws.cell(row=current_row, column=1, value=employee.get('name'))
            ws.cell(row=current_row, column=2, value=employee.get('employee_name'))
            ws.cell(row=current_row, column=3, value=employee.get('designation') or 'N/A')
            
            # Empty cells for percentages (user will fill)
            for col in range(4, len(headers) - 1):
                cell = ws.cell(row=current_row, column=col, value='')
                cell.border = border
                cell.alignment = center_alignment
            
            # Total percentage and status
            total_cell = ws.cell(row=current_row, column=len(headers), value='0')
            total_cell.border = border
            total_cell.alignment = center_alignment
            
            status_cell = ws.cell(row=current_row, column=len(headers)+1, value='Pending')
            status_cell.border = border
            status_cell.alignment = center_alignment
            
            # Apply borders to all cells
            for col in range(1, len(headers) + 2):
                cell = ws.cell(row=current_row, column=col)
                cell.border = border
                cell.alignment = center_alignment
            
            current_row += 1
        
        # Add instructions
        current_row += 1
        instructions = [
            'INSTRUCTIONS:',
            '1. Fill in the percentage values for each project-activity combination',
            '2. Each employee\'s total percentage should sum to 100%',
            '3. Only fill numeric values (0-100) in the percentage columns',
            '4. Do not modify employee information columns',
            '5. Make sure each employee has exactly 100% total allocation'
        ]
        
        for idx, instruction in enumerate(instructions):
            cell = ws.cell(row=current_row + idx, column=1, value=instruction)
            if idx == 0:
                cell.font = Font(bold=True, color="7d6608")
            cell.alignment = Alignment(horizontal="left", vertical="center")
        
        # Set column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        
        for col in range(4, len(headers) + 1):
            col_letter = openpyxl.utils.get_column_letter(col)
            ws.column_dimensions[col_letter].width = 22
        
        ws.column_dimensions[openpyxl.utils.get_column_letter(len(headers))].width = 15
        ws.column_dimensions[openpyxl.utils.get_column_letter(len(headers)+1)].width = 12
        
        # Save to file
        file_name = f"Employee_Allocation_Template_{department}_{today()}.xlsx"
        temp_path = get_site_path('private', 'files', 'templates')
        
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        
        file_path = os.path.join(temp_path, file_name)
        wb.save(file_path)
        
        # Create file record
        from frappe.utils.file_manager import save_file
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_doc = save_file(
            file_name,
            file_content,
            'Employee Project Allocation Tool',
            tool_name,
            is_private=1
        )
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            'file_url': file_doc.file_url,
            'file_name': file_name
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating template: {str(e)}", "Template Generation Error")
        frappe.throw(str(e))


@frappe.whitelist()
def process_salary_allocation_for_tool(tool_name):
    """Process salary allocation for a specific tool"""
    tool = frappe.get_doc('Employee Project Allocation Tool', tool_name)
    return tool.process_salary_allocation()


@frappe.whitelist()
def create_journal_entry_for_tool(tool_name):
    """Create journal entry for a specific tool"""
    tool = frappe.get_doc('Employee Project Allocation Tool', tool_name)
    return tool.create_journal_entry_from_allocations()


@frappe.whitelist()
def get_salary_payable_account(company=None):
    """Get salary payable account"""
    if not company:
        company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    return frappe.db.get_value("Company", company, "default_income_account")


@frappe.whitelist()
def delete_all_allocations(tool_name):
    """Delete all employee project allocations linked to the given tool"""
    try:
        allocations = frappe.get_all('Employee Project Allocation', 
            filters={
                'employee_project_allocation_tool': tool_name,
                'docstatus': 0
            },
            pluck='name'
        )
        
        count = len(allocations)
        
        for alloc_name in allocations:
            frappe.delete_doc('Employee Project Allocation', alloc_name, force=True)
        
        frappe.db.commit()
        return count
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error deleting allocations: {str(e)}", "Allocation Delete Error")
        frappe.throw(str(e))
@frappe.whitelist()
def download_allocation_template(department, tool_name):
    """Generate and return Excel template for employee allocations"""
    try:
        # Get employees from selected department
        employees = frappe.get_all('Employee',
            filters={
                'department': department,
                'status': 'Active'
            },
            fields=['name', 'employee_name', 'designation']
        )
        
        # Get up to 4 projects
        projects = frappe.get_all('Project',
            fields=['name', 'custom_project_shortcut as project_name'],
            filters={'custom_include_employee_allocation': 1}
        )
        
        activities = ['Operation', 'Installation']
        
        if not employees:
            frappe.throw(_('No active employees found in the selected department'))
        
        if not projects:
            frappe.throw(_('No projects found in the system'))
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Employee Allocations"
        
        # Define styles
        header_fill = PatternFill(start_color="2c3e50", end_color="2c3e50", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        subheader_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Prepare header row
        headers = ['Employee ID', 'Employee Name', 'Designation']
        for project in projects:
            for activity in activities:
                project_name = project.get('project_name') or project.get('name')
                headers.append(f"{project_name} - {activity} (%)")
        
        headers.extend(['Total Percentage', 'Status'])
        
        # Write main headers
        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_alignment
            cell.border = border
        
        # Write data rows
        current_row = 2
        for employee in employees:
            # Add employee info
            ws.cell(row=current_row, column=1, value=employee.get('name'))
            ws.cell(row=current_row, column=2, value=employee.get('employee_name'))
            ws.cell(row=current_row, column=3, value=employee.get('designation') or 'N/A')
            
            # Empty cells for percentages (user will fill)
            for col in range(4, len(headers) - 1):
                cell = ws.cell(row=current_row, column=col, value='')
                cell.border = border
                cell.alignment = center_alignment
            
            # Total percentage and status
            total_cell = ws.cell(row=current_row, column=len(headers), value='0')
            total_cell.border = border
            total_cell.alignment = center_alignment
            
            status_cell = ws.cell(row=current_row, column=len(headers)+1, value='Pending')
            status_cell.border = border
            status_cell.alignment = center_alignment
            
            # Apply borders to all cells
            for col in range(1, len(headers) + 2):
                cell = ws.cell(row=current_row, column=col)
                cell.border = border
                cell.alignment = center_alignment
            
            current_row += 1
        
        # Add instructions
        current_row += 1
        instructions = [
            'INSTRUCTIONS:',
            '1. Fill in the percentage values for each project-activity combination',
            '2. Each employee\'s total percentage should sum to 100%',
            '3. Only fill numeric values (0-100) in the percentage columns',
            '4. Do not modify employee information columns',
            '5. Make sure each employee has exactly 100% total allocation'
        ]
        
        for idx, instruction in enumerate(instructions):
            cell = ws.cell(row=current_row + idx, column=1, value=instruction)
            if idx == 0:
                cell.font = Font(bold=True, color="7d6608")
            cell.alignment = Alignment(horizontal="left", vertical="center")
        
        # Set column widths
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 20
        
        for col in range(4, len(headers) + 1):
            col_letter = openpyxl.utils.get_column_letter(col)
            ws.column_dimensions[col_letter].width = 22
        
        ws.column_dimensions[openpyxl.utils.get_column_letter(len(headers))].width = 15
        ws.column_dimensions[openpyxl.utils.get_column_letter(len(headers)+1)].width = 12
        
        # Save to file
        file_name = f"Employee_Allocation_Template_{department}_{today()}.xlsx"
        temp_path = get_site_path('private', 'files', 'templates')
        
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        
        file_path = os.path.join(temp_path, file_name)
        wb.save(file_path)
        
        # Create file record
        from frappe.utils.file_manager import save_file
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_doc = save_file(
            file_name,
            file_content,
            'Employee Project Allocation Tool',
            tool_name,
            is_private=1
        )
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            'file_url': file_doc.file_url,
            'file_name': file_name
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating template: {str(e)}", "Template Generation Error")
        frappe.throw(str(e))

    


@frappe.whitelist()
def process_allocation_excel(file_url, tool_name, from_date, to_date):
    """Process uploaded Excel file and create/update allocations"""
    try:
        # Get the file content correctly
        file_doc = frappe.get_doc('File', {'file_url': file_url})
        if not file_doc:
            frappe.throw(_("File not found"))
        
        # Get the file path
        file_path = get_file_path(file_doc.file_url)
        
        # Check if file exists
        if not os.path.exists(file_path):
            frappe.throw(_("File does not exist at path: {0}").format(file_path))
        
        # Load workbook from file path
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        # First, try to read from the new format (with Project ID columns)
        # Check if this is the new format by looking at row 3
        is_new_format = False
        for col in range(1, min(ws.max_column + 1, 10)):
            cell_value = ws.cell(row=3, column=col).value
            if cell_value and 'Project ID' in str(cell_value):
                is_new_format = True
                break
        
        if is_new_format:
            # Process new format (with separate Project ID and Percentage columns)
            return process_new_format_excel(ws, tool_name, from_date, to_date, file_doc)
        else:
            # Process old format for backward compatibility
            return process_old_format_excel(ws, tool_name, from_date, to_date, file_doc)
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error processing Excel: {str(e)}", "Excel Processing Error")
        frappe.throw(str(e))

def process_new_format_excel(ws, tool_name, from_date, to_date, file_doc):
    """Process Excel file in new format with separate Project ID and Percentage columns"""
    success_count = 0
    errors = []
    
    # Find column indices from row 2 and 3
    emp_id_col = None
    emp_name_col = None
    total_percentage_col = None
    percentage_cols = []
    
    max_col = ws.max_column
    max_row = ws.max_row
    
    # First, find basic columns from row 2
    for col in range(1, max_col + 1):
        cell_value = ws.cell(row=2, column=col).value
        if cell_value:
            cell_str = str(cell_value).strip()
            if cell_str == 'Employee ID':
                emp_id_col = col - 1  # 0-based index
            elif cell_str == 'Employee Name':
                emp_name_col = col - 1
            elif cell_str == 'Total Percentage':
                total_percentage_col = col - 1
    
    # Now find percentage columns from row 3
    for col in range(1, max_col + 1):
        cell_value = ws.cell(row=3, column=col).value
        if cell_value:
            cell_str = str(cell_value).strip()
            if 'Percentage (%)' in cell_str:
                # Extract activity
                activity = cell_str.replace(' - Percentage (%)', '').strip()
                
                # The project ID column is to the left
                project_id_col = col - 2  # 0-based index
                
                # Get a sample project ID from the first data row (row 4) to verify
                sample_project_id = None
                for sample_row in range(4, min(max_row + 1, 6)):
                    project_cell = ws.cell(row=sample_row, column=project_id_col + 1)
                    if project_cell.value:
                        sample_project_id = str(project_cell.value).strip()
                        break
                
                percentage_cols.append({
                    'percentage_col': col - 1,  # 0-based index
                    'project_id_col': project_id_col,
                    'activity': activity,
                    'sample_project': sample_project_id
                })
    
    if emp_id_col is None:
        frappe.throw(_("Invalid file format: Employee ID column not found"))
    
    # Create a cache for project name to ID mapping
    project_cache = {}
    
    # Process each data row (starting from row 4)
    for row in range(4, max_row + 1):
        employee_id = ws.cell(row=row, column=emp_id_col + 1).value
        if not employee_id or not str(employee_id).strip():
            continue
        
        employee_id = str(employee_id).strip()
        
        # Check if employee exists
        if not frappe.db.exists('Employee', employee_id):
            errors.append(f"Employee {employee_id} not found in system")
            continue
        
        # Extract allocations
        allocations = []
        total_percentage = 0
        
        for col_info in percentage_cols:
            # Get project ID from the project ID column
            project_cell = ws.cell(row=row, column=col_info['project_id_col'] + 1)
            project_identifier = project_cell.value if project_cell.value else None
            
            if not project_identifier:
                continue
            
            project_identifier = str(project_identifier).strip()
            
            # Get percentage from percentage column
            percentage_cell = ws.cell(row=row, column=col_info['percentage_col'] + 1)
            percentage = 0
            cell_value = percentage_cell.value
            
            if cell_value is not None and str(cell_value).strip():
                try:
                    # Handle different data types that might come from Excel
                    if isinstance(cell_value, (int, float)):
                        percentage = float(cell_value)
                    else:
                        percentage = float(str(cell_value).strip())
                    
                    if percentage > 0:
                        # Check if this is a project name or project ID
                        project_id = None
                        
                        # Check cache first
                        if project_identifier in project_cache:
                            project_id = project_cache[project_identifier]
                        else:
                            # Try to find project by ID first
                            if frappe.db.exists('Project', project_identifier):
                                project_id = project_identifier
                            else:
                                # Try to find project by name
                                project_name_match = frappe.db.get_value('Project', 
                                    {'project_name': project_identifier}, 'name')
                                if project_name_match:
                                    project_id = project_name_match
                                else:
                                    # Try partial match
                                    projects = frappe.get_all('Project', 
                                        filters={'project_name': ['like', f'%{project_identifier}%']},
                                        fields=['name', 'project_name'],
                                        limit=1
                                    )
                                    if projects:
                                        project_id = projects[0].name
                            
                            # Cache the result
                            project_cache[project_identifier] = project_id
                        
                        if project_id:
                            allocations.append({
                                'project': project_id,
                                'activity': col_info['activity'],
                                'percentage': percentage
                            })
                            total_percentage += percentage
                        else:
                            errors.append(f"Employee {employee_id}: Project '{project_identifier}' not found")
                            
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
        
        # Validate total percentage
        if total_percentage > 0:
            # Allow small rounding errors (99.5% to 100.5%)
            if abs(total_percentage - 100) > 0.5:
                errors.append(f"Employee {employee_id}: Total percentage is {total_percentage}%, must be 100%")
                continue
            else:
                # Round to 100 if close enough
                total_percentage = 100
        
        if allocations:
            # Check if allocation already exists
            existing_allocation = frappe.db.get_value('Employee Project Allocation',
                {
                    'employee': employee_id,
                    'docstatus': 0,
                    'employee_project_allocation_tool': tool_name
                },
                'name'
            )
            
            if existing_allocation:
                # Update existing allocation
                update_allocation(existing_allocation, allocations, total_percentage)
                success_count += 1
            else:
                # Create new allocation
                create_allocation(employee_id, tool_name, from_date, to_date, allocations, total_percentage)
                success_count += 1
    
    frappe.db.commit()
    
    # Clean up the uploaded file
    if file_doc:
        frappe.delete_doc('File', file_doc.name)
    
    return {
        'success_count': success_count,
        'errors': errors
    }

def process_old_format_excel(ws, tool_name, from_date, to_date, file_doc):
    print("Processing old format Excel file")
    """Process Excel file in old format for backward compatibility"""
    success_count = 0
    errors = []
    
    # Parse headers to identify columns
    headers = []
    max_col = ws.max_column
    for col in range(1, max_col + 1):
        header = ws.cell(row=1, column=col).value
        if header:
            headers.append(str(header).strip())
    
    # Find column indices
    emp_id_col = None
    emp_name_col = None
    total_percentage_col = None
    percentage_cols = []
    
    for idx, header in enumerate(headers):
        if header == 'Employee ID':
            emp_id_col = idx
        elif header == 'Employee Name':
            emp_name_col = idx
        elif header == 'Total Percentage':
            total_percentage_col = idx
        elif header and ' (%)' in header:
            # This is a percentage column
            project_activity = header.replace(' (%)', '')
            if ' - ' in project_activity:
                parts = project_activity.split(' - ')
                percentage_cols.append({
                    'col': idx,
                    'project_name': parts[0],
                    'activity': parts[1]
                })
    
    if emp_id_col is None:
        frappe.throw(_("Invalid file format: Employee ID column not found"))
    
    # Create project name to ID mapping
    project_cache = {}
    
    # Process each row
    max_row = ws.max_row
    for row in range(2, max_row + 1):
        employee_id = ws.cell(row=row, column=emp_id_col + 1).value
        if not employee_id or not str(employee_id).strip():
            continue
        
        employee_id = str(employee_id).strip()
        
        # Check if employee exists
        if not frappe.db.exists('Employee', employee_id):
            errors.append(f"Employee {employee_id} not found in system")
            continue
        
        # Extract allocations
        allocations = []
        total_percentage = 0
        
        for col_info in percentage_cols:
            percentage_cell = ws.cell(row=row, column=col_info['col'] + 1)
            percentage = 0
            cell_value = percentage_cell.value
            
            if cell_value is not None and str(cell_value).strip():
                try:
                    # Handle different data types that might come from Excel
                    if isinstance(cell_value, (int, float)):
                        percentage = float(cell_value)
                    else:
                        percentage = float(str(cell_value).strip())
                    
                    if percentage > 0:
                        # Get project ID from project name
                        project_name = col_info['project_name']
                        project_id = None
                        
                        # Check cache first
                        if project_name in project_cache:
                            project_id = project_cache[project_name]
                        else:
                            # Try to find project by name
                            project = frappe.db.get_value('Project', 
                                {'custom_project_shortcut': project_name}, 'name')
                            if project:
                                project_id = project
                            else:
                                # Try to find by exact name match in name field
                                project = frappe.db.get_value('Project', 
                                    {'name': project_name}, 'name')
                                if project:
                                    project_id = project
                            
                            project_cache[project_name] = project_id
                        
                        if project_id:
                            allocations.append({
                                'project': project_id,
                                'activity': col_info['activity'],
                                'percentage': percentage
                            })
                            total_percentage += percentage
                        else:
                            errors.append(f"Employee {employee_id}: Project '{project_name}' not found")
                            
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
        
        # Validate total percentage
        if total_percentage > 0:
            # Allow small rounding errors (99.5% to 100.5%)
            if abs(total_percentage - 100) > 0.5:
                errors.append(f"Employee {employee_id}: Total percentage is {total_percentage}%, must be 100%")
                continue
            else:
                # Round to 100 if close enough
                total_percentage = 100
        
        if allocations:
            # Check if allocation already exists
            existing_allocation = frappe.db.get_value('Employee Project Allocation',
                {
                    'employee': employee_id,
                    'docstatus': 0,
                    'employee_project_allocation_tool': tool_name
                },
                'name'
            )
            
            if existing_allocation:
                # Update existing allocation
                update_allocation(existing_allocation, allocations, total_percentage)
                success_count += 1
            else:
                # Create new allocation
                create_allocation(employee_id, tool_name, from_date, to_date, allocations, total_percentage)
                success_count += 1
    
    frappe.db.commit()
    
    # Clean up the uploaded file
    if file_doc:
        frappe.delete_doc('File', file_doc.name)
    
    return {
        'success_count': success_count,
        'errors': errors
    }

def create_allocation(employee_id, tool_name, from_date, to_date, allocations, total_percentage):
    """Create new employee project allocation"""
    doc = frappe.get_doc({
        'doctype': 'Employee Project Allocation',
        'employee': employee_id,
        'from_date': from_date,
        'to_date': to_date,
        'employee_project_allocation_tool': tool_name,
        'employee_project_allocation_details': []
    })
    
    for alloc in allocations:
        doc.append('employee_project_allocation_details', {
            'project': alloc['project'],
            'activity': alloc['activity'],
            'percentage': alloc['percentage']
        })
    
    doc.total_percentage = total_percentage
    doc.insert()
    return doc

def update_allocation(allocation_name, allocations, total_percentage):
    """Update existing employee project allocation"""
    doc = frappe.get_doc('Employee Project Allocation', allocation_name)
    doc.employee_project_allocation_details = []
    
    for alloc in allocations:
        doc.append('employee_project_allocation_details', {
            'project': alloc['project'],
            'activity': alloc['activity'],
            'percentage': alloc['percentage']
        })
    
    doc.total_percentage = total_percentage
    doc.save()
    return doc







# Method to get salary component accounts
@frappe.whitelist()
def get_salary_component_account(component_name):
    """Get the default account for a salary component"""
    component = frappe.get_doc('Salary Component', component_name)
    return component.get('account')


# Method to test/fetch employee salary slip
@frappe.whitelist()
def get_employee_salary_slip_for_date(employee, to_date):
    """Get employee's salary slip for a specific date"""
    slip = frappe.db.get_value(
        'Salary Slip',
        {
            'employee': employee,
            'docstatus': 1,
            'start_date': ['<=', to_date]
        },
        ['name', 'start_date', 'end_date', 'gross_pay', 'net_pay'],
        order_by='start_date desc',
        as_dict=True
    )
    
    if slip:
        # Get components
        components = frappe.get_all(
            'Salary Detail',
            filters={'parent': slip.name},
            fields=['salary_component', 'amount', 'parentfield']
        )
        slip['components'] = components
    
    return slip







# ===================
# Add this to: wt_operations/wt_operations/doctype/employee_project_allocation_tool/employee_project_allocation_tool.py
# (alongside your existing download_allocation_template / process_allocation_excel / delete_all_allocations methods)
#
# Make sure `import re` and `import frappe` exist at the top of that file.

import re


@frappe.whitelist()
def get_dashboard_data(tool_name):
    """
    Returns everything the dashboard needs in ONE server round-trip:
    - allocations + their child rows (1 query instead of N)
    - employee details for all involved employees (1 query instead of N)
    - project details/shortcuts for all involved projects (1 query instead of P)

    Replaces the old client-side pattern of 3N + P sequential frappe.call()/
    frappe.db.get_value() awaits with a single call.
    """

    allocations = frappe.get_all(
        "Employee Project Allocation",
        filters={"docstatus": 0, "employee_project_allocation_tool": tool_name},
        fields=["name", "employee", "employee_name", "from_date", "to_date", "total_percentage"],
    )

    if not allocations:
        return {"employees": [], "projects": [], "activities": [], "project_details": {}}

    allocation_names = [a.name for a in allocations]
    employee_ids = list({a.employee for a in allocations if a.employee})

    # Resolve the child table doctype dynamically (no hardcoded/guessed name)
    meta = frappe.get_meta("Employee Project Allocation")
    child_field = meta.get_field("employee_project_allocation_details")
    child_doctype = child_field.options

    # 1 query: all child rows for all allocations at once
    all_details = frappe.get_all(
        child_doctype,
        filters={"parent": ["in", allocation_names]},
        fields=["parent", "project", "activity", "percentage"],
    )

    details_by_parent = {}
    project_ids = set()
    activity_set = set()
    for d in all_details:
        details_by_parent.setdefault(d.parent, []).append(d)
        if d.project:
            project_ids.add(d.project)
        if d.activity:
            activity_set.add(d.activity)

    # 1 query: all employees at once
    employee_info = {}
    if employee_ids:
        emp_rows = frappe.get_all(
            "Employee",
            filters={"name": ["in", employee_ids]},
            fields=["name", "employee_name", "department", "designation"],
        )
        employee_info = {e.name: e for e in emp_rows}

    # 1 query: all projects at once
    project_details = {}
    if project_ids:
        proj_rows = frappe.get_all(
            "Project",
            filters={"name": ["in", list(project_ids)]},
            fields=["name", "project_name", "custom_project_shortcut"],
        )
        for p in proj_rows:
            shortcut = p.custom_project_shortcut or _generate_shortcut(p.project_name or p.name)
            project_details[p.name] = {
                "name": p.name,
                "project_name": p.project_name or p.name,
                "shortcut": shortcut,
            }

    # Fallback entries for any project referenced but not found (e.g. deleted/renamed)
    for pid in project_ids:
        if pid not in project_details:
            project_details[pid] = {
                "name": pid,
                "project_name": pid,
                "shortcut": _generate_shortcut(pid),
            }

    employees = []
    for a in allocations:
        emp = employee_info.get(a.employee) or {}
        rows = details_by_parent.get(a.name, [])
        employees.append({
            "employee": a.employee,
            "employee_name": a.employee_name or emp.get("employee_name") or a.employee,
            "department": emp.get("department") or "N/A",
            "designation": emp.get("designation") or "N/A",
            "allocations": [
                {"project": r.project, "activity": r.activity, "percentage": r.percentage}
                for r in rows
            ],
            "total_percentage": a.total_percentage or 0,
            "allocation_name": a.name,
        })

    return {
        "employees": employees,
        "projects": sorted(project_ids),
        "activities": sorted(activity_set),
        "project_details": project_details,
    }


def _generate_shortcut(name):
    if not name:
        return "N/A"
    words = re.split(r"[\s\-_]+", name)
    words = [w for w in words if w]
    if len(words) <= 1:
        return name[:4].upper()
    return "".join(w[0] for w in words).upper()[:4]