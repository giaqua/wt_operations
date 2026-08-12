# Copyright (c) 2026, GiaquaTech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime
from frappe.utils.pdf import get_pdf
import json
from datetime import datetime

# All possible parameters
ALL_PARAMETERS = ["TDS.", "COD", "TSS", "pH", "Turbidity.", "Ammonia", "Oil & Grease", "BOD", "E.coli", "Total chlorine"]

# Parameter field name mapping
def param_to_fieldname(param):
    return param.strip().rstrip(".").lower().replace(" ", "_").replace(".", "")

def execute(filters=None):
    """Main report execution function"""
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    
    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)
    
    return columns, data

def validate_filters(filters):
    """Validate filter values"""
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date"))
    
    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))

def get_columns(filters):
    """Define report columns with dynamic parameter columns"""
    columns = []
    
    # Basic columns
    columns.extend([
        {
            "label": _("Sample ID"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Project Operation Water Sample",
            "width": 150
        },
        {
            "label": _("Sampling Date"),
            "fieldname": "sampling_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Site"),
            "fieldname": "site",
            "fieldtype": "Link",
            "options": "Project",
            "width": 150
        },
        {
            "label": _("Sample Type"),
            "fieldname": "sample_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Water Source"),
            "fieldname": "water_source",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "workflow_state",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Responsible"),
            "fieldname": "responsible",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Result Type"),
            "fieldname": "result_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Lab Receiving"),
            "fieldname": "lab_receiving_date",
            "fieldtype": "Date",
            "width": 130
        },
        {
            "label": _("Result Shared"),
            "fieldname": "result_shared_date",
            "fieldtype": "Date",
            "width": 130
        }
    ])
    
    # Get selected parameters from filters
    selected_parameters = filters.get("parameter")
    if selected_parameters and isinstance(selected_parameters, str):
        selected_parameters = (
            frappe.parse_json(selected_parameters)
            if selected_parameters.startswith("[")
            else selected_parameters.split(",")
        )
    
    parameters = selected_parameters or ALL_PARAMETERS
    
    # Add parameter columns
    for param in parameters:
        if param:
            columns.append({
                "label": _(param.rstrip(".")),
                "fieldname": param_to_fieldname(param),
                "fieldtype": "Float",
                "width": 110
            })
    
    # Add compliance column
    columns.append({
        "label": _("Compliance"),
        "fieldname": "compliance",
        "fieldtype": "Data",
        "width": 120
    })
    
    return columns, parameters

def get_data(filters, parameters):
    """Fetch and process report data"""
    conditions = get_conditions(filters)
    
    # Get samples
    query = f"""
        SELECT 
            name,
            sampling_date,
            site,
            sample_type,
            water_source,
            workflow_state,
            responsible,
            result_type,
            lab_receiving_date,
            result_shared_date
        FROM `tabProject Operation Water Sample`
        WHERE 1=1 {conditions}
        ORDER BY sampling_date DESC, creation DESC
    """
    
    samples = frappe.db.sql(query, filters, as_dict=1)
    
    if not samples:
        return []
    
    # Get parameter results for all samples
    sample_names = [s.name for s in samples]
    sample_names_str = ','.join(['%s'] * len(sample_names))
    
    results_query = f"""
        SELECT 
            parent,
            parameter,
            unit,
            inlet,
            contract_inlet
        FROM `tabSample Collection Details`
        WHERE parent IN ({sample_names_str})
    """
    
    results = frappe.db.sql(results_query, sample_names, as_dict=1)
    
    # Get required parameters
    params_query = f"""
        SELECT 
            parent,
            parameter
        FROM `tabParameters Required`
        WHERE parent IN ({sample_names_str})
        ORDER BY idx
    """
    
    params = frappe.db.sql(params_query, sample_names, as_dict=1)
    
    # Build data rows
    data = []
    for sample in samples:
        row = sample.copy()
        
        # Initialize parameter fields
        for p in parameters:
            if p:
                row[param_to_fieldname(p)] = None
        
        # Fill parameter values
        non_compliant = []
        for result in results:
            if result.parent == sample.name and result.parameter in parameters:
                fieldname = param_to_fieldname(result.parameter)
                row[fieldname] = flt(result.inlet) if result.inlet is not None else None
                
                # Check compliance
                if result.inlet and result.contract_inlet and result.inlet > result.contract_inlet:
                    non_compliant.append(result.parameter)
        
        # Determine overall compliance
        if non_compliant:
            row["compliance"] = f"Fail ({', '.join(non_compliant)})"
        else:
            row["compliance"] = "Pass"
        
        data.append(row)
    
    return data

def get_conditions(filters):
    """Build filter conditions"""
    conditions = []
    
    # Sample ID filter
    if filters.get("name"):
        conditions.append("name = %(name)s")
    
    # Date range filters
    if filters.get("from_date"):
        conditions.append("sampling_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("sampling_date <= %(to_date)s")
    
    # Site filter
    if filters.get("site"):
        conditions.append("site = %(site)s")
    
    # Sample type filter
    if filters.get("sample_type"):
        conditions.append("sample_type = %(sample_type)s")
    
    # Water source filter
    if filters.get("water_source"):
        conditions.append("water_source = %(water_source)s")
    
    # Status filter
    if filters.get("workflow_state"):
        conditions.append("workflow_state = %(workflow_state)s")
    
    # Result type filter
    if filters.get("result_type"):
        conditions.append("result_type = %(result_type)s")
    
    # Responsible filter
    if filters.get("responsible"):
        conditions.append("responsible = %(responsible)s")
    
    # Parameter filter - check if sample has specific parameter
    if filters.get("parameter_filter"):
        subquery = """
            EXISTS (
                SELECT 1 
                FROM `tabParameters Required` pr
                WHERE pr.parent = `tabProject Operation Water Sample`.name 
                AND pr.parameter = %(parameter_filter)s
            )
        """
        conditions.append(subquery)
    
    return " AND " + " AND ".join(conditions) if conditions else ""


# ============================
# COMPANY INFO
# ============================

def get_company_info():
    """Get company information for reports"""
    default_company = frappe.defaults.get_global_default("company")
    company = {}
    if default_company:
        company = frappe.db.get_value(
            "Company", default_company, ["company_name", "company_logo"], as_dict=True
        ) or {}
    
    return {
        "company_name": company.get("company_name"),
        "company_logo": company.get("company_logo"),
    }


# ============================
# TOTALS COMPUTATION
# ============================

def compute_totals(columns, data):
    """Sum every Float column across the data"""
    totals = {}
    for col in columns:
        if col.get("fieldtype") in ("Float", "Currency"):
            fieldname = col.get("fieldname")
            totals[fieldname] = flt(sum(flt(row.get(fieldname)) for row in data))
    return totals


# ============================
# PRINT FUNCTIONALITY
# ============================

@frappe.whitelist()
def get_print_data(filters=None):
    """Get complete data for print format"""
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)
    
    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)
    totals = compute_totals(columns, data)
    
    return {
        "columns": columns,
        "data": data,
        "totals": totals,
        "company": get_company_info(),
        "filters": filters,
        "parameters": parameters
    }

def get_print_html(columns, data, totals, filters, company, parameters):
    """Generate HTML for print output"""
    is_arabic = bool(filters.get("show_arabic_report"))
    
    # Filter summary
    filter_parts = []
    if filters.get("from_date") and filters.get("to_date"):
        filter_parts.append(f"Date: {filters.get('from_date')} to {filters.get('to_date')}")
    if filters.get("site"):
        filter_parts.append(f"Site: {filters.get('site')}")
    if filters.get("sample_type"):
        filter_parts.append(f"Type: {filters.get('sample_type')}")
    if filters.get("water_source"):
        filter_parts.append(f"Source: {filters.get('water_source')}")
    if filters.get("workflow_state"):
        filter_parts.append(f"Status: {filters.get('workflow_state')}")
    
    filter_summary = ", ".join(filter_parts) if filter_parts else "All Samples"
    
    # Company info
    company_name = company.get("company_name") or ""
    logo_url = company.get("company_logo") or ""
    if logo_url:
        logo_url = frappe.urllib.get_full_url(logo_url)
    
    # Title
    title = _("Water Sample Summary Report")
    if is_arabic:
        title = _("تقرير ملخص عينات المياه")
    
    # Date range
    date_range = f"{filters.get('from_date')} - {filters.get('to_date')}"
    generated_on = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
    
    # Column headers
    header_cells = []
    for col in columns:
        header_cells.append(f"<th>{frappe.utils.escape_html(_(col.get('label')))}</th>")
    
    # Data rows
    body_rows = []
    for idx, row in enumerate(data):
        cells = []
        for col in columns:
            fieldname = col.get("fieldname")
            raw = row.get(fieldname)
            
            # Format value
            if raw is None or raw == "":
                value = ""
            elif col.get("fieldtype") in ("Float", "Currency"):
                value = flt(raw)
                # Highlight if parameter exceeds limit
                if fieldname.startswith("param_"):
                    # Find contract limit
                    contract_field = f"contract_{fieldname.replace('param_', '')}"
                    # Note: We don't have contract limits in columns for print
                    # but we can still check if it's a parameter
                    pass
                value = f"{value:.2f}" if value else ""
            elif col.get("fieldtype") == "Date":
                value = frappe.utils.format_date(raw) if raw else ""
            else:
                value = frappe.utils.escape_html(str(raw))
            
            # Style for compliance
            if fieldname == "compliance" and value:
                if "Pass" in value:
                    value = f'<span style="color: green; font-weight: bold;">✓ {value}</span>'
                elif "Fail" in value:
                    value = f'<span style="color: red; font-weight: bold;">✗ {value}</span>'
            
            # Style for status
            if fieldname == "workflow_state" and value:
                status_class = value.lower()
                value = f'<span class="status-{status_class}">{value}</span>'
            
            align = "right" if col.get("fieldtype") in ("Float", "Currency") else ("right" if is_arabic else "left")
            cells.append(f'<td style="text-align:{align}">{value}</td>')
        
        row_class = "row-even" if idx % 2 == 0 else "row-odd"
        body_rows.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')
    
    # Totals row
    total_cells = []
    for idx, col in enumerate(columns):
        fieldname = col.get("fieldname")
        if totals and fieldname in totals and col.get("fieldtype") in ("Float", "Currency"):
            value = f"{flt(totals[fieldname]):.2f}"
            align = "right"
            if idx == 0:
                total_cells.append(f'<td style="text-align:{align};font-weight:bold;">{_("Total") if not is_arabic else "الإجمالي"}</td>')
            else:
                total_cells.append(f'<td style="text-align:{align};font-weight:bold;">{value}</td>')
        elif idx == 0:
            total_cells.append(f'<td style="text-align:{is_arabic and "right" or "left"};font-weight:bold;">{_("Total") if not is_arabic else "الإجمالي"}</td>')
        else:
            total_cells.append("<td></td>")
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="{is_arabic and 'ar' or 'en'}" dir="{is_arabic and 'rtl' or 'ltr'}">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            @page {{
                size: A4 landscape;
                margin: 14mm 10mm 16mm 10mm;
            }}
            
            * {{ box-sizing: border-box; }}
            body {{
                font-family: {is_arabic and "'Tahoma','Arial',sans-serif" or "'Segoe UI','Arial',sans-serif"};
                color: #1a1a1a;
                margin: 0;
                font-size: 10px;
            }}
            
            table.report-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            thead.report-header {{
                display: table-header-group;
            }}
            
            .brand-bar {{
                background: #010BCE;
                color: #fff;
                padding: 8px 12px;
            }}
            .brand-bar-inner {{
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .brand-bar img.logo {{
                max-height: 40px;
                max-width: 150px;
                background: #fff;
                padding: 2px 5px;
                border-radius: 3px;
            }}
            .brand-bar .company-name {{
                font-size: 14px;
                font-weight: 600;
            }}
            .brand-bar .report-title {{
                font-size: 13px;
                font-weight: 600;
                text-align: center;
                flex: 1;
            }}
            .brand-bar .meta {{
                font-size: 9px;
                text-align: {is_arabic and 'left' or 'right'};
                line-height: 1.4;
            }}
            .accent-strip {{
                height: 3px;
                background: #D50000;
            }}
            
            thead.report-header th {{
                background: #f1f2fb;
                color: #010BCE;
                border: 1px solid #ccc;
                padding: 5px 6px;
                font-size: 9.5px;
                font-weight: 700;
                white-space: nowrap;
            }}
            
            tbody td {{
                border: 1px solid #ddd;
                padding: 4px 6px;
                font-size: 9.5px;
            }}
            tr.row-even td {{ background: #ffffff; }}
            tr.row-odd td {{ background: #f8f9fd; }}
            tr {{ page-break-inside: avoid; }}
            
            tr.grand-total-row td {{
                border: 1px solid #ccc;
                border-top: 2px solid #D50000;
                padding: 5px 6px;
                background: #f1f2fb;
                font-size: 10px;
            }}
            
            .status-completed {{ color: green; font-weight: bold; }}
            .status-draft {{ color: orange; font-weight: bold; }}
            .status-submitted {{ color: blue; font-weight: bold; }}
            .status-cancelled {{ color: red; font-weight: bold; }}
            
            .print-toolbar {{
                position: fixed;
                top: 8px;
                right: 8px;
                z-index: 999;
            }}
            .print-toolbar button {{
                background: #010BCE;
                color: #fff;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 11px;
                cursor: pointer;
            }}
            @media print {{
                .print-toolbar {{ display: none; }}
            }}
            
            .filters-summary {{
                background: #f8f9fa;
                padding: 6px 12px;
                border-bottom: 1px solid #ddd;
                font-size: 9.5px;
            }}
        </style>
    </head>
    <body>
        <div class="print-toolbar">
            <button onclick="window.print()">{is_arabic and "طباعة" or "Print"}</button>
        </div>
        
        <table class="report-table">
            <thead class="report-header">
                <tr>
                    <th colspan="{len(columns)}" style="padding:0;border:none">
                        <div class="brand-bar">
                            <div class="brand-bar-inner">
                                {logo_url and f'<img class="logo" src="{logo_url}">' or '<div></div>'}
                                <div class="company-name">{company_name}</div>
                                <div class="report-title">{title}</div>
                                <div class="meta">
                                    {_("Period") if not is_arabic else "الفترة"}: {date_range}<br>
                                    {_("Generated") if not is_arabic else "تاريخ الطباعة"}: {generated_on}
                                </div>
                            </div>
                        </div>
                        <div class="accent-strip"></div>
                    </th>
                </tr>
                <tr>
                    {''.join(header_cells)}
                </tr>
            </thead>
            <tbody>
                {''.join(body_rows)}
                <tr class="grand-total-row">
                    {''.join(total_cells)}
                </tr>
            </tbody>
        </table>
        
        <script>
            window.addEventListener("load", function () {{
                setTimeout(function () {{ window.print(); }}, 300);
            }});
        </script>
    </body>
    </html>
    """
    
    return html

@frappe.whitelist()
def print_report(filters=None):
    """Generate PDF print of the report"""
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    
    # Get print data
    print_data = get_print_data(filters)
    
    # Generate HTML
    html = get_print_html(
        print_data["columns"],
        print_data["data"],
        print_data["totals"],
        print_data["filters"],
        print_data["company"],
        print_data.get("parameters", [])
    )
    
    # Generate PDF
    pdf = get_pdf(html, {
        "margin-top": "0.5in",
        "margin-right": "0.5in",
        "margin-bottom": "0.5in",
        "margin-left": "0.5in",
        "page-size": "A3",
        "orientation": "Landscape"
    })
    
    # Return PDF
    frappe.response.filename = f"Water_Sample_Summary_{now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
    frappe.response.filecontent = pdf
    frappe.response.type = "pdf"


# ============================
# EXCEL EXPORT FUNCTIONALITY
# ============================

@frappe.whitelist()
def get_excel(filters=None):
    """Generate Excel export of the report"""
    filters = frappe.parse_json(filters) if isinstance(filters, str) else frappe._dict(filters or {})
    validate_filters(filters)
    
    columns, parameters = get_columns(filters)
    data = get_data(filters, parameters)
    totals = compute_totals(columns, data)
    
    if not data:
        frappe.throw(_("No data to export. Please adjust your filters."))
    
    is_arabic = bool(filters.get("show_arabic_report"))
    company = get_company_info()
    
    # Build Excel workbook
    from io import BytesIO
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Water Sample Summary"
    if is_arabic:
        ws.sheet_view.rightToLeft = True
    
    n_cols = len(columns)
    
    # Colors
    HM_BLUE_HEX = "FF010BCE"
    HM_RED_HEX = "FFD50000"
    HEADER_FILL_HEX = "FFF1F2FB"
    ROW_ODD_FILL_HEX = "FFF8F9FD"
    
    blue_fill = PatternFill("solid", fgColor=HM_BLUE_HEX)
    red_top_border = Border(top=Side(style="medium", color=HM_RED_HEX))
    header_fill = PatternFill("solid", fgColor=HEADER_FILL_HEX)
    row_odd_fill = PatternFill("solid", fgColor=ROW_ODD_FILL_HEX)
    thin_border = Border(
        left=Side(style="thin", color="FFDDDDDD"),
        right=Side(style="thin", color="FFDDDDDD"),
        top=Side(style="thin", color="FFDDDDDD"),
        bottom=Side(style="thin", color="FFDDDDDD"),
    )
    
    white_bold = Font(color="FFFFFFFF", bold=True, size=11)
    white_regular = Font(color="FFFFFFFF", size=9)
    header_font = Font(color=HM_BLUE_HEX[2:], bold=True, size=10)
    body_font = Font(size=9)
    bold_font = Font(size=9, bold=True)
    
    row_num = 1
    
    # Title row
    company_name = company.get("company_name") or ""
    title = _("Water Sample Summary Report")
    if is_arabic:
        title = _("تقرير ملخص عينات المياه")
    
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=n_cols)
    cell = ws.cell(row=row_num, column=1, value=f"{company_name} - {title}" if company_name else title)
    cell.font = white_bold
    cell.fill = blue_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row_num].height = 28
    row_num += 1
    
    # Meta info row
    period_text = f"{_('Period') if not is_arabic else 'الفترة'}: {filters.get('from_date')} - {filters.get('to_date')}"
    generated_text = f"{_('Generated') if not is_arabic else 'تاريخ الطباعة'}: {now_datetime().strftime('%Y-%m-%d %H:%M')}"
    
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=n_cols)
    cell = ws.cell(row=row_num, column=1, value=f"{period_text}    |    {generated_text}")
    cell.font = white_regular
    cell.fill = blue_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row_num].height = 18
    row_num += 1
    
    # Headers row
    header_row_num = row_num
    for col_idx, col in enumerate(columns, start=1):
        cell = ws.cell(row=header_row_num, column=col_idx, value=str(_(col.get("label")) or ""))
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        align = "right" if is_arabic else "left"
        cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    ws.row_dimensions[header_row_num].height = 28
    row_num += 1
    
    # Data rows
    for idx, row_data in enumerate(data):
        for col_idx, col in enumerate(columns, start=1):
            fieldname = col.get("fieldname")
            raw = row_data.get(fieldname)
            
            cell = ws.cell(row=row_num, column=col_idx)
            
            if col.get("fieldtype") in ("Float", "Currency") and raw is not None:
                cell.value = flt(raw)
                cell.number_format = "0.00"
            else:
                cell.value = raw
            
            cell.font = body_font
            cell.border = thin_border
            align = "right" if col.get("fieldtype") in ("Float", "Currency") else ("right" if is_arabic else "left")
            cell.alignment = Alignment(horizontal=align, vertical="center")
            
            if idx % 2 == 1:
                cell.fill = row_odd_fill
        
        row_num += 1
    
    # Totals row
    total_label = _("Total") if not is_arabic else "الإجمالي"
    for col_idx, col in enumerate(columns, start=1):
        fieldname = col.get("fieldname")
        cell = ws.cell(row=row_num, column=col_idx)
        cell.border = red_top_border
        cell.font = bold_font
        cell.fill = header_fill
        
        if col_idx == 1:
            cell.value = total_label
            align = "right" if is_arabic else "left"
            cell.alignment = Alignment(horizontal=align, vertical="center")
        elif totals and fieldname in totals and col.get("fieldtype") in ("Float", "Currency"):
            cell.value = flt(totals[fieldname])
            cell.number_format = "0.00"
            cell.alignment = Alignment(horizontal="right", vertical="center")
    
    # Column widths
    for col_idx, col in enumerate(columns, start=1):
        px_width = col.get("width") or 100
        excel_width = max(10, min(40, round(px_width / 7)))
        ws.column_dimensions[get_column_letter(col_idx)].width = excel_width
    
    # Freeze panes
    ws.freeze_panes = ws.cell(row=header_row_num + 1, column=1)
    
    # Save to BytesIO
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    
    # Set response
    filename = f"Water_Sample_Summary_{now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"
    frappe.response["filename"] = filename
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"] = "binary"