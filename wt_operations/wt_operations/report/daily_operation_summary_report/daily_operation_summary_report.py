import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data

def get_columns():
    return [
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 120},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Link", "options": "Asset", "width": 120},
        {"label": "Project Unit Assignment", "fieldname": "unit_assignment_record", "fieldtype": "Link", "options": "Project Unit Assignment", "width": 180},
        {"label": "Prepared By", "fieldname": "prepared_by", "fieldtype": "Link", "options": "User", "width": 120},
        {"label": "Shift Supervisor", "fieldname": "shift_supervisor", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Operator", "fieldname": "operator", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Technician 1", "fieldname": "technician", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Technician 2", "fieldname": "technician_2", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Average Flow Rate", "fieldname": "average_flow_rate", "fieldtype": "Float", "width": 120},
        {"label": "Energy Consumption", "fieldname": "energy_consumtion", "fieldtype": "Float", "width": 120},
        {"label": "Noncompliant", "fieldname": "noncompliant", "fieldtype": "Data", "width": 150},
        {"label": "Safety", "fieldname": "safety", "fieldtype": "Data", "width": 150},
        {"label": "Section", "fieldname": "section", "fieldtype": "Data", "width": 150},
        {"label": "Parameter", "fieldname": "treatment_parameter", "fieldtype": "Data", "width": 180},
        {"label": "UOM", "fieldname": "uom", "fieldtype": "Data", "width": 80},
        {"label": "Target", "fieldname": "target", "fieldtype": "Float", "width": 100},
        {"label": "Actual", "fieldname": "actual", "fieldtype": "Float", "width": 100},
        {"label": "Chemical", "fieldname": "chemical", "fieldtype": "Data", "width": 150},
        {"label": "Volume (m3)", "fieldname": "volume_m3", "fieldtype": "Float", "width": 100},
        {"label": "Tank Type", "fieldname": "tank_type", "fieldtype": "Data", "width": 120},
    ]

def get_data(filters):
    conditions = []
    if filters.get("start_date") and filters.get("end_date"):
        conditions.append(f"date BETWEEN '{filters['start_date']}' AND '{filters['end_date']}'")
    if filters.get("project"):
        conditions.append(f"project = '{filters['project']}'")
    if filters.get("unit"):
        conditions.append(f"unit = '{filters['unit']}'")
    if filters.get("unit_assignment_record"):
        conditions.append(f"unit_assignment_record = '{filters['unit_assignment_record']}'")
    if filters.get("name"):
        conditions.append(f"name = '{filters['name']}'")

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    group_by = filters.get("group_by") or "project"

    dor_list = frappe.db.sql(f"""
        SELECT *
        FROM `tabDaily Operation Report`
        {where_clause}
        ORDER BY {group_by}, date
    """, as_dict=True)

    data = []
    for dor in dor_list:
        dor_name = dor["name"]

        def add_rows(child_doctype, section_label):
            rows = frappe.get_all(child_doctype, filters={"parent": dor_name}, fields=["*"])
            for row in rows:
                data.append({**dor, "section": section_label, **row})

        add_rows("Treatment parameters table", "Treatment Parameters")
        add_rows("Tank Level Table", "Tank Levels")
        add_rows("Chemical Consumption table", "Chemical Consumption")
        add_rows("Influent Parameters Table", "Influent Parameters")
        add_rows("Effluent Parameters Table", "Effluent Parameters")

    return data
