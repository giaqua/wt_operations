import frappe
from frappe.model.document import Document
import operator

class DailyOperationReport(Document):
    # def before_save(self):
    #     text = "ABD12+DESD-OOCS*400-700/2"
    #     result = calculate_expression(text)
    #     print(f"{text} = {result}","============================")  # Output: 100+200-300*400 = -119700.0


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

