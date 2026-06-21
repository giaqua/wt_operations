# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, date


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    
    # Group data by year-month if requested
    if filters and filters.get("group_by_month"):
        grouped_data = group_by_year_month(data)
        report_summary, primitive_summary = get_summary_data(grouped_data, "pending_with")
        chart = get_chart_data(report_summary)
        message = get_dashboard_html(grouped_data, report_summary)
    else:
        report_summary, primitive_summary = get_summary_data(data, "pending_with")
        chart = get_chart_data(report_summary)
        message = get_dashboard_html(data, report_summary)
    
    return columns, data, message


def group_by_year_month(data):
    """
    Groups data by year-month based on tq_date.
    Returns data with an additional grouping key.
    """
    grouped_data = []
    
    for row in data:
        if row.get("tq_date"):
            # Format date as YYYY-MM
            month_key = row["tq_date"].strftime("%Y-%m")
            row["month_group"] = month_key
            grouped_data.append(row)
        else:
            row["month_group"] = "No Date"
            grouped_data.append(row)
    
    return grouped_data


def get_monthly_summary(data):
    """
    Returns summary statistics grouped by year-month.
    """
    monthly_stats = {}
    
    for row in data:
        month = row.get("month_group", "Unknown")
        if month not in monthly_stats:
            monthly_stats[month] = {
                "total": 0,
                "completed": 0,
                "pending_sales": 0,
                "pending_tech": 0,
                "pending_lab": 0,
                "avg_delay": 0,
                "delays": []
            }
        
        monthly_stats[month]["total"] += 1
        
        pending_with = row.get("pending_with", "")
        if pending_with == "Completed":
            monthly_stats[month]["completed"] += 1
        elif pending_with == "Sales":
            monthly_stats[month]["pending_sales"] += 1
        elif pending_with == "Technical":
            monthly_stats[month]["pending_tech"] += 1
        elif pending_with == "Lab":
            monthly_stats[month]["pending_lab"] += 1
        
        if pending_with != "Completed":
            monthly_stats[month]["delays"].append(row.get("delay_days", 0))
    
    # Calculate averages
    for month, stats in monthly_stats.items():
        if stats["delays"]:
            stats["avg_delay"] = round(sum(stats["delays"]) / len(stats["delays"]), 1)
        stats["completion_rate"] = round((stats["completed"] / stats["total"] * 100) if stats["total"] else 0, 1)
    
    return monthly_stats


def get_dashboard_html(data, report_summary):
    total         = len(data)
    completed     = sum(1 for r in data if r.get("pending_with") == "Completed")
    pending_sales = sum(1 for r in data if r.get("pending_with") == "Sales")
    pending_tech  = sum(1 for r in data if r.get("pending_with") == "Technical")
    pending_lab   = sum(1 for r in data if r.get("pending_with") == "Lab")
    in_progress   = total - completed

    open_delays = [r.get("delay_days", 0) for r in data if r.get("pending_with") != "Completed"]
    avg_delay   = round(sum(open_delays) / len(open_delays), 1) if open_delays else 0
    max_delay   = max(open_delays) if open_delays else 0

    delay_0_5  = sum(1 for d in open_delays if d <= 5)
    delay_6_15 = sum(1 for d in open_delays if 6 <= d <= 15)
    delay_16up = sum(1 for d in open_delays if d > 15)

    stage_keys   = ["visit_request","site_visit","water_sample","lab_test_result","technical_proposal","customer_proposal"]
    stage_labels = ["Visit Request","Site Visit","Water Sample","Lab Result","Tech Proposal","Customer Prop."]
    stage_icons  = ["VR","SV","WS","LR","TP","CP"]
    stage_colors = ["#378ADD","#534AB7","#BA7517","#D85A30","#1D9E75","#888780"]
    stage_counts = [sum(1 for r in data if (r.get(k) or 0) > 0) for k in stage_keys]
    funnel_max   = max([pending_sales, pending_tech, pending_lab, 1])

    comp_pct    = round(completed / total * 100) if total else 0
    incomp_pct  = 100 - comp_pct

    # ── Build JS arrays without f-strings ──────────────────────────────────
    dept_values_js = "[" + str(pending_sales) + "," + str(pending_tech) + "," + str(pending_lab) + "]"

    stage_parts = []
    for i in range(len(stage_labels)):
        pct_of_total = round(stage_counts[i] / total * 100) if total else 0
        smx = max(stage_counts) if stage_counts else 1
        bar_pct = round(stage_counts[i] / smx * 100) if smx else 0
        part = (
            "{label:'" + stage_labels[i] + "'"
            + ",count:" + str(stage_counts[i])
            + ",barPct:" + str(bar_pct)
            + ",pctOf:" + str(pct_of_total)
            + ",color:'" + stage_colors[i] + "'"
            + ",icon:'" + stage_icons[i] + "'}"
        )
        stage_parts.append(part)
    stage_js = "[" + ",".join(stage_parts) + "]"

    delay_parts = [
        "{label:'0\u20135 days',count:" + str(delay_0_5)  + ",fill:'#1D9E75',bg:'#EAF3DE',tc:'#3B6D11'}",
        "{label:'6\u201315 days',count:" + str(delay_6_15) + ",fill:'#BA7517',bg:'#FAEEDA',tc:'#633806'}",
        "{label:'16+ days',count:" + str(delay_16up) + ",fill:'#E24B4A',bg:'#FCEBEB',tc:'#791F1F'}",
    ]
    delay_js = "[" + ",".join(delay_parts) + "]"

    # ── KPI HTML (plain string concatenation) ──────────────────────────────
    def kpi(bar_color, lbl, val, val_color, sub):
        return (
            '<div class="tq-kpi">'
            + '<div class="tq-kpi-bar" style="background:' + bar_color + '"></div>'
            + '<span class="tq-kpi-lbl">' + lbl + '</span>'
            + '<span class="tq-kpi-val" style="color:' + val_color + '">' + str(val) + '</span>'
            + '<span class="tq-kpi-sub">' + sub + '</span>'
            + '</div>'
        )

    kpi_row1 = (
        kpi('#378ADD', 'Total TQs',   total,        '#185FA5', 'all questionnaires')
        + kpi("#D16105", 'Pending sales',     pending_sales, '#D16105', 'awaiting action')
        + kpi('#534AB7', 'Pending technical', pending_tech,  '#3C3489', 'awaiting action')
        + kpi('#D85A30', 'Pending lab',       pending_lab,   '#993C1D', 'awaiting action')
    )
    kpi_row2 = (
        kpi('#1D9E75', 'Completed',  completed,    '#0F6E56', str(comp_pct) + '% completion rate')
        + kpi('#BA7517', 'In progress', in_progress, '#854F0B', 'open TQs')
        + kpi('#E24B4A', 'Avg delay',  str(avg_delay) + 'd', '#A32D2D', 'across open TQs')
        + kpi('#E24B4A', 'Max delay',         str(max_delay) + 'd', '#A32D2D', 'longest open case')
    )

    # ── Dept chart aria label ───────────────────────────────────────────────
    dept_aria = "Horizontal bar: Sales " + str(pending_sales) + " Technical " + str(pending_tech) + " Lab " + str(pending_lab)
    donut_aria = str(comp_pct) + "% completed"
    open_tqs_label = str(in_progress) + " open TQs"
    donut_completed_label = str(completed) + " of " + str(total) + " TQs"

    # ── Assemble final HTML (plain string, no f-string) ────────────────────
    html = (
"""<style>
#tqdash{all:initial;display:block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;color:#1F2937;line-height:1.4;padding:4px 0 16px;width:100%}
#tqdash *{box-sizing:border-box;margin:0;padding:0;line-height:inherit}
#tqdash .tq-hdr{display:flex;align-items:center;justify-content:space-between;padding:8px 0 12px;border-bottom:1px solid #E5E7EB;margin-bottom:12px}
#tqdash .tq-title{display:flex;align-items:center;gap:7px;font-size:13px;font-weight:700;color:#1F2937}
#tqdash .tq-actions{display:flex;gap:6px}
#tqdash .tq-btn{display:inline-flex;align-items:center;gap:5px;background:#F3F4F6;border:1px solid #E5E7EB;border-radius:6px;padding:4px 10px;font-size:11px;font-weight:600;cursor:pointer;color:#6B7280;font-family:inherit;transition:background .12s}
#tqdash .tq-btn:hover{background:#E9EBF0}
#tqdash .tq-btn.on{background:#EFF6FF;border-color:#BFDBFE;color:#1D4ED8}
#tqdash .tq-sec-lbl{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#9CA3AF;margin-bottom:8px;display:block}
#tqdash .tq-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-bottom:7px}
#tqdash .tq-kpi{background:#F9FAFB;border:1px solid #F3F4F6;border-radius:8px;padding:10px 12px 9px 15px;position:relative;overflow:hidden}
#tqdash .tq-kpi-bar{position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:0}
#tqdash .tq-kpi-lbl{font-size:10px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;display:block}
#tqdash .tq-kpi-val{font-size:22px;font-weight:800;line-height:1;margin-bottom:2px;display:block}
#tqdash .tq-kpi-sub{font-size:10px;color:#9CA3AF;display:block}
#tqdash .tq-div{height:1px;background:#E5E7EB;margin:12px 0;border:none}
/* Three column layout for cards */
#tqdash .tq-charts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
#tqdash .tq-card{background:#fff;border:1px solid #E5E7EB;border-radius:9px;padding:16px 18px;min-width:0}
#tqdash .tq-card.wide{grid-column:1/-1}
#tqdash .tq-card-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
#tqdash .tq-card-ttl{font-size:11px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.6px}
#tqdash .tq-card-meta{font-size:10px;color:#9CA3AF}
#tqdash .tq-legend{display:flex;gap:12px;margin-bottom:9px;flex-wrap:wrap}
#tqdash .tq-leg{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:#4B5563}
#tqdash .tq-leg-sq{display:inline-block;width:9px;height:9px;border-radius:2px;flex-shrink:0}
#tqdash .tq-chart-wrap{position:relative;width:100%;height:130px}
#tqdash .tq-stage-row{display:flex;align-items:center;gap:7px;margin-bottom:8px}
#tqdash .tq-stage-icon{width:22px;height:22px;min-width:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;flex-shrink:0}
#tqdash .tq-stage-lbl{font-size:11px;color:#4B5563;width:96px;min-width:96px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#tqdash .tq-stage-track{flex:1;min-width:0;background:#F3F4F6;border-radius:3px;height:7px;overflow:hidden}
#tqdash .tq-stage-fill{height:100%;border-radius:3px}
#tqdash .tq-stage-n{font-size:11px;font-weight:700;color:#1F2937;width:22px;min-width:22px;text-align:right;flex-shrink:0}
#tqdash .tq-stage-pct{font-size:10px;color:#9CA3AF;width:30px;min-width:30px;text-align:right;flex-shrink:0}
#tqdash .tq-dly-row{display:flex;align-items:center;gap:7px;margin-bottom:8px}
#tqdash .tq-dly-pill{font-size:10px;font-weight:700;padding:3px 7px;border-radius:20px;width:68px;min-width:68px;text-align:center;flex-shrink:0;display:inline-block}
#tqdash .tq-dly-track{flex:1;min-width:0;background:#F3F4F6;border-radius:3px;height:7px;overflow:hidden}
#tqdash .tq-dly-fill{height:100%;border-radius:3px}
#tqdash .tq-dly-n{font-size:12px;font-weight:700;color:#1F2937;width:22px;min-width:22px;text-align:right;flex-shrink:0}
#tqdash .tq-donut-wrap{display:flex;align-items:center;gap:16px;padding-top:11px;border-top:1px solid #F3F4F6;margin-top:11px}
#tqdash .tq-dstat{margin-bottom:10px}
#tqdash .tq-dstat-lbl{font-size:10px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.5px;font-weight:700;margin-bottom:1px;display:block}
#tqdash .tq-dstat-val{font-size:17px;font-weight:800;display:block;line-height:1.1}
#tqdash .tq-dstat-sub{font-size:10px;color:#9CA3AF;display:block}
#tqdash .tq-hidden{display:none!important}

/* Monthly Summary Table Styles */
.tq-monthly-table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
.tq-monthly-table th{background:#F9FAFB;text-align:left;padding:8px 12px;font-weight:600;color:#6B7280;border-bottom:2px solid #E5E7EB}
.tq-monthly-table td{padding:8px 12px;border-bottom:1px solid #F3F4F6;color:#1F2937}
.tq-monthly-table tr:hover{background:#FAFBFC}
.tq-monthly-table .completed{color:#0F6E56;font-weight:600}
.tq-monthly-table .pending-sales{color:#D16105;font-weight:600}
.tq-monthly-table .pending-tech{color:#3C3489;font-weight:600}
.tq-monthly-table .pending-lab{color:#993C1D;font-weight:600}
.tq-monthly-card{margin-top:16px}

/* Popup Styles */
.tq-popup-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;justify-content:center;align-items:center;animation:fadeIn .3s}
.tq-popup-overlay.active{display:flex}
.tq-popup{background:#fff;border-radius:16px;max-width:900px;width:95%;max-height:90vh;overflow-y:auto;padding:0;box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:slideUp .3s}
.tq-popup-header{display:flex;justify-content:space-between;align-items:center;padding:20px 28px;border-bottom:1px solid #E5E7EB;background:#FAFBFC;border-radius:16px 16px 0 0}
.tq-popup-header h2{font-size:18px;font-weight:700;color:#1F2937;margin:0}
.tq-popup-close{background:none;border:none;font-size:28px;cursor:pointer;color:#9CA3AF;padding:0;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all .2s}
.tq-popup-close:hover{background:#F3F4F6;color:#1F2937}
.tq-popup-body{padding:24px 28px}
.tq-popup-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px}
.tq-popup-item{background:#F9FAFB;border-radius:10px;padding:14px 18px;border:1px solid #F3F4F6}
.tq-popup-item .label{font-size:11px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:4px}
.tq-popup-item .value{font-size:15px;font-weight:600;color:#1F2937;display:block}
.tq-popup-item .value a{color:#1D4ED8;text-decoration:none;font-weight:600}
.tq-popup-item .value a:hover{text-decoration:underline}
.tq-popup-section{margin-top:20px}
.tq-popup-section-title{font-size:13px;font-weight:700;color:#374151;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.tq-popup-section-title .badge{font-size:10px;font-weight:600;background:#EFF6FF;color:#1D4ED8;padding:2px 10px;border-radius:12px}
.tq-action-buttons{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;padding-top:16px;border-top:1px solid #F3F4F6}
.tq-action-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;border:none;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;text-decoration:none;font-family:inherit}
.tq-action-btn-primary{background:#1D4ED8;color:#fff}
.tq-action-btn-primary:hover{background:#1E40AF;transform:translateY(-1px);box-shadow:0 4px 12px rgba(29,78,216,0.3)}
.tq-action-btn-success{background:#0F6E56;color:#fff}
.tq-action-btn-success:hover{background:#0A4F3E;transform:translateY(-1px);box-shadow:0 4px 12px rgba(15,110,86,0.3)}
.tq-action-btn-warning{background:#D97706;color:#fff}
.tq-action-btn-warning:hover{background:#B45309;transform:translateY(-1px);box-shadow:0 4px 12px rgba(217,119,6,0.3)}
.tq-action-btn-secondary{background:#F3F4F6;color:#374151}
.tq-action-btn-secondary:hover{background:#E5E7EB;transform:translateY(-1px)}
.tq-popup-status{display:inline-flex;align-items:center;gap:6px;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600}
.tq-popup-status.completed{background:#D1FAE5;color:#065F46}
.tq-popup-status.pending{background:#FEF3C7;color:#92400E}
.tq-popup-status.inprogress{background:#DBEAFE;color:#1E40AF}
.tq-popup-status.lab{background:#FEE2E2;color:#991B1B}
.tq-popup-status .dot{width:6px;height:6px;border-radius:50%;display:inline-block}
.tq-popup-status.completed .dot{background:#065F46}
.tq-popup-status.pending .dot{background:#92400E}
.tq-popup-status.inprogress .dot{background:#1E40AF}
.tq-popup-status.lab .dot{background:#991B1B}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{transform:translateY(20px);opacity:0}to{transform:translateY(0);opacity:1}}
.tq-table-wrap{overflow-x:auto;margin-top:8px}
.tq-table-wrap table{width:100%;border-collapse:collapse;font-size:13px}
.tq-table-wrap th{background:#F9FAFB;text-align:left;padding:10px 14px;font-weight:600;color:#6B7280;border-bottom:2px solid #E5E7EB}
.tq-table-wrap td{padding:10px 14px;border-bottom:1px solid #F3F4F6;color:#1F2937}
.tq-table-wrap tr:hover{background:#FAFBFC}
.tq-detail-btn{background:#1D4ED8;color:#fff;border:none;border-radius:6px;padding:4px 12px;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;font-family:inherit}
.tq-detail-btn:hover{background:#1E40AF;transform:translateY(-1px);box-shadow:0 2px 8px rgba(29,78,216,0.3)}
</style>
<div id="tqdash">
  <div class="tq-hdr">
    <div class="tq-title">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#378ADD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>
      TQ pipeline dashboard
    </div>
    <div class="tq-actions">
      <button class="tq-btn on" id="tqBtnK" onclick="tqToggle('kpis')">&#9783; KPIs</button>
      <button class="tq-btn on" id="tqBtnC" onclick="tqToggle('charts')">&#9641; Charts</button>
    </div>
  </div>

  <div id="tqKpis">
    <span class="tq-sec-lbl">Overview</span>
    <div class="tq-kpis">""" + kpi_row1 + """</div>
    <div class="tq-kpis" style="margin-bottom:0">""" + kpi_row2 + """</div>
  </div>

  <hr class="tq-div" id="tqDiv1">

  <div id="tqCharts">
    <span class="tq-sec-lbl">Analytics</span>
    <div class="tq-charts">

      <div class="tq-card">
        <div class="tq-card-hdr">
          <span class="tq-card-ttl">Pending by department</span>
          <span class="tq-card-meta">""" + open_tqs_label + """</span>
        </div>
        <div class="tq-legend" id="tqDeptLeg"></div>
        <div class="tq-chart-wrap">
          <canvas id="tqDeptC" role="img" aria-label=\"""" + dept_aria + """\">""" + dept_aria + """.</canvas>
        </div>
      </div>

      <div class="tq-card">
        <div class="tq-card-hdr">
          <span class="tq-card-ttl">Stage funnel</span>
          <span class="tq-card-meta">by step reached</span>
        </div>
        <div id="tqStage"></div>
      </div>

      <div class="tq-card">
        <div class="tq-card-hdr">
          <span class="tq-card-ttl">Delay distribution</span>
          <span class="tq-card-meta">open TQs only</span>
        </div>
        <div id="tqDelay"></div>
        <div class="tq-donut-wrap">
          <div style="position:relative;width:80px;height:80px;min-width:80px;flex-shrink:0">
            <canvas id="tqDonut" width="80" height="80" role="img" aria-label=\"""" + donut_aria + """\">""" + donut_aria + """.</canvas>
          </div>
          <div>
            <div class="tq-dstat">
              <span class="tq-dstat-lbl">Completion</span>
              <span class="tq-dstat-val" style="color:#1D9E75">""" + str(comp_pct) + """%</span>
              <span class="tq-dstat-sub">""" + donut_completed_label + """</span>
            </div>
            <div class="tq-dstat">
              <span class="tq-dstat-lbl">In progress</span>
              <span class="tq-dstat-val" style="color:#E24B4A">""" + str(incomp_pct) + """%</span>
              <span class="tq-dstat-sub">""" + str(in_progress) + """ open</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Summary Card (spans full width) -->
      <div class="tq-card wide tq-monthly-card">
        <div class="tq-card-hdr">
          <span class="tq-card-ttl">Monthly Summary</span>
          <span class="tq-card-meta">by year-month</span>
        </div>
        <div id="tqMonthlySummary">
          <!-- Monthly summary table will be injected here -->
        </div>
      </div>

    </div>
  </div>
</div>

<!-- Popup Container -->
<div class="tq-popup-overlay" id="tqPopupOverlay" onclick="if(event.target===this)closeTQPopup()">
  <div class="tq-popup" id="tqPopup">
    <div class="tq-popup-header">
      <h2 id="tqPopupTitle">Technical Questionnaire Details</h2>
      <button class="tq-popup-close" onclick="closeTQPopup()">×</button>
    </div>
    <div class="tq-popup-body" id="tqPopupBody">
      <!-- Popup content will be injected here -->
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
(function(){
var dept={labels:['Sales','Technical','Lab'],values:""" + dept_values_js + """,colors:['#378ADD','#534AB7','#D85A30']};
var stages=""" + stage_js + """;
var delays=""" + delay_js + """;
var compPct=""" + str(comp_pct) + """;

// Store data for popup
var tqData = """ + frappe.as_json(data) + """;

var leg=document.getElementById('tqDeptLeg');
if(leg){leg.innerHTML=dept.labels.map(function(l,i){return '<span class="tq-leg"><span class="tq-leg-sq" style="background:'+dept.colors[i]+'"></span>'+l+' ('+dept.values[i]+')</span>';}).join('');}

if(window.Chart){
  new Chart(document.getElementById('tqDeptC'),{
    type:'bar',
    data:{labels:dept.labels,datasets:[{data:dept.values,backgroundColor:dept.colors,borderRadius:4,borderSkipped:false,barThickness:24}]},
    options:{
      indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return ' '+c.raw+' TQs';}}}},
      scales:{
        x:{grid:{color:'rgba(0,0,0,0.05)'},ticks:{font:{size:11},color:'#9CA3AF'},border:{display:false}},
        y:{grid:{display:false},ticks:{font:{size:12},color:'#374151'},border:{display:false}}
      },
      layout:{padding:{right:8}}
    }
  });
}

var st=document.getElementById('tqStage');
if(st){
  st.innerHTML=stages.map(function(s){
    var bp=s.count>0?Math.max(s.barPct,3):0;
    return '<div class="tq-stage-row">'
      +'<div class="tq-stage-icon" style="background:'+s.color+'22;color:'+s.color+'">'+s.icon+'</div>'
      +'<div class="tq-stage-lbl" title="'+s.label+'">'+s.label+'</div>'
      +'<div class="tq-stage-track"><div class="tq-stage-fill" style="width:'+bp+'%;background:'+s.color+'"></div></div>'
      +'<div class="tq-stage-n">'+s.count+'</div>'
      +'<div class="tq-stage-pct">'+s.pctOf+'%</div>'
      +'</div>';
  }).join('');
}

var dl=document.getElementById('tqDelay');
if(dl){
  var dmx=Math.max.apply(null,delays.map(function(d){return d.count;}))||1;
  dl.innerHTML=delays.map(function(d){
    var bp=d.count>0?Math.max(Math.round(d.count/dmx*100),3):0;
    return '<div class="tq-dly-row">'
      +'<div class="tq-dly-pill" style="background:'+d.bg+';color:'+d.tc+'">'+d.label+'</div>'
      +'<div class="tq-dly-track"><div class="tq-dly-fill" style="width:'+bp+'%;background:'+d.fill+'"></div></div>'
      +'<div class="tq-dly-n">'+d.count+'</div>'
      +'</div>';
  }).join('');
}

var dc=document.getElementById('tqDonut');
if(dc){
  var ctx=dc.getContext('2d');
  var cx=40,cy=40,r=30,lw=9;
  ctx.lineWidth=lw;ctx.strokeStyle='#FECACA';
  ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();
  if(compPct>0){
    ctx.strokeStyle='#1D9E75';ctx.lineCap='round';
    ctx.beginPath();ctx.arc(cx,cy,r,-Math.PI/2,-Math.PI/2+Math.PI*2*(compPct/100));ctx.stroke();
  }
  ctx.fillStyle=compPct>0?'#0F6E56':'#A32D2D';
  ctx.font='700 11px -apple-system,sans-serif';
  ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(compPct+'%',cx,cy);
}

// Function to render monthly summary
function renderMonthlySummary(data) {
    var container = document.getElementById('tqMonthlySummary');
    if (!container) return;
    
    // Group data by month
    var monthlyData = {};
    data.forEach(function(row) {
        if (!row.tq_date) return;
        var date = new Date(row.tq_date);
        var monthKey = date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0');
        
        if (!monthlyData[monthKey]) {
            monthlyData[monthKey] = {
                total: 0,
                completed: 0,
                pending_sales: 0,
                pending_tech: 0,
                pending_lab: 0,
                delays: []
            };
        }
        
        monthlyData[monthKey].total += 1;
        if (row.pending_with === 'Completed') {
            monthlyData[monthKey].completed += 1;
        } else if (row.pending_with === 'Sales') {
            monthlyData[monthKey].pending_sales += 1;
        } else if (row.pending_with === 'Technical') {
            monthlyData[monthKey].pending_tech += 1;
        } else if (row.pending_with === 'Lab') {
            monthlyData[monthKey].pending_lab += 1;
        }
        
        if (row.pending_with !== 'Completed' && row.delay_days) {
            monthlyData[monthKey].delays.push(row.delay_days);
        }
    });
    
    // Sort months
    var sortedMonths = Object.keys(monthlyData).sort();
    
    if (sortedMonths.length === 0) {
        container.innerHTML = '<p style="color:#9CA3AF;font-size:13px;padding:12px;text-align:center;">No data available for monthly summary</p>';
        return;
    }
    
    // Build HTML table
    var html = '<div class="tq-table-wrap"><table class="tq-monthly-table">';
    html += '<thead><tr>' +
        '<th>Month</th>' +
        '<th>Total</th>' +
        '<th class="completed">Completed</th>' +
        '<th class="pending-sales">Pending Sales</th>' +
        '<th class="pending-tech">Pending Technical</th>' +
        '<th class="pending-lab">Pending Lab</th>' +
        '<th>Avg Delay</th>' +
        '<th>Completion Rate</th>' +
        '</tr></thead><tbody>';
    
    sortedMonths.forEach(function(month) {
        var stats = monthlyData[month];
        var avgDelay = stats.delays.length ? (stats.delays.reduce(function(a,b) { return a + b; }, 0) / stats.delays.length).toFixed(1) : '0';
        var completionRate = stats.total ? ((stats.completed / stats.total) * 100).toFixed(1) : '0';
        
        // Format month display
        var dateParts = month.split('-');
        var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var displayMonth = monthNames[parseInt(dateParts[1]) - 1] + ' ' + dateParts[0];
        
        var rateColor = completionRate >= 70 ? '#0F6E56' : completionRate >= 40 ? '#D97706' : '#E24B4A';
        
        html += '<tr>' +
            '<td><strong>' + displayMonth + '</strong></td>' +
            '<td>' + stats.total + '</td>' +
            '<td class="completed">' + stats.completed + '</td>' +
            '<td class="pending-sales">' + stats.pending_sales + '</td>' +
            '<td class="pending-tech">' + stats.pending_tech + '</td>' +
            '<td class="pending-lab">' + stats.pending_lab + '</td>' +
            '<td>' + avgDelay + 'd</td>' +
            '<td><span style="color:' + rateColor + ';font-weight:600;">' + completionRate + '%</span></td>' +
            '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

var vis={kpis:true,charts:true};
window.tqToggle=function(sec){
  vis[sec]=!vis[sec];
  if(sec==='kpis'){
    document.getElementById('tqKpis').classList.toggle('tq-hidden',!vis.kpis);
    document.getElementById('tqBtnK').classList.toggle('on',vis.kpis);
  } else {
    document.getElementById('tqCharts').classList.toggle('tq-hidden',!vis.charts);
    document.getElementById('tqBtnC').classList.toggle('on',vis.charts);
  }
  document.getElementById('tqDiv1').classList.toggle('tq-hidden',!vis.kpis&&!vis.charts);
};

// Helper function to get document link
function getDocLink(doctype, docname) {
    if (!docname) return '#';
    var doctypeMap = {
        'water_sample': 'water-sample',
        'lab_test_result': 'lab-test-result',
        'technical_proposal': 'wwtp-technical-proposal',
        'customer_proposal': 'customer-proposal',
        'technical_questionnaire': 'wwtp-technical-questionnaire'
    };
    var urlDoctype = doctypeMap[doctype] || doctype;
    return '/app/' + urlDoctype + '/' + docname;
}

// Popup Functions
window.openTQPopup = function(tqName) {
  var row = tqData.find(function(d) { return d.technical_questionnaire === tqName; });
  if (!row) return;
  
  var popup = document.getElementById('tqPopupOverlay');
  var body = document.getElementById('tqPopupBody');
  var title = document.getElementById('tqPopupTitle');
  
  title.textContent = row.lead_name + ' - Technical Questionnaire';
  
  // Status badge
  var statusMap = {
    'Completed': '<span class="tq-popup-status completed"><span class="dot"></span> Completed</span>',
    'Sales': '<span class="tq-popup-status pending"><span class="dot"></span> Pending: Sales</span>',
    'Technical': '<span class="tq-popup-status inprogress"><span class="dot"></span> Pending: Technical</span>',
    'Lab': '<span class="tq-popup-status lab"><span class="dot"></span> Pending: Lab</span>'
  };
  var statusHtml = statusMap[row.pending_with] || '<span class="tq-popup-status pending"><span class="dot"></span> '+row.pending_with+'</span>';
  
  // Build popup content
  body.innerHTML = 
    '<div class="tq-popup-grid">' +
      '<div class="tq-popup-item">' +
        '<span class="label">Questionnaire</span>' +
        '<span class="value"><a href="'+getDocLink('technical_questionnaire', row.technical_questionnaire)+'" target="_blank">'+row.technical_questionnaire+'</a></span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Status</span>' +
        '<span class="value">'+statusHtml+'</span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Workflow State</span>' +
        '<span class="value">'+(row.wtq_workflow_state || 'N/A')+'</span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Lead</span>' +
        '<span class="value"><a href="/app/lead/'+row.lead_id+'" target="_blank">'+row.lead_name+'</a></span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Date</span>' +
        '<span class="value">'+(row.tq_date ? row.tq_date : 'N/A')+'</span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Progress</span>' +
        '<span class="value">'+(row.achieved_operations || 0)+'%</span>' +
      '</div>' +
      '<div class="tq-popup-item">' +
        '<span class="label">Delay Days</span>' +
        '<span class="value" style="color:'+(row.delay_days > 15 ? '#E24B4A' : row.delay_days > 5 ? '#D97706' : '#0F6E56')+'">'+(row.delay_days || 0)+' days</span>' +
      '</div>' +
    '</div>' +
    
    '<div class="tq-popup-section">' +
      '<div class="tq-popup-section-title">Workflow Stages <span class="badge">'+ 
        (row.achieved_operations >= 100 ? 'Complete' : row.achieved_operations >= 70 ? 'Advanced' : row.achieved_operations >= 40 ? 'In Progress' : 'Initial') +
      '</span></div>' +
      '<div class="tq-table-wrap">' +
        '<table>' +
          '<thead><tr><th>Stage</th><th>Status</th><th>Date</th><th>Link</th></tr></thead>' +
          '<tbody>' +
            buildStageRow('Visit Request', row.visit_request || 0, null, null, null) +
            buildStageRow('Site Visit', row.site_visit || 0, row.site_visit_date, null, null) +
            buildStageRow('Water Sample', row.water_sample || 0, row.water_sample_date, 'water_sample', row.water_sample_name) +
            buildStageRow('Lab Test Result', row.lab_test_result || 0, row.lab_test_result_date, 'lab_test_result', row.lab_test_result_name) +
            buildStageRow('Technical Proposal', row.technical_proposal || 0, row.technical_proposal_date, 'technical_proposal', row.technical_proposal_name) +
            buildStageRow('Customer Proposal', row.customer_proposal || 0, row.customer_proposal_date, 'customer_proposal', row.customer_proposal_name) +
          '</tbody>' +
        '</table>' +
      '</div>' +
    '</div>' +
    
    '<div class="tq-action-buttons">' +
      buildActionButton('Technical Questionnaire', getDocLink('technical_questionnaire', row.technical_questionnaire), 'primary') +
      (row.water_sample_name ? buildActionButton('Water Sample', getDocLink('water_sample', row.water_sample_name), 'secondary') : '') +
      (row.lab_test_result_name ? buildActionButton('Lab Test Result', getDocLink('lab_test_result', row.lab_test_result_name), 'warning') : '') +
      (row.technical_proposal_name ? buildActionButton('Technical Proposal', getDocLink('technical_proposal', row.technical_proposal_name), 'success') : '') +
      (row.customer_proposal_name ? buildActionButton('Customer Proposal', getDocLink('customer_proposal', row.customer_proposal_name), 'primary') : '') +
    '</div>';
  
  popup.classList.add('active');
  document.body.style.overflow = 'hidden';
};

function buildStageRow(label, count, date, doctype, docname) {
  var status = count > 0 ? '✅ Done' : '⏳ Pending';
  var color = count > 0 ? '#0F6E56' : '#9CA3AF';
  var dateStr = date ? date : '-';
  var link = '';
  if (count > 0 && doctype && docname) {
    var linkUrl = getDocLink(doctype, docname);
    link = '<a href="'+linkUrl+'" target="_blank" style="color:#1D4ED8;text-decoration:none;font-weight:500">View →</a>';
  } else {
    link = '-';
  }
  return '<tr>' +
    '<td style="font-weight:600">'+label+'</td>' +
    '<td style="color:'+color+'">'+status+'</td>' +
    '<td>'+dateStr+'</td>' +
    '<td>'+link+'</td>' +
    '</tr>';
}

function buildActionButton(label, url, type) {
  var classMap = {
    'primary': 'tq-action-btn-primary',
    'success': 'tq-action-btn-success',
    'warning': 'tq-action-btn-warning',
    'secondary': 'tq-action-btn-secondary'
  };
  return '<a href="'+url+'" target="_blank" class="tq-action-btn '+(classMap[type]||'tq-action-btn-secondary')+'">'+label+' →</a>';
}

window.closeTQPopup = function() {
  document.getElementById('tqPopupOverlay').classList.remove('active');
  document.body.style.overflow = '';
};

// Keyboard shortcut
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeTQPopup();
});

// Render monthly summary after everything is loaded
renderMonthlySummary(tqData);

})();
</script>"""
    )
    return html


def get_chart_data(report_summary):
    chart = {
        "data": {
            "labels": [d["label"] for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"],
            "datasets": [{
                "name": "Sales Distribution",
                "values": [d["value"] for d in report_summary]
            }]
        },
        "type": "pie",
        "height": 300,
        "colors": ["#7cd6fd", "#743ee2", "#ffa00a"]  # Optional custom colors
    }
    chart["data"]["datasets"][0]["values"] = [d["value"] for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"]

    additional_colors = {
        "Sales": "#7cd6fd",
        "Technical": "#743ee2",
        "Lab": "#ffa00a",
    }
    chart["colors"] = [additional_colors.get(d["label"], "#000000") for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"]

    days_ago = (date.today() - date(date.today().year, 1, 1)).days
    chart["title"] = f"Technical Questionnaire Summary as of {date.today().strftime('%d %b, %Y')} (Day {days_ago+1} of {date.today().year})"        

    dely_days = (date.today() - date(date.today().year, 1, 1)).days
    chart["subtitle"] = f"Total Technical Questionnaires: {report_summary[-1]['value']}"
    chart["footnote"] = "Generated by WT Operations System"    
    add_progress = False
    if add_progress:
        chart["data"]["datasets"].append({
            "name": "Progress",
            "values": [round((d["value"] / report_summary[-1]["value"]) * 100, 2) for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"]
        })
        chart["type"] = "bar"
        chart["colors"].append("#4caf50")

    add_more_charts = False
    if add_more_charts:
        frappe.local.response.charts = [chart,{
            "data": {
                "labels": [d["label"] for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"],
                "datasets": [{
                    "name": "Progress",
                    "values": [round((d["value"] / report_summary[-1]["value"]) * 100, 2) for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"]
                }]
            },
            "type": "bar",
            "height": 300,
            "colors": ["#4caf50"]  # Optional custom colors
        }]

    return chart


def get_summary_data(data, group_by):
    summary = {}
    total_count = len(data)
    for row in data:
        key = row.get(group_by)
        if key not in summary:
            summary[key] = {
                "achieved_operations": 0,
                "pending_operations": 0,
                "count": 0
            }
        summary[key]["achieved_operations"] += row.get("achieved_operations", 0)
        summary[key]["pending_operations"] += row.get("pending_operations", 0)
        summary[key]["count"] += 1
    all_summary = []
    for key, values in summary.items():
        all_summary.append({
            "value": values["count"],
            "label": key,
            "indicator": "green" if key == "Completed" else "Black",
            "datatype": "float",
        }
    )
    all_summary.append({
            "value": total_count,
            "label": "Total",
            "datatype": "float",
            "indicator": "Blue"
        }
    )
    html = "<div><h3>Technical Questionnaire Summary</h3><table><tr><th>Pending With</th><th>Count</th></tr>"
    for item in all_summary:
        html += f"<tr><td>{item['label']}</td><td>{item['value']}</td></tr>"
    html += "</table></div>"
    frappe.local.response.report_summary_html = html    
    return all_summary,(total_count)


def get_columns(filters):
    columns = [
        {
            "fieldname": "lead_name",
            "label": "Lead",
            "fieldtype": "Link",
            "options": "Lead",
            "width": 140,
        },
        {
            "fieldname": "technical_questionnaire",
            "label": """Technical Questionnaire""",
            "fieldtype": "Link",
            "options": "WWTP Technical Questionnaire",
            "width": 180,
        },
        {
            "fieldname": "wtq_workflow_state",
            "label": "Workflow State",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "tq_date",
            "label": "Date",
            "fieldtype": "Date",
            "width": 140,
        },
        {
            "fieldname": "achieved_operations",
            "label": "Achieved Operations",
            "fieldtype": "Percent",
            "width": 140,
            "precision": 1
        },
        # Add action button column
        {
            "fieldname": "actions",
            "label": "Actions",
            "fieldtype": "HTML",
            "width": 120,
        },
        {
            "fieldname": "days_count",
            "label": "Days Count",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "delay_days",
            "label": "Delay Days",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "pending_with",
            "label": "Pending With",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "fieldname": "visit_request",
            "label": "Visit Request(Sales)",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "site_visit",
            "label": "Site Visit(Sales)",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "water_sample",
            "label": "Water Sample(Sales)",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "lab_test_result",
            "label": "Lab Test Result(Lab)",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "technical_proposal",
            "label": "Technical Proposal(Technical)",
            "fieldtype": "Int",
            "width": 140,
        },
        {
            "fieldname": "customer_proposal",
            "label": "Customer Proposal(Sales)",
            "fieldtype": "Int",
            "width": 140,
        },
       
    ]
    
    department = filters.get("department")
    if department:
        if department == "Sales":
            columns = [col for col in columns if col["fieldname"] not in ["lab_test_result", "technical_proposal"]]
        elif department == "Technical":
            columns = [col for col in columns if col["fieldname"] not in ["visit_request", "site_visit", "water_sample", "lab_test_result", "customer_proposal", "request_for_proposal"]]
        elif department == "Lab":
            columns = [col for col in columns if col["fieldname"] not in ["visit_request", "site_visit", "water_sample", "technical_proposal", "customer_proposal", "request_for_proposal"]]
    
    return columns


def get_data(filters):    
    technical_questionnaire = filters.get("technical_qquestionnaire")
    lead = filters.get("lead")
    hide_completed_operations = filters.get("hide_completed_operations")
    sql = """
        Select
            ld.company_name as lead_name,
            ld.name as lead_id,
            wtq.name as technical_questionnaire,
            wtq.site_visit_required as site_visit_required,
            wtq.workflow_state as wtq_workflow_state,
            wtq.estimated_completion_date as estimated_completion_date,
            wtq.date as tq_date,
            wtq.sample_collection_required as sample_collection_required,
            wtq.opportunity as opportunity,
            count(DISTINCT svr.name) as visit_request,
            count(DISTINCT sv.name) as site_visit,
            sv.date as site_visit_date,
            count(DISTINCT ws.name) as water_sample,
            ws.date_collected as water_sample_date,
            GROUP_CONCAT(DISTINCT ws.name) as water_sample_names,
            count(DISTINCT ltr.name) as lab_test_result,
            ltr.deadline_date as lab_test_result_date,
            GROUP_CONCAT(DISTINCT ltr.name) as lab_test_result_names,
            count(DISTINCT wtp.name) as technical_proposal,
            wtp.proposal_date as technical_proposal_date,
            GROUP_CONCAT(DISTINCT wtp.name) as technical_proposal_names,
            wtq.workflow_state as wtp_workflow_state,
            count(DISTINCT cp.name) as customer_proposal,
            cp.issue_date as customer_proposal_date,
            GROUP_CONCAT(DISTINCT cp.name) as customer_proposal_names,
            count(DISTINCT rfp.name) as request_for_proposal,
            ROUND((count(svr.name)+count(sv.name)+count(ws.name)+count(ltr.name)+count(wtp.name)+count(rfp.name)+count(cp.name))/7*100, 1) as achieved_operations,
            (100-ROUND((count(svr.name)+count(sv.name)+count(ws.name)+count(ltr.name)+count(wtp.name)+count(rfp.name)+count(cp.name))/7*100, 1)) as pending_operations
        From
            `tabLead` ld, `tabWWTP Technical Questionnaire` wtq
            LEFT JOIN `tabSite Visit Request` svr 
            ON wtq.name = svr.technical_questionnaire and svr.docstatus = 1
            LEFT JOIN `tabSite Visit` sv 
            On wtq.name = sv.wwtp_technical_questionnaire and sv.docstatus = 1
            LEFT JOIN `tabWater Sample` ws
            On wtq.name = ws.wwtp_technical_questionnaire and ws.docstatus = 1
            LEFT JOIN `tabLab Test Result` ltr
            On FIND_IN_SET(ws.name, ltr.sample_tag) > 0 and ws.docstatus = 1
            LEFT JOIN `tabWWTP Technical Proposal` wtp
            On wtq.name = wtp.wwtp_technical_questionnaire and wtp.docstatus != 2
            LEFT JOIN `tabCustomer Proposal` cp
            On  wtp.name = cp.wwtp_technical_proposal and cp.docstatus = 1
            LEFT JOIN `tabRequest For Proposal` rfp
            On  wtq.name = rfp.technical_questionnaire and rfp.docstatus = 1    
        Where
            wtq.lead = ld.name and wtq.docstatus != 2
        """
    if technical_questionnaire:
        sql += " and wtq.name = %(technical_questionnaire)s"
    if lead:
        sql += " and ld.name = %(lead)s"
    
    
    sql = sql + " group by wtq.name"

    data = frappe.db.sql(sql,
            {"technical_questionnaire": technical_questionnaire, "lead": lead},
            as_dict=1,
        )

    if len(data) > 0:
        for row in data:
            achieved_operations = count_achieved_operations(row)
            if row.site_visit_required == 1 and row.sample_collection_required == 1:
                row.achieved_operations = round(achieved_operations / 5 * 100,2)
            else:
                row.achieved_operations = round(achieved_operations / 2 * 100,2)
            
            row.pending_operations = 100 - row.achieved_operations

    for row in data:
        tq_date = row.get("tq_date")
        row.days_count = (date.today() - tq_date).days if tq_date else 0        
        if tq_date:
            delay_count = (date.today() - tq_date).days
            row.delay_days = delay_count
        else:
            row.delay_days = 0
        
        # Get workflow states
        wtq_workflow_state = row.get("wtq_workflow_state", "")
        wtp_workflow_state = row.get("wtp_workflow_state", "")
        
        # Check for Rejected By Technical Manager in Technical Questionnaire
        if wtq_workflow_state and "Rejected By Technical Manager" in wtq_workflow_state:
            row.pending_with = "Sales"
            row.delay_days = (date.today() - row.tq_date).days if row.tq_date else delay_count

        elif wtq_workflow_state and "Draft" in wtq_workflow_state:
            row.pending_with = "Sales"
            row.delay_days = (date.today() - row.tq_date).days if row.tq_date else delay_count
        
        # Check for Rejected By Sales in Technical Proposal
        elif wtp_workflow_state and "Rejected By Sales" in wtp_workflow_state:
            row.pending_with = "Technical"
            row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count
            

        elif wtp_workflow_state and "Draft" in wtp_workflow_state:
            row.pending_with = "Technical"
            row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count
        elif wtp_workflow_state and "Rejected" in wtp_workflow_state:
            row.pending_with = "Technical"
            row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count    
        
        # Check Technical Proposal workflow state (pending with sales)
        elif row.technical_proposal > 0:
            # If technical proposal workflow is pending with sales (even if draft)
            if wtp_workflow_state and "Sales" in wtp_workflow_state:
                row.pending_with = "Sales"
                row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count
            elif row.customer_proposal == 0:
                row.pending_with = "Sales"
                row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count
        
        # Check Technical Questionnaire workflow state (pending for technical)
        elif row.technical_proposal == 0:
            # If technical questionnaire workflow is pending for technical
            if wtq_workflow_state and "Technical" in wtq_workflow_state:
                row.pending_with = "Technical"
                row.delay_days = (date.today() - row.tq_date).days if row.tq_date else delay_count
            else:
                # Original logic for site visit and sample collection
                if row.site_visit_required and row.sample_collection_required:
                    if row.site_visit == 0:
                        row.pending_with = "Sales"
                    elif row.water_sample == 0:
                        row.delay_days = (date.today() - row.site_visit_date).days if row.site_visit_date else delay_count
                        row.pending_with = "Sales"
                    elif row.lab_test_result == 0:
                        row.delay_days = (date.today() - row.water_sample_date).days if row.water_sample_date else delay_count
                        row.pending_with = "Lab"
                    else:
                        row.pending_with = "Technical"
                        row.delay_days = (date.today() - row.lab_test_result_date).days if row.lab_test_result_date else delay_count
                else:
                    row.pending_with = "Technical"
                    row.delay_days = (date.today() - row.tq_date).days if row.tq_date else delay_count
        else:
            # Both technical proposal exists and customer proposal missing
            if row.customer_proposal == 0:
                row.pending_with = "Sales"
                row.delay_days = (date.today() - row.technical_proposal_date).days if row.technical_proposal_date else delay_count
        
        if row.achieved_operations == 100:
            row.pending_with = "Completed"
        
        # Extract single document names from GROUP_CONCAT
        row.water_sample_name = row.water_sample_names.split(',')[0] if row.water_sample_names else ''
        row.lab_test_result_name = row.lab_test_result_names.split(',')[0] if row.lab_test_result_names else ''
        row.technical_proposal_name = row.technical_proposal_names.split(',')[0] if row.technical_proposal_names else ''
        row.customer_proposal_name = row.customer_proposal_names.split(',')[0] if row.customer_proposal_names else ''

    department = filters.get("department")
    if department:
        filtered_data = []
        for wtq in data:
            if department == "Sales" and wtq.pending_with == "Sales":
                filtered_data.append(wtq)
            elif department == "Technical" and wtq.pending_with == "Technical":
                filtered_data.append(wtq)
            elif department == "Lab" and wtq.pending_with == "Lab":
                filtered_data.append(wtq)
        data = filtered_data

    if hide_completed_operations:
        data_copy = data.copy()
        for row in data:
            if row.pending_with == "Completed":
                data_copy.remove(row)
        data = data_copy
    
    # Add action buttons to each row
    for row in data:
        row['actions'] = '<button class="tq-detail-btn" onclick="openTQPopup(\'' + row.technical_questionnaire + '\')">📋 Details</button>'
    
    return data


def count_achieved_operations(row):
    count = 0
    if row.site_visit_required == 1 and row.sample_collection_required == 1:
        if row.site_visit:
            count += 1
        if row.water_sample:
            count += 1
        if row.lab_test_result:
            count += 1
    if row.technical_proposal:
        count += 1
    if row.customer_proposal:
        count += 1
    
    return count