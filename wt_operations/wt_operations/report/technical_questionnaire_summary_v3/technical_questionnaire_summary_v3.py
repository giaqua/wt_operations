# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, date


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    report_summary, primitive_summary = get_summary_data(data, "pending_with")
    chart = get_chart_data(report_summary)
    message = get_dashboard_html(data, report_summary)
    # return columns, data, message, chart, report_summary, primitive_summary
    return columns, data, message


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
        + kpi('#1D9E75', 'Completed',  completed,    '#0F6E56', str(comp_pct) + '% completion rate')
        + kpi('#BA7517', 'In progress', in_progress, '#854F0B', 'open TQs')
        + kpi('#E24B4A', 'Avg delay',  str(avg_delay) + 'd', '#A32D2D', 'across open TQs')
    )
    kpi_row2 = (
        kpi('#378ADD', 'Pending sales',     pending_sales, '#185FA5', 'awaiting action')
        + kpi('#534AB7', 'Pending technical', pending_tech,  '#3C3489', 'awaiting action')
        + kpi('#D85A30', 'Pending lab',       pending_lab,   '#993C1D', 'awaiting action')
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
#tqdash .tq-charts{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:9px}
#tqdash .tq-card{background:#fff;border:1px solid #E5E7EB;border-radius:9px;padding:13px 14px;min-width:0}
#tqdash .tq-card.wide{grid-column:1/-1}
#tqdash .tq-card-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}
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

      <div class="tq-card wide">
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

	# add_progress = True	
	# if add_progress:
	# 	chart["data"]["datasets"].append({
	# 		"name": "Progress",
	# 		"values": [round((d["value"] / report_summary[-1]["value"]) * 100, 2) for d in report_summary if d["label"] != "Total" and d["label"] != "Completed"]
	# 	})
	# 	chart["type"] = "bar"
	# 	chart["colors"].append("#4caf50")		

	days_ago = (date.today() - date(date.today().year, 1, 1)).days
	chart["title"] = f"Technical Questionnaire Summary as of {date.today().strftime('%d %b, %Y')} (Day {days_ago+1} of {date.today().year})"		


	dely_days = (date.today() - date(date.today().year, 1, 1)).days
	chart["subtitle"] = f"Total Technical Questionnaires: {report_summary[-1]['value']}"
	chart["footnote"] = "Generated by WT Operations System"	
	add_progress = False
	# add_progress = True
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

	# add_summary = True
	# if add_summary:
	# 	frappe.local.response.summary = report_summary	
	return chart
# def get_chart_data(data):
# 	labels = []
# 	datasets = [
# 		{
# 			"name": "Achieved Operations",
# 			"values": [],
# 		},
# 		{
# 			"name": "Pending Operations",
# 			"values": [],
# 		},
# 	]

# 	for key, values in summary.items():
# 		labels.append(key)
# 		datasets[0]["values"].append(values["achieved_operations"] / values["count"])
# 		datasets[1]["values"].append(values["pending_operations"] / values["count"])

# 	chart = {
# 		"data": {
# 			"labels": labels,
# 			"datasets": datasets,
# 		},
# 		"type": "bar",
# 		"colors": ["#4caf50", "#f44336"],
# 	}
# 	return chart

def get_summary_data(data, group_by):
	summary = {}
	# print(data,"=================data==================")
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
	# print(all_summary,"=================summary==================")
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
			"fieldname": "achieved_operations",
			"label": "Achieved Operations",
			"fieldtype": "Percent",
			"width": 140,
			"precision": 1
		},
		{
			"fieldname": "pending_operations",
			"label": "Pending Operations",
			"fieldtype": "Percent",
			"width": 140,
			"precision": 1
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
		# {
		# 	"fieldname": "request_for_proposal",
		# 	"label": "Request For Proposal(Sales)",
		# 	"fieldtype": "Int",
		# 	"width": 140,
		# },
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
			count(DISTINCT ltr.name) as lab_test_result,
			ltr.deadline_date as lab_test_result_date,
			count(DISTINCT wtp.name) as technical_proposal,
			wtp.proposal_date as technical_proposal_date,
			wtq.workflow_state as wtp_workflow_state,
			count(DISTINCT cp.name) as customer_proposal,
			cp.issue_date as customer_proposal_date,
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
	return data
def count_achieved_operations(row):
	count = 0
	# if row.visit_request:
	# 	count += 
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
	# if row.request_for_proposal:
	# 	count += 1
	
	return count