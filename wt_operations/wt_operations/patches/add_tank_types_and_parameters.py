import frappe

def execute():
    # Tank Types 
    tank_types = [
        {"tank_type_name": "Waste Water Tank"},
        {"tank_type_name": "Equalization Tank"},
        {"tank_type_name": "Product Tank"},
        {"tank_type_name": "Sludge Tank"}
    ]
    for tank in tank_types:
        if not frappe.db.exists("Tank Type", tank["tank_type_name"]):
            frappe.get_doc({
                "doctype": "Tank Type",
                "tank_type_name": tank["tank_type_name"]
            }).insert(ignore_permissions=True)

    # Treatment Parameters 
    treatment_parameters = [
        {
            "parameter_name": "Drain volume",
            "parameter_type": "Treatment",
            "parameter_uom": None
        },
        {
            "parameter_name": "Energy Consumed",
            "parameter_type": "Treatment",
            "parameter_uom": None
        },
        {
            "parameter_name": "Running Hours",
            "parameter_type": "Treatment",
            "parameter_uom": None
        },
        {
            "parameter_name": "Treated water production",
            "parameter_type": "Treatment",
            "parameter_uom": None
        },
        {
            "parameter_name": "Waste water treated volume",
            "parameter_type": "Treatment",
            "parameter_uom": None
        }
    ]

    for param in treatment_parameters:
        if not frappe.db.exists("Treatment parameter", param["parameter_name"]):
            frappe.get_doc({
                "doctype": "Treatment parameter",
                "parameter_name": param["parameter_name"],
                "parameter_type": param["parameter_type"],
                "parameter_uom": param["parameter_uom"]
            }).insert(ignore_permissions=True)