

import frappe
from frappe.utils import getdate
from calendar import monthrange
import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    days = [str(day).zfill(2) for day in range(1, 32)]
    return [
        {"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 250},
        {"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 80},
        *[{ "label": day, "fieldname": f"day_{day}", "fieldtype": "Data", "width": 100 } for day in days],
        {"label": "Total", "fieldname": "total", "fieldtype": "Data", "width": 100},
    ]

def get_data(filters):
    today = datetime.date.today()
    year = int(filters.get("year") or today.year)
    month = int(filters.get("month") or today.month)

    if not filters.get("project") or not filters.get("unit"):
        return []

    last_day = monthrange(year, month)[1]
    start_date = f"{year}-{str(month).zfill(2)}-01"
    end_date = f"{year}-{str(month).zfill(2)}-{last_day}"

    dor_list = frappe.get_all(
        "Daily Operation Report",
        filters={
            "project": filters.get("project"),
            "unit": filters.get("unit"),
            "docstatus": 1,
            "date": ["between", [start_date, end_date]]
        },
        fields=["name", "date"]
    )

    if not dor_list:
        return []

    child_tables = {}
    if filters.get("treatment_parameters"):
        child_tables["Treatment Parameters Table"] = {
            "doctype": "Treatment parameters table",
            "fields": ["treatment_parameter", "uom", "actual"],
            "label_field": "treatment_parameter",
            "unit_field": "uom",
            "value_field": "actual"
        }
    if filters.get("chemical_dilution"):
        child_tables["Chemical Dilution Table"] = {
            "doctype": "Chemical Dilution Table",
            "fields": ["chemical", "uom", "quantity_of_chemical", "volume_of_water", "dilution_rate"],
            "label_field": "chemical",
            "unit_field": "uom",
            "value_fields": ["quantity_of_chemical", "volume_of_water", "dilution_rate"]
        }
    if filters.get("chemical_usage"):
        child_tables["Chemical Usage Table"] = {
            "doctype": "Chemical Usage Table",
            "fields": ["chemical", "uom", "volume_consumed_l", "chemical_quantity_used_kg"],
            "label_field": "chemical",
            "unit_field": "uom",
            "value_fields": ["volume_consumed_l", "chemical_quantity_used_kg"]
        }
    if filters.get("influent_parameters"):
        child_tables["Influent Parameters Table"] = {
            "doctype": "Influent Parameters Table",
            "fields": ["parameter", "actual_value"],
            "label_field": "parameter",
            "unit_field": "",
            "value_field": "actual_value"
        }
    if filters.get("effluent_parameters"):
        child_tables["Effluent Parameters Table"] = {
            "doctype": "Effluent Parameters Table",
            "fields": ["parameter", "actual_value"],
            "label_field": "parameter",
            "unit_field": "",
            "value_field": "actual_value"
        }


    # child_tables = {
    #     "Treatment Parameters Table": {
    #         "doctype": "Treatment parameters table",
    #         "fields": ["treatment_parameter", "uom", "actual"],
    #         "label_field": "treatment_parameter",
    #         "unit_field": "uom",
    #         "value_field": "actual"
    #     },
    #     "Chemical Dilution Table": {
    #         "doctype": "Chemical Dilution Table",
    #         "fields": ["chemical", "uom", "quantity_of_chemical", "volume_of_water", "dilution_rate"],
    #         "label_field": "chemical",
    #         "unit_field": "uom",
    #         "value_fields": ["quantity_of_chemical", "volume_of_water", "dilution_rate"]
    #     },
    #     "Chemical Usage Table": {
    #         "doctype": "Chemical Usage Table",
    #         "fields": ["chemical", "uom", "volume_consumed_l", "chemical_quantity_used_kg"],
    #         "label_field": "chemical",
    #         "unit_field": "uom",
    #         "value_fields": ["volume_consumed_l", "chemical_quantity_used_kg"]
    #     },
    #     "Influent Parameters Table": {
    #         "doctype": "Influent Parameters Table",
    #         "fields": ["parameter", "actual_value"],
    #         "label_field": "parameter",
    #         "unit_field": "",
    #         "value_field": "actual_value"
    #     },
    #     "Effluent Parameters Table": {
    #         "doctype": "Effluent Parameters Table",
    #         "fields": ["parameter", "actual_value"],
    #         "label_field": "parameter",
    #         "unit_field": "",
    #         "value_field": "actual_value"
    #     }
    # }

    grouped_data = {}

    # Initialize all sections
    for section_name in child_tables.keys():
        grouped_data[section_name] = {}

    calculated_fields = []
    if filters.get("treatment_parameters"):
        # Initialize calculated fields under Treatment Parameters Table
        calculated_fields = [
            ("average_flow_rate", "Average Flow Rate", "m³/h"),
            ("energy_consumtion", "Energy Consumption", "kWh/m³")
        ]
    for key, label, unit in calculated_fields:
        if "Treatment Parameters Table" not in grouped_data:
            grouped_data["Treatment Parameters Table"] = {}
        if label not in grouped_data["Treatment Parameters Table"]:
            grouped_data["Treatment Parameters Table"][label] = {
                "unit": unit,
                "values": {}
            }

    for dor in dor_list:
        dor_doc = frappe.get_doc("Daily Operation Report", dor["name"])

        # Fill values for calculated fields
        for key, label, unit in calculated_fields:
            val = getattr(dor_doc, key, None)
            if val is not None:
                day_str = str(getdate(dor_doc.date).day).zfill(2)
                try:
                    val_float = float(val)
                except:
                    val_float = 0.0
                grouped_data["Treatment Parameters Table"][label]["values"][day_str] = val_float

        # Process child tables
        for section_name, config in child_tables.items():
            records = frappe.get_all(config["doctype"], filters={"parent": dor["name"]}, fields=config["fields"])
            for rec in records:
                label = rec.get(config["label_field"])
                unit = rec.get(config["unit_field"]) if config["unit_field"] and rec.get(config["unit_field"]) else ""
                if not label:
                    continue
                value_fields = config.get("value_fields") or [config.get("value_field")] or []
                for field in value_fields:
                    raw_value = rec.get(field)
                    try:
                        value = float(raw_value) if raw_value is not None else 0.0
                    except:
                        value = 0.0
                    if label not in grouped_data[section_name]:
                        grouped_data[section_name][label] = {
                            "unit": unit,
                            "values": {}
                        }
                    day_str = str(getdate(dor["date"]).day).zfill(2)
                    grouped_data[section_name][label]["values"][day_str] = value

    result = []

    for section, params in grouped_data.items():
        result.append({"description": f"**{section}**", "unit": ""})

        if section == "Treatment Parameters Table":
            # Separate calculated and regular parameters
            calculated_labels = [label for _, label, _ in calculated_fields]
            regular_params = {k: v for k, v in params.items() if k not in calculated_labels}
            calculated_params = {k: v for k, v in params.items() if k in calculated_labels}

            # Add regular parameters first
            for param, details in regular_params.items():
                row = {
                    "description": param,
                    "unit": details.get("unit", "")
                }
                total_sum = 0.0
                for day in range(1, last_day + 1):
                    day_str = str(day).zfill(2)
                    val = details["values"].get(day_str, 0)
                    row[f"day_{day_str}"] = str(val) if val != 0 else ""
                    if val:
                        total_sum += val
                row["total"] = str(total_sum) if total_sum != 0 else ""
                result.append(row)

            # Add calculated parameters section label
            result.append({"description": "-- Calculated Parameters --", "unit": ""})

            # Add calculated parameters
            for param, details in calculated_params.items():
                row = {
                    "description": param,
                    "unit": details.get("unit", "")
                }
                total_sum = 0.0
                for day in range(1, last_day + 1):
                    day_str = str(day).zfill(2)
                    val = details["values"].get(day_str, 0)
                    row[f"day_{day_str}"] = str(val) if val != 0 else ""
                    if val:
                        total_sum += val
                row["total"] = str(total_sum) if total_sum != 0 else ""
                result.append(row)

        else:
            for param, details in params.items():
                row = {
                    "description": param,
                    "unit": details.get("unit", "")
                }
                total_sum = 0.0
                for day in range(1, last_day + 1):
                    day_str = str(day).zfill(2)
                    val = details["values"].get(day_str, 0)
                    row[f"day_{day_str}"] = str(val) if val != 0 else ""
                    if val:
                        total_sum += val
                row["total"] = str(total_sum) if total_sum != 0 else ""
                result.append(row)

    return result
