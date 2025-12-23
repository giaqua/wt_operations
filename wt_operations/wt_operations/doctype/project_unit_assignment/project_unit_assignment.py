import frappe
from frappe.model.document import Document

class ProjectUnitAssignment(Document):
    def validate(self):
        self.ensure_no_duplicate_assignments()
        self.validate_dates()
        self.ensure_unique_parameters()

# This method checks for overlapping assignments for the same unit
    def ensure_no_duplicate_assignments(self):
        overlap_query = """
            SELECT name
            FROM `tabProject Unit Assignment`
            WHERE
                unit = %s AND docstatus < 2 AND name != %s AND (
                    (assignment_date <= %s AND assignment_expected_end_date >= %s) OR
                    (assignment_date <= %s AND assignment_expected_end_date >= %s)
                )
        """
        overlapping_assignments = frappe.db.sql(overlap_query, (
            self.unit, self.name,
            self.assignment_expected_end_date, self.assignment_date,
            self.assignment_date, self.assignment_expected_end_date,
        ))
        if overlapping_assignments:
            frappe.throw(f"Duplicate assignment detected for unit {self.unit} between {self.assignment_date} and {self.assignment_expected_end_date}.")
# This method validates the assignment dates
    def validate_dates(self):
        if not self.assignment_date or not self.assignment_expected_end_date:
            frappe.throw("Please set both Assignment Date and Assignment Expected End Date.")
        if self.assignment_expected_end_date <= self.assignment_date:
            frappe.throw("Assignment Expected End Date must be after the Assignment Date.")
# This method ensures that treatment parameters are unique
    def ensure_unique_parameters(self):
        parameters = [row.treatment_parameter for row in self.treatment_parameters_template_table]
        if len(parameters) != len(set(parameters)):
            frappe.throw("Duplicate parameters found in Treatment Parameters Table.")