# Copyright (c) 2026, Takamol and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	message = get_message()
	return columns, data, message

def get_message():
	html = "<h4>Daily Operation Summary Report</h4>"
	html += """
	<style>
					.donut-chart {
			/* Set size and make it circular */
			width: 200px;
			height: 200px;
			border-radius: 50%;
			/* Use conic-gradient to create segments (example: 30%, 20%, 50%) */
			background: conic-gradient(
				#ff6384 0% 30%,    /* Segment 1 (0 to 30%) */
				#36a2eb 30% 50%,    /* Segment 2 (30% to 50%) */
				#cc65fe 50% 100%    /* Segment 3 (50% to 100%) */
			);
			position: relative;
			}

			.donut-chart::after {
			/* Create the center "hole" using a pseudo-element */
			content: '';
			position: absolute;
			top: 50%;
			left: 50%;
			width: 100px; /* Adjust size for the inner white circle */
			height: 100px;
			background: white; /* Match your background color */
			border-radius: 50%;
			transform: translate(-50%, -50%); /* Center the hole precisely */
			}
	</style>
	<div class="donut-chart"></div>
	"""


	html2 = """	
	<style>
					.donut-chart {
			/* Dimensions and basic shape */
			width: 150px;
			height: 150px;
			border-radius: 50%;
			position: relative;
			display: flex;
			justify-content: center;
			align-items: center;
			
			/* Use CSS variable to set the conic gradient */
			background: conic-gradient(
				var(--fill-color) 0deg calc(var(--percentage) * 1%),
				#e0e0e0 calc(var(--percentage) * 1%) 360deg
			);
			}

			.donut-chart::after {
			/* Creates the inner white circle (the "hole") */
			content: '';
			position: absolute;
			width: 100px; /* Controls the size of the hole (thickness of the ring) */
			height: 100px;
			background: #fff; /* Must match the background color of the page/container */
			border-radius: 50%;
			}

			.chart-label {
			/* Styles the label inside the hole */
			position: relative; /* Brings label above the pseudo-element */
			z-index: 1;
			font-family: sans-serif;
			font-size: 1.2em;
			color: #333;
			}
	</style>
	<div class="donut-chart" style="--percentage: 75; --fill-color: #4CAF50;">
		<span class="chart-label">75%</span>
	</div>	
	"""
	html3 = """
	<style>
				.donut-chart-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		font-family: sans-serif;
		width: 30%;
		}

		.donut-chart {
		width: 200px;
		height: 200px;
		border-radius: 50%;
		/* Conic gradient: Used (blue) 0%-75%, Wasted (red) 75%-100% */
		background: conic-gradient(
			#3498db var(--usage),
			#e74c3c var(--usage) 100%
		);
		display: flex;
		justify-content: center;
		align-items: center;
		position: relative;
		}

		/* Creates the "hole" in the donut */
		.donut-chart::before {
		content: "";
		width: 70%;
		height: 70%;
		background-color: white;
		border-radius: 50%;
		position: absolute;
		}

		.donut-center {
		position: relative;
		text-align: center;
		}

		.main-title {
		font-weight: bold;
		font-size: 1.2rem;
		}

		.sub-title {
		color: #555;
		font-size: 0.9rem;
		}

		.chart-legend {
		margin-top: 15px;
		display: flex;
		gap: 15px;
		}

		.legend-item::before {
		content: "";
		display: inline-block;
		width: 10px;
		height: 10px;
		margin-right: 5px;
		border-radius: 50%;
		}

		.legend-item.usage::before { background-color: #3498db; }
		.legend-item.waste::before { background-color: #e74c3c; }
	</style>
		
		
		<div class="donut-chart-container">
		<h4>Fresh Water Usage</h4>
		<div class="donut-chart" style="--usage: 75%; --waste: 25%;">
			<div class="donut-center">
			<div class="main-title">Water Audit</div>
			<div class="sub-title">75% Usage</div>
			</div>
		</div>
		<div class="chart-legend">
			<span class="legend-item usage">treated Waste Water: 75%</span>
		</div>
		<div class="chart-legend">
			<span class="legend-item waste">Fresh Water Usage: 25%</span>
		</div>
		</div>
	"""

	return html3
def get_columns(filters):
	columns = [
	]
	return columns

def get_data(filters):
	data = []
	# daily_operations = get_daily_operation_report(filters)
	treatment_parameters= get_treatment_parameters(filters)
	return data

def get_treatment_parameters(filters):
	# daily_operations_string = ', '.join(["'" + d.daily_operation_report + "'" for d in daily_operations])
	# print(str(daily_operations_string),"=========================")
	sql = """
		SELECT
			dor.name AS daily_operation_report,
			dor.date AS daily_operation_date,
			dpt.*
		FROM
			`tabDaily Operation Report` dor,`tabTreatment parameters table` dpt,`tabTreatment parameter` tp
		WHERE
			dor.name = dpt.parent AND
			dpt.treatment_parameter = tp.name
	"""

	print(sql,"=============sql============")
	report_data = frappe.db.sql(sql, as_dict=1)

	print(str(report_data),"=========================")

	return report_data

def get_daily_operation_report(filters):
	report_data = frappe.db.sql("""
		SELECT
			dor.name AS daily_operation_report,
			dor.date AS daily_operation_date
		FROM
			`tabDaily Operation Report` dor
	""",  as_dict=1)

	print(str(report_data),"=========================")

	return report_data
