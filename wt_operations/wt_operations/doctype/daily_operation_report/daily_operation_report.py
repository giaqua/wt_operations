import frappe
from frappe.model.document import Document
from frappe import _
import operator

class DailyOperationReport(Document):
    def before_submit(self):
        self.update_chemical_valuation_rates()
    #     text = "ABD12+DESD-OOCS*400-700/2"
    #     result = calculate_expression(text)
    #     print(f"{text} = {result}","============================")  # Output: 100+200-300*400 = -119700.0

    # def after_submit(self):
    #     # Recalculate valuation rates whenever the document is updated
    #     self.update_chemical_valuation_rates()
    #     print("Updated chemical valuation rates on update","============================")

    def validate(self):
        self.validate_comments()
        self.validate_physical_parameter_comments()

    # This method checks if comments are provided when actual values do not match target values
    def validate_comments(self):
        if hasattr(self, "treatment_parameters_table"):
            for row in self.treatment_parameters_table:
                if row.actual and row.target and row.actual < row.target and not row.comments:
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

    def get_warehouse_from_unit(unit_name):
        """Get warehouse from Project Unit doctype"""
        project_unit = frappe.get_doc("Project Unit", unit_name)
        return project_unit.warehouse  # Assuming fieldname is 'warehouse'

    def get_valuation_rate_on_date(item_code, warehouse, posting_date):
        """
        Get valuation rate from Stock Ledger Entry for a specific date.
        Uses the same logic ERPNext uses for valuation calculation.
        """
        
        # Query the most recent SLE before or on the posting date
        sle = frappe.db.sql("""
            SELECT valuation_rate
            FROM `tabStock Ledger Entry`
            WHERE 
                item_code = %s 
                AND warehouse = %s 
                AND posting_date <= %s
                AND is_cancelled = 0
                AND valuation_rate > 0
            ORDER BY posting_date DESC, posting_time DESC, name DESC
            LIMIT 1
        """, (item_code, warehouse, posting_date), as_dict=True)
        
        if sle and sle[0].get('valuation_rate'):
            return sle[0]['valuation_rate']
        
        # Fallback: try without warehouse constraint
        sle = frappe.db.sql("""
            SELECT valuation_rate
            FROM `tabStock Ledger Entry`
            WHERE 
                item_code = %s 
                AND posting_date <= %s
                AND is_cancelled = 0
                AND valuation_rate > 0
            ORDER BY posting_date DESC, posting_time DESC, name DESC
            LIMIT 1
        """, (item_code, posting_date), as_dict=True)
        
        if sle and sle[0].get('valuation_rate'):
            return sle[0]['valuation_rate']
        
        # Return 0 if no valuation found
        return 0.0

    def update_chemical_valuation_rates(self):
        """Update valuation_rate for all chemicals in usage table"""
        
        # Get warehouse from Unit
        if not self.unit:
            frappe.throw("Unit is required to determine warehouse")
            
        project_unit = frappe.get_doc("Project Unit", self.unit)
        warehouse = project_unit.warehouse
        
        if not warehouse:
            frappe.throw(f"No warehouse found for Unit {self.unit}")
        
        # Update each chemical entry
        for chemical_row in self.chemical_usage_table:
            if not chemical_row.chemical or chemical_row.chemical_quantity_used_kg == 0:
                continue
            
            item_code = frappe.get_value("Chemical Item", chemical_row.chemical, "stock_item")
            if not item_code:
                frappe.throw(f"No item code found for chemical {chemical_row.chemical}")
            # Get valuation rate from Stock Ledger
            valuation_rate = self._get_valuation_rate_for_chemical(
                item_code,
                warehouse,
                self.date
            )
            
            # Update the field
            chemical_row.valuation_rate = valuation_rate
            
        # Save the document
        # self.save()
        
    def _get_valuation_rate_for_chemical(self, item_code, warehouse, posting_date):
        """Get valuation rate for a chemical item on specific date"""
        
        sle = frappe.db.sql("""
            SELECT valuation_rate
            FROM `tabStock Ledger Entry`
            WHERE 
                item_code = %s 
                AND warehouse = %s 
                AND posting_date <= %s
                AND is_cancelled = 0
                AND valuation_rate > 0
            ORDER BY posting_date DESC, posting_time DESC, name DESC
            LIMIT 1
        """, (item_code, warehouse, posting_date), as_dict=True)
        
        if sle:
            return sle[0]['valuation_rate']
            
        return 0.0

def calculate_expression(expression):
# Define operators and their precedence
    ops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv
    }
    
    # Simple tokenization (for basic expressions)
    import re
    # tokens = re.findall(r'\d+|[+\-*/]', expression)
      # Pattern breakdown:
    # [A-Za-z]+\d*  : letters followed by optional digits (for operands like ABD12, DESD)
    # |             : OR
    # \d+           : digits only (for pure numbers like 400, 700, 2)
    # |             : OR
    # [+\-*/]       : operators
    pattern = r'\d+|[A-Za-z]+\d*|[+\-*/]'
    tokens = re.findall(pattern, expression)

    # tokens = re.findall(r'[a-zA-Z]*\d+[a-zA-Z]*|[+\-*/]', expression)
    print(f"Tokens: {tokens}")
    # First pass: handle * and / (higher precedence)
    i = 1
    while i < len(tokens) - 1:
        if tokens[i] in ('*', '/'):
            left = float(tokens[i-1])
            right = float(tokens[i+1])
            result = ops[tokens[i]](left, right)
            print(str(tokens) + " operator found. Calculating: " + str(left) + " " + tokens[i] + " " + str(right) + " = " + str(result),"======================")
            print(f"Calculating {left} {tokens[i]} {right} = {result}")
            tokens[i-1:i+2] = [str(result)]
        else:
            i += 1
    
    # Second pass: handle + and -
    result = float(tokens[0])
    for i in range(1, len(tokens), 2):
        op = tokens[i]
        num = float(tokens[i+1])
        print(f"Applying operator {op} to {result} and {num}")
        result = ops[op](result, num)
    
    return result

