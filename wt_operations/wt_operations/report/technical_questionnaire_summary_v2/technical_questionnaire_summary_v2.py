# Copyright (c) 2025, Takamol and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, date


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	report_summary,primitive_summary = get_summary_data(data, "pending_with")
	# print(report_summary,"=================report_summary==================")
	chart = get_chart_data(report_summary)
	message = None
	# chart = get_chart_data(report_summary)
	message = ""
	# message = get_message(data)
	# frappe.local.response.chart = chart
	return columns, data,message, chart,report_summary,primitive_summary

def get_message(data):
	# html = "<div><h3>Technical Questionnaire Summary</h3><table><tr><th>Pending With</th><th>Count</th></tr>"
	# summary = {}
	# for row in data:
	# 	key = row.get("pending_with")
	# 	if key not in summary:
	# 		summary[key] = 0
	# 	summary[key] += 1
	# for key, value in summary.items():
	# 	html += f"<tr><td>{key}</td><td>{value}</td></tr>"
	# html += "</table></div>"
	# html_cards = "<div style='display: flex; gap: 20px;'>"
	# for key, value in summary.items():
	# 	html_cards += f"""
	# 	<div style='border: 1px solid #ccc; padding: 10px; border-radius: 5px; width: 150px; text-align: center;'>
	# 		<h4>{key}</h4>
	# 		<p style='font-size: 24px; margin: 0;'>{value}</p>
	# 	</div>
	# 	"""
	# html_cards += "</div>"
	# html_charts += "</table></div>"	
	# add_html_chart_progress = True
	html = "<div><h3>Technical Questionnaire Summary</h3><table><tr><th>Pending With</th><th>Count</th></tr>"
	summary = {}
	for row in data:
		key = row.get("pending_with")
		if key not in summary:
			summary[key] = 0
		summary[key] += 1
	html = """
	<style>
	.kpi-card {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin: 10px;
    width: 250px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: transform 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-5px);
}

.kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.kpi-title {
    font-size: 1rem;
    color: #555;
    text-transform: uppercase;
}

.kpi-icon {
    color: #007bff; /* Example color for an icon */
}

.kpi-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #333;
}

.kpi-comparison {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
}

.kpi-difference.up {
    color: #28a745; /* Green for positive change */
    font-weight: bold;
    margin-right: 5px;
}

.kpi-difference.down {
    color: #dc3545; /* Red for negative change */
    font-weight: bold;
    margin-right: 5px;
}

.kpi-period {
    color: #777;
}
	</style>
	
	<div class="kpi-card">
		<div class="kpi-header">
			<span class="kpi-title">Total Revenue</span>
			<!-- Optional Icon (e.g., Font Awesome) -->
			<!-- <i class="fa fa-hospital-o kpi-icon" aria-hidden="true"></i> -->
		</div>
		<div class="kpi-value">$50,846.90</div>
		<div class="kpi-comparison">
			<span class="kpi-difference up">+12%</span>
			<span class="kpi-period">vs last month</span>
		</div>
	</div>
	"""

	html2 = """
	<style>
	.summary-container {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        margin: 24px 0;
        padding: 0;
    }}
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }}
    .kpi-card {{
        background: #FFFFFF;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }}
    .kpi-card:hover {{
        border-color: #D1D5DB;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transform: translateY(-1px);
    }}
    .kpi-label {{
        font-size: 11px;
        color: #6B7280;
        margin-bottom: 8px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }}
    .kpi-value {{
        font-size: 32px;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 6px;
        color: #1F2937;
    }}
    .kpi-subtitle {{
        font-size: 13px;
        color: #9CA3AF;
        font-weight: 400;
    }}
    .alert-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 16px;
        margin: 24px 0;
    }}
    .alert-box {{
        background: #FFFFFF;
        border-left: 3px solid var(--alert-color);
        border-radius: 6px;
        padding: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    .alert-title {{
        font-weight: 700;
        color: var(--alert-color);
        margin-bottom: 6px;
        font-size: 14px;
    }}
    .alert-message {{
        font-size: 13px;
        color: #4B5563;
        margin-bottom: 6px;
        line-height: 1.5;
    }}
    .alert-action {{
        font-size: 12px;
        color: #9CA3AF;
        font-style: italic;
    }}
    .insights-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
        margin-top: 24px;
    }}
    .insight-panel {{
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    .insight-header {{
        margin: 0 0 16px 0;
        font-size: 14px;
        color: #1F2937;
        font-weight: 700;
        display: flex;
        align-items: center;
        padding-bottom: 10px;
        border-bottom: 1px solid #F3F4F6;
    }}	
    .insight-icon {{
        display: inline-block;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        margin-right: 8px;
        background: #1F2937;
    }}
    .insight-item {{
        margin-bottom: 12px;
    }}
    .insight-bar-container {{
        background: #F9FAFB;
        border-radius: 3px;
        height: 5px;
        overflow: hidden;
        margin-top: 5px;
    }}
    .insight-bar {{
        height: 100%;
        border-radius: 3px;
        background: #1F2937;
    }}
    .insight-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        align-items: center;
    }}
    .insight-name {{
        font-weight: 500;
        color: #4B5563;
        font-size: 13px;
    }}
    .insight-value {{
        font-weight: 700;
        font-size: 13px;
        color: #1F2937;
    }}
    .success-banner {{
        background: #F0FDF4;
        border: 1px solid #10B981;
        border-radius: 6px;
        padding: 14px;
        text-align: center;
        color: #059669;
        font-weight: 600;
        font-size: 14px;
    }}
	</style>
	 <div class="summary-container">
        
        <!-- KPI Cards - Frappe Insights Style -->
        <div class="kpi-grid">
			<div class="kpi-card">	
				<div class="kpi-label">Total Leads</div>		
				<div class="kpi-value">{lead_count:,}</div>
				<div class="kpi-subtitle">{completed_lead_count:,} completed leads</div>
			</div>
			<div class="kpi-card">	
				<div class="kpi-label">Total Technical Questionnaires</div>		
				<div class="kpi-value">{tq_count:,}</div>	
				<div class="kpi-subtitle">{completed_tq_count:,} completed technical questionnaires</div>
			</div>
		</div>
		 <!-- Insights -->
        <div class="insights-grid">
            
            <div class="insight-panel">
                <h3 class="insight-header">
                    <span class="insight-icon"></span>
                    Top 5 Frequent Failures
                </h3>
                {completed_lead_count}
            </div>
            
            <div class="insight-panel">
                <h3 class="insight-header">
                    <span class="insight-icon"></span>
                    Top Dealers by Amount
                </h3>
                {tq_count}
            </div>
            
            <div class="insight-panel">
                <h3 class="insight-header">
                    <span class="insight-icon"></span>
                    High-Cost Operations
                </h3>
                {lead_count}
            </div>
            
        </div>
	""".format(
		lead_count = sum(value for key, value in summary.items() if key != "Completed"),
		completed_lead_count = summary.get("Completed", 0),
		tq_count = sum(value for key, value in summary.items()),
		completed_tq_count = summary.get("Completed", 0),
		)
	# html_cards = "<div style='display: flex; gap: 20px;'>"
	# for key, value in summary.items():	
	# 	html += f"<tr><td>{key}</td><td>{value}</td></tr>"
	# 	html_cards += f"""
	# 	<div style='border: 1px solid #ccc; padding: 10px; border-radius: 5px; width: 150px; text-align: center;'>
	# 		<h4>{key}</h4>
	# 		<p style='font-size: 24px; margin: 0;'>{value}</p>
	# 	</div>
	# 	"""
	# html += "</table></div>"
	# html_cards += "</div>"
	html3 = """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
       
        
        .table-container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow-x: auto;
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 600;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        
        /* Method 1: Using writing-mode */
        .table-vertical {
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
        }
        
        .table-vertical th {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px 10px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table-vertical th.vertical-text {
            height: 200px;
            width: 50px;
            writing-mode: vertical-rl;
            text-orientation: mixed;
            transform: rotate(180deg);
            text-align: center;
            font-weight: 600;
            font-size: 16px;
            letter-spacing: 1px;
            position: relative;
        }
        
        .table-vertical th.vertical-text span {
            display: inline-block;
            padding: 10px 0;
        }
        
        .table-vertical td {
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            text-align: center;
            font-weight: 500;
            color: #555;
        }
        
        .table-vertical tr:hover td {
            background-color: #f8f9ff;
            color: #667eea;
            transition: all 0.3s ease;
        }
        
        .table-vertical th:first-child {
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
        }
        
        .table-vertical th:last-child {
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            border-right: none;
        }
        
        /* Method 2: Using transform rotate */
        .table-rotate {
            margin-top: 50px;
        }
        
        .table-rotate th {
            background: linear-gradient(135deg, #00c6ff, #0072ff);
            color: white;
            padding: 15px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .table-rotate th.rotated {
            height: 180px;
            width: 40px;
        }
        
        .table-rotate th.rotated div {
            transform: rotate(90deg);
            transform-origin: left top 0;
            white-space: nowrap;
            position: absolute;
            bottom: 0;
            left: 50%;
            font-weight: 600;
            font-size: 15px;
            letter-spacing: 0.5px;
        }
        
        .table-rotate td {
            padding: 12px 20px;
            border-bottom: 1px solid #eef;
            text-align: center;
        }
        
        /* Method 3: Pure CSS with flexbox */
        .table-flex {
            display: table;
            width: 100%;
            margin-top: 50px;
        }
        
        .table-flex .header-row {
            display: table-row;
        }
        
        .table-flex .header-cell {
            display: table-cell;
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
            padding: 0;
            text-align: center;
            vertical-align: bottom;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            height: 150px;
            width: 60px;
        }
        
        .table-flex .header-cell .content {
            display: flex;
            align-items: flex-end;
            justify-content: center;
            height: 100%;
            padding-bottom: 20px;
            transform: rotate(180deg);
            writing-mode: vertical-lr;
            font-weight: 600;
            font-size: 15px;
        }
        
        .table-flex .data-row {
            display: table-row;
        }
        
        .table-flex .data-cell {
            display: table-cell;
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
            text-align: center;
        }
        
        /* Status indicators */
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status.active {
            background: #e7f7ef;
            color: #27ae60;
        }
        
        .status.pending {
            background: #fff4e6;
            color: #f2994a;
        }
        
        .status.inactive {
            background: #ffeaea;
            color: #eb5757;
        }
        
        /* Color coding for values */
        .value-high { color: #27ae60; font-weight: bold; }
        .value-medium { color: #f2994a; font-weight: bold; }
        .value-low { color: #eb5757; font-weight: bold; }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .table-container {
                padding: 15px;
            }
            
            .table-vertical th.vertical-text,
            .table-rotate th.rotated,
            .table-flex .header-cell {
                height: 120px;
                font-size: 14px;
            }
            
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
    <div class="table-container">
        <h1>📊 Sales Performance Dashboard</h1>
        
        <!-- Method 1: Writing Mode -->
        <table class="table-vertical">
            <thead>
                <tr>
                    <th class="vertical-text"><span>Product Category</span></th>
                    <th class="vertical-text"><span>Q1 Sales</span></th>
                    <th class="vertical-text"><span>Q2 Sales</span></th>
                    <th class="vertical-text"><span>Q3 Sales</span></th>
                    <th class="vertical-text"><span>Q4 Sales</span></th>
                    <th class="vertical-text"><span>Annual Growth</span></th>
                    <th class="vertical-text"><span>Market Share</span></th>
                    <th class="vertical-text"><span>Status</span></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Electronics</td>
                    <td class="value-high">$125,430</td>
                    <td class="value-high">$145,210</td>
                    <td class="value-high">$162,890</td>
                    <td class="value-high">$198,540</td>
                    <td class="value-high">+24.5%</td>
                    <td class="value-medium">32.4%</td>
                    <td><span class="status active">Active</span></td>
                </tr>
                <tr>
                    <td>Clothing</td>
                    <td class="value-medium">$89,760</td>
                    <td class="value-high">$112,340</td>
                    <td class="value-medium">$95,670</td>
                    <td class="value-high">$134,890</td>
                    <td class="value-high">+18.9%</td>
                    <td class="value-low">21.7%</td>
                    <td><span class="status active">Active</span></td>
                </tr>
                <tr>
                    <td>Home Goods</td>
                    <td class="value-low">$45,320</td>
                    <td class="value-medium">$67,890</td>
                    <td class="value-medium">$72,340</td>
                    <td class="value-medium">$89,560</td>
                    <td class="value-high">+22.3%</td>
                    <td class="value-low">15.2%</td>
                    <td><span class="status pending">Pending</span></td>
                </tr>
                <tr>
                    <td>Books</td>
                    <td class="value-low">$23,450</td>
                    <td class="value-low">$28,910</td>
                    <td class="value-low">$31,230</td>
                    <td class="value-medium">$45,670</td>
                    <td class="value-high">+25.8%</td>
                    <td class="value-low">8.9%</td>
                    <td><span class="status inactive">Inactive</span></td>
                </tr>
                <tr>
                    <td>Sports</td>
                    <td class="value-medium">$67,890</td>
                    <td class="value-medium">$78,340</td>
                    <td class="value-high">$112,560</td>
                    <td class="value-high">$145,780</td>
                    <td class="value-high">+28.7%</td>
                    <td class="value-medium">27.3%</td>
                    <td><span class="status active">Active</span></td>
                </tr>
            </tbody>
        </table>
        
        <!-- Method 2: Transform Rotate -->
        <h1 style="margin-top: 60px;">📈 Financial Metrics</h1>
        <table class="table-vertical table-rotate">
            <thead>
                <tr>
                    <th class="vertical-text"><span>Department</span></th>
                    <th class="vertical-text"><span>Revenue</span></th>
                    <th class="vertical-text"><span>Expenses</span></th>
                    <th class="vertical-text"><span>Profit</span></th>
                    <th class="vertical-text"><span>ROI</span></th>
                    <th class="vertical-text"><span>Budget</span></th>
                    <th class="vertical-text"><span>Actual</span></th>
                    <th class="vertical-text"><span>Variance</span></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Marketing</td>
                    <td class="value-high">$2,450,000</td>
                    <td class="value-medium">$1,230,000</td>
                    <td class="value-high">$1,220,000</td>
                    <td class="value-high">+18.5%</td>
                    <td class="value-medium">$1,500,000</td>
                    <td class="value-medium">$1,230,000</td>
                    <td class="value-high">-$270,000</td>
                </tr>
                <tr>
                    <td>Sales</td>
                    <td class="value-high">$5,670,000</td>
                    <td class="value-high">$2,340,000</td>
                    <td class="value-high">$3,330,000</td>
                    <td class="value-high">+22.3%</td>
                    <td class="value-high">$2,500,000</td>
                    <td class="value-high">$2,340,000</td>
                    <td class="value-high">-$160,000</td>
                </tr>
                <tr>
                    <td>R&D</td>
                    <td class="value-low">$890,000</td>
                    <td class="value-high">$1,560,000</td>
                    <td class="value-low">-$670,000</td>
                    <td class="value-low">-5.2%</td>
                    <td class="value-medium">$1,800,000</td>
                    <td class="value-high">$1,560,000</td>
                    <td class="value-high">-$240,000</td>
                </tr>
                <tr>
                    <td>Operations</td>
                    <td class="value-medium">$3,210,000</td>
                    <td class="value-high">$2,780,000</td>
                    <td class="value-medium">$430,000</td>
                    <td class="value-medium">+8.7%</td>
                    <td class="value-high">$3,000,000</td>
                    <td class="value-high">$2,780,000</td>
                    <td class="value-high">-$220,000</td>
                </tr>
            </tbody>
        </table>
        
        <!-- Method 3: Flexbox Approach -->
        <h1 style="margin-top: 60px;">👥 Employee Performance</h1>
        <div class="table-flex">
            <div class="header-row">
                <div class="header-cell">
                    <div class="content">Employee Name</div>
                </div>
                <div class="header-cell">
                    <div class="content">Projects</div>
                </div>
                <div class="header-cell">
                    <div class="content">Completed</div>
                </div>
                <div class="header-cell">
                    <div class="content">Success Rate</div>
                </div>
                <div class="header-cell">
                    <div class="content">Rating</div>
                </div>
                <div class="header-cell">
                    <div class="content">Satisfaction</div>
                </div>
                <div class="header-cell">
                    <div class="content">Tenure</div>
                </div>
            </div>
            
            <div class="data-row">
                <div class="data-cell">John Smith</div>
                <div class="data-cell">24</div>
                <div class="data-cell">22</div>
                <div class="data-cell class="value-high">91.7%</div>
                <div class="data-cell class="value-high">4.8/5</div>
                <div class="data-cell class="value-high">94%</div>
                <div class="data-cell">3.5 years</div>
            </div>
            
            <div class="data-row">
                <div class="data-cell">Sarah Johnson</div>
                <div class="data-cell">18</div>
                <div class="data-cell">17</div>
                <div class="data-cell class="value-high">94.4%</div>
                <div class="data-cell class="value-high">4.9/5</div>
                <div class="data-cell class="value-high">96%</div>
                <div class="data-cell">2 years</div>
            </div>
            
            <div class="data-row">
                <div class="data-cell">Mike Chen</div>
                <div class="data-cell">31</div>
                <div class="data-cell">28</div>
                <div class="data-cell class="value-high">90.3%</div>
                <div class="data-cell class="value-high">4.7/5</div>
                <div class="data-cell class="value-high">89%</div>
                <div class="data-cell">5 years</div>
            </div>
        </div>
    </div>
    
   
	
"""
	css = """
		<style>
		.dt-scrollable thead th {
			white-space: nowrap !important;
			writing-mode: vertical-rl !important;
			transform: rotate(180deg) !important;
			text-align: center !important;
			height: 200px !important;
			min-height: 200px !important;
			max-height: 200px !important;
			vertical-align: bottom !important;
			padding: 10px 5px !important;
			background-color: #f0f4f7 !important;
			border-left: 1px solid #d1d8dd !important;
		}
		
		.dt-scrollable thead th:first-child {
			border-left: none !important;
		}
		
		.dt-scrollable thead th .dt-cell__content {
			transform: rotate(180deg) !important;
			writing-mode: vertical-rl !important;
		}
		
		/* Adjust table body position */
		.dt-scrollable .dt-body {
			margin-top: 150px !important;
		}
		
		/* For specific report */
		[data-page-route="query-report/Sales Report"] .dt-scrollable thead th {
			writing-mode: vertical-rl !important;
			transform: rotate(180deg) !important;
		}
		</style>
    """
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
			wtp.workflow_state as wtp_workflow_state,
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