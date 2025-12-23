import frappe
from frappe.model.document import Document

class DailyOperationReport(Document):
    def validate(self):
        self.validate_comments()
        self.validate_physical_parameter_comments()

    # This method checks if comments are provided when actual values do not match target values
    def validate_comments(self):
        if hasattr(self, "treatment_parameters_table"):
            for row in self.treatment_parameters_table:
                if row.actual != row.target and not row.comments:
                    frappe.throw(
                        f"Comments are required when Actual value does not match Target for treatment parameter: {row.treatment_parameter}"
                    )
    # This method checks if comments are provided for physical parameters when actual values exceed limits
    def validate_physical_parameter_comments(self):
        # Validate influent parameters
        if hasattr(self, "influent_parameters_table"):
            for row in self.influent_parameters_table:
                if (
                    row.actual_value
                    and row.limit
                    and row.actual_value > row.limit
                    and not row.comments
                ):
                    frappe.throw(
                        f'Please add a comment for Influent Parameter "{row.parameter}" where Actual Value ({row.actual_value}) exceeds Limit ({row.limit}).'
                    )
        # Validate effluent parameters 
        if hasattr(self, "effluent_parameters_table"):
            for row in self.effluent_parameters_table:
                if (
                    row.actual_value
                    and row.limit
                    and row.actual_value > row.limit
                    and not row.comments
                ):
                    frappe.throw(
                        f'Please add a comment for Effluent Parameter "{row.parameter}" where Actual Value ({row.actual_value}) exceeds Limit ({row.limit}).'
                    )