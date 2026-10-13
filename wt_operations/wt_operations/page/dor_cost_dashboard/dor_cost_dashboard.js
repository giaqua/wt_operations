// ============================================================
// DOR Cost Dashboard - Frappe Desk Page
// Route: /app/dor-cost-dashboard
//
// Features
//   - Period presets or custom range, project filter, exclude zero
//     volume, compare with previous period, target Cost / M3,
//     Cost / Cost per M3 / Both display toggle
//   - KPI cards with delta vs previous period, share of cost,
//     peak / best day
//   - Charts: monthly cost/M3 by category (stacked), cost mix (donut),
//     daily trend + 7-day average, project comparison, monthly volume
//   - Sections as tabs: Overview (KPIs + monthly charts), Trends (daily /
//     volume), Projects (chart + table), Monthly, DOR Detail, Flagged Days (sortable,
//     show-more, CSV export, links open in a new tab)
//   - "Print Full Report" (branded, A4 landscape: KPIs, all charts, all tables)
//     and a "Report v3" button that opens DOR Cost Analysis v3 with the same filters
//
// All numbers come from get_dashboard_data() in dor_cost_dashboard.py
// (same cost model as the report: SUM(cost) / SUM(volume)).
// ============================================================

const API =
	"wt_operations.wt_operations.page.dor_cost_dashboard.dor_cost_dashboard.get_dashboard_data";
const REPORT_NAME = "DOR Cost Analysis V3";

const CATS = [
	{ key: "chemical", label: "Chemical", color: "#1976a8" },
	{ key: "manpower", label: "Manpower", color: "#2e9e6f" },
	{ key: "spare_part", label: "Spare Part", color: "#f0a030" },
	{ key: "other", label: "Other", color: "#8e6bbf" },
];

const PRESETS = [
	"Last 30 Days",
	"This Month",
	"Last Month",
	"Last 3 Months",
	"Year to Date",
	"Last 12 Months",
	"Custom",
];

frappe.pages["dor-cost-dashboard"].on_page_load = function (wrapper) {
	frappe.dor_cost_dashboard = new DORCostDashboard(wrapper);
};

class DORCostDashboard {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("DOR Cost Dashboard"),
			single_column: true,
		});

		this.data = null;
		this.currency = frappe.defaults.get_default("currency") || "";
		this.active_tab = "overview";
		this.sort = {};
		this.limit = {};
		this.silent = false;
		this.req_id = 0;
		this.current_table = null;

		this.refresh_debounced = frappe.utils.debounce(() => this.refresh(), 300);

		this.inject_css();
		this.make_actions();
		this.make_filters();
		this.make_layout();
		this.apply_preset("Last 30 Days");
	}

	// --------------------------------------------------------
	// Setup
	// --------------------------------------------------------
	make_actions() {
		this.page.set_primary_action(__("Refresh"), () => this.refresh(), "refresh");
		this.page.add_inner_button(__("Print Full Report"), () => this.print_full_report());
		this.page.add_inner_button(__("Report v3"), () => this.open_report());
		this.page.add_menu_item(__("Print Full Report"), () => this.print_full_report());
		this.page.add_menu_item(__("Export Current Table (CSV)"), () => this.export_csv());
		this.page.add_menu_item(__("Open DOR Cost Analysis v3 Report"), () => this.open_report());
	}

	make_filters() {
		this.f = {};
		const server = () => this.refresh_debounced();
		const client = () => this.data && this.render();

		const add = (df) => {
			this.f[df.fieldname] = this.page.add_field(df);
		};

		add({
			fieldname: "preset",
			label: __("Period"),
			fieldtype: "Select",
			options: PRESETS.join("\n"),
			default: "Last 30 Days",
			change: () => {
				if (!this.silent) this.apply_preset(this.f.preset.get_value());
			},
		});
		add({
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			change: () => this.on_date_change(),
		});
		add({
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			change: () => this.on_date_change(),
		});
		add({
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			change: server,
		});
		add({
			fieldname: "target",
			label: __("Target Cost / M3"),
			fieldtype: "Float",
			change: client,
		});
		add({
			fieldname: "display",
			label: __("Show"),
			fieldtype: "Select",
			options: ["Both", "Cost Only", "Cost per M3 Only"].join("\n"),
			default: "Cost Only",
			change: client,
		});
		add({
			fieldname: "exclude_zero",
			label: __("Exclude Zero Treated Water"),
			fieldtype: "Check",
			default: 0,
			change: server,
		});
		add({
			fieldname: "compare",
			label: __("Compare Previous Period"),
			fieldtype: "Check",
			default: 1,
			change: server,
		});
	}

	make_layout() {
		this.$body = $(`
			<div class="dd-root">
				<div class="dd-period"></div>
				<div class="dd-empty" style="display:none"></div>
				<div class="dd-content">
					<div class="dd-tabbar dd-main-tabs">
						<button class="dd-tab" data-tab="overview">${__("Overview")}</button>
						<button class="dd-tab" data-tab="trends">${__("Trends")}</button>
						<button class="dd-tab" data-tab="projects">${__("Projects")}</button>
						<button class="dd-tab" data-tab="monthly">${__("Monthly")}</button>
						<button class="dd-tab" data-tab="detail">${__("DOR Detail")}</button>
						<button class="dd-tab" data-tab="flagged">${__("Flagged Days")}<span class="dd-badge"></span></button>
						<span class="dd-spacer"></span>
						<button class="btn btn-xs btn-default dd-export">${__("Export CSV")}</button>
					</div>

					<div class="dd-pane" data-pane="overview">
						<div class="dd-kpis"></div>
						<div class="dd-grid">
							<div class="dd-card">
								<div class="dd-card-title">${__("Monthly Cost / M3 by Category")}</div>
								<div class="dd-chart" data-chart="monthly"></div>
							</div>
							<div class="dd-card">
								<div class="dd-card-title">${__("Cost Mix")}</div>
								<div class="dd-chart" data-chart="mix"></div>
							</div>
						</div>
					</div>

					<div class="dd-pane" data-pane="trends">
						<div class="dd-card dd-gap">
							<div class="dd-card-title">${__("Daily Total Cost / M3 (with 7-day average)")}</div>
							<div class="dd-chart" data-chart="daily"></div>
						</div>
						<div class="dd-card dd-gap">
							<div class="dd-card-title">${__("Monthly Treated Water (M3)")}</div>
							<div class="dd-chart" data-chart="volume"></div>
						</div>
					</div>

					<div class="dd-pane" data-pane="projects">
						<div class="dd-card dd-gap">
							<div class="dd-card-title dd-projects-title">${__("Project Comparison - Cost / M3")}</div>
							<div class="dd-chart" data-chart="projects"></div>
						</div>
						<div class="dd-card dd-tbl" data-tbl="projects"></div>
					</div>

					<div class="dd-pane" data-pane="monthly">
						<div class="dd-card dd-tbl" data-tbl="monthly"></div>
					</div>

					<div class="dd-pane" data-pane="detail">
						<div class="dd-card dd-tbl" data-tbl="detail"></div>
					</div>

					<div class="dd-pane" data-pane="flagged">
						<div class="dd-card dd-tbl" data-tbl="flagged"></div>
					</div>

					<div class="dd-footer text-muted"></div>
				</div>
			</div>
		`).appendTo(this.page.main);

		this.$body.on("click", ".dd-tab", (e) => {
			this.active_tab = $(e.currentTarget).data("tab");
			this.render_tabs();
		});
		this.$body.on("click", ".dd-export", () => this.export_csv());
		this.$body.on("click", "th[data-sort]", (e) => {
			const $th = $(e.currentTarget);
			const id = $th.closest("table").data("table");
			const key = $th.data("sort");
			const cur = this.sort[id];
			this.sort[id] = {
				key,
				dir: cur && cur.key === key && cur.dir === "desc" ? "asc" : "desc",
			};
			this.render_tables();
		});
		this.$body.on("click", ".dd-more", (e) => {
			const id = $(e.currentTarget).data("table");
			this.limit[id] = (this.limit[id] || 100) + 200;
			this.render_tables();
		});
	}

	// --------------------------------------------------------
	// Filters
	// --------------------------------------------------------
	preset_range(name) {
		const m = moment();
		const f = "YYYY-MM-DD";
		switch (name) {
			case "This Month":
				return [m.clone().startOf("month").format(f), m.clone().endOf("month").format(f)];
			case "Last Month": {
				const l = m.clone().subtract(1, "month");
				return [l.clone().startOf("month").format(f), l.clone().endOf("month").format(f)];
			}
			case "Last 3 Months":
				return [m.clone().subtract(2, "months").startOf("month").format(f), m.format(f)];
			case "Year to Date":
				return [m.clone().startOf("year").format(f), m.format(f)];
			case "Last 12 Months":
				return [m.clone().subtract(11, "months").startOf("month").format(f), m.format(f)];
			case "Last 30 Days":
			default:
				return [m.clone().subtract(29, "days").format(f), m.format(f)];
		}
	}

	apply_preset(name) {
		if (name === "Custom") return;
		const [from, to] = this.preset_range(name);
		this.silent = true;
		this.f.preset.set_value(name);
		this.f.from_date.set_value(from);
		this.f.to_date.set_value(to);
		setTimeout(() => {
			this.silent = false;
		}, 500);
		this.refresh_debounced();
	}

	on_date_change() {
		if (this.silent) return;
		this.silent = true;
		this.f.preset.set_value("Custom");
		setTimeout(() => {
			this.silent = false;
		}, 500);
		this.refresh_debounced();
	}

	get_filters() {
		return {
			from_date: this.f.from_date.get_value(),
			to_date: this.f.to_date.get_value(),
			project: this.f.project.get_value() || "",
			exclude_zero: this.f.exclude_zero.get_value() ? 1 : 0,
			compare: this.f.compare.get_value() ? 1 : 0,
		};
	}

	target() {
		return flt(this.f.target.get_value());
	}

	display() {
		return this.f.display.get_value() || "Both";
	}

	// --------------------------------------------------------
	// Data
	// --------------------------------------------------------
	refresh() {
		const filters = this.get_filters();
		if (!filters.from_date || !filters.to_date) return;

		const req_id = ++this.req_id;
		this.$body.addClass("dd-loading");

		frappe.call({
			method: API,
			args: { filters },
			callback: (r) => {
				if (req_id !== this.req_id) return; // stale response
				this.$body.removeClass("dd-loading");
				this.data = r.message;
				this.render();
			},
			error: () => {
				this.$body.removeClass("dd-loading");
			},
		});
	}

	// --------------------------------------------------------
	// Formatting helpers
	// --------------------------------------------------------
	fmt_cur(v, decimals = 2) {
		return format_currency(flt(v), this.currency, decimals);
	}
	fmt_m3(v) {
		return format_currency(flt(v), this.currency, 3);
	}
	fmt_num(v, decimals = 2) {
		return format_number(flt(v), null, decimals);
	}
	esc(v) {
		return frappe.utils.escape_html(v == null ? "" : String(v));
	}
	user_date(d) {
		return d ? frappe.datetime.str_to_user(d) : "";
	}
	link(url, text) {
		return `<a href="${url}" target="_blank" rel="noopener">${this.esc(text)}</a>`;
	}
	project_link(id, name) {
		if (!id) return this.esc(name || __("(No Project)"));
		return this.link(`/app/project/${encodeURIComponent(id)}`, name || id);
	}
	dor_link(name) {
		return this.link(`/app/daily-operation-report/${encodeURIComponent(name)}`, name);
	}

	delta_html(cur, prev, good_when_up) {
		if (!flt(prev)) return `<span class="dd-delta dd-na" title="${__("No previous data")}">&mdash;</span>`;
		const pct = ((flt(cur) - flt(prev)) / flt(prev)) * 100;
		if (Math.abs(pct) < 0.05) return `<span class="dd-delta dd-na">0.0%</span>`;
		const up = pct > 0;
		const good = up === good_when_up;
		return `<span class="dd-delta ${good ? "dd-good" : "dd-bad"}" title="${__("vs previous period")}">${
			up ? "&#9650;" : "&#9660;"
		} ${Math.abs(pct).toFixed(1)}%</span>`;
	}

	// --------------------------------------------------------
	// Render
	// --------------------------------------------------------
	render() {
		const d = this.data;
		if (!d) return;

		this.render_period();

		if (!d.kpis) {
			this.$body.find(".dd-content").hide();
			this.$body
				.find(".dd-empty")
				.html(`${__("No submitted Daily Operation Reports found for the selected filters.")}`)
				.show();
			return;
		}

		this.$body.find(".dd-empty").hide();
		this.$body.find(".dd-content").show();

		this.render_kpis();
		this.render_tables();
		this.render_tabs();

		let footer = `${__("Generated")}: ${d.generated_at} &nbsp;|&nbsp; ${__("DORs")}: ${d.row_count}`;
		if (d.rows_truncated) {
			footer += ` &nbsp;|&nbsp; ${__("DOR Detail shows the latest {0} only", [d.rows.length])}`;
		}
		this.$body.find(".dd-footer").html(footer);
	}

	render_period() {
		const d = this.data;
		const p = d.period;
		let html = `${__("Period")}: <b>${this.user_date(p.from_date)}</b> &rarr; <b>${this.user_date(
			p.to_date
		)}</b> (${__("{0} days", [p.days])})`;
		const project = this.f.project.get_value();
		if (project) html += ` &nbsp;|&nbsp; ${__("Project")}: <b>${this.esc(project)}</b>`;
		if (d.previous_period) {
			html += ` &nbsp;|&nbsp; ${__("Compared with")} ${this.user_date(
				d.previous_period.from_date
			)} &rarr; ${this.user_date(d.previous_period.to_date)}`;
		}
		this.$body.find(".dd-period").html(html);
	}

	kpi(label, value, delta, sub, color, over) {
		return `
			<div class="dd-kpi ${over ? "dd-kpi-over" : ""}" style="border-top-color:${color}">
				<div class="dd-kpi-label">${label}</div>
				<div class="dd-kpi-value">${value}</div>
				<div class="dd-kpi-foot">${delta || ""}<span class="dd-kpi-sub">${sub || ""}</span></div>
			</div>`;
	}

	render_kpis() {
		const d = this.data;
		const k = d.kpis;
		const p = d.previous_kpis;
		const target = this.target();
		const dl = (key, good_up) => (p ? this.delta_html(k[key], p[key], good_up) : "");

		const over = target && k.total_cost_per_m3 > target;
		let target_sub = "";
		if (target) {
			target_sub = over
				? `<span class="dd-bad-text">${__("Above target")} (${this.fmt_m3(target)})</span>`
				: `<span class="dd-good-text">${__("Within target")} (${this.fmt_m3(target)})</span>`;
		}

		const cards = [];
		cards.push(
			this.kpi(
				__("Treated Water (m³)"),
				this.fmt_num(k.treated_water),
				dl("treated_water", true),
				`${this.fmt_num(k.avg_daily_volume)} m³/${__("day")} &middot; ${k.days_with_data} ${__("days")}`,
				"#1976a8"
			)
		);
		cards.push(
			this.kpi(__("Total Cost"), this.fmt_cur(k.total_cost), dl("total_cost", false), `${k.dor_count} ${__("DORs")}`, "#1976a8")
		);
		cards.push(
			this.kpi(
				__("Total Cost / m³"),
				this.fmt_m3(k.total_cost_per_m3),
				dl("total_cost_per_m3", false),
				target_sub,
				over ? "#e24c4c" : "#2e9e6f",
				over
			)
		);

		CATS.forEach((c) => {
			const share = k.total_cost ? (k[`${c.key}_cost`] / k.total_cost) * 100 : 0;
			cards.push(
				this.kpi(
					`${__(c.label)} / m³`,
					this.fmt_m3(k[`${c.key}_cost_per_m3`]),
					dl(`${c.key}_cost_per_m3`, false),
					`${share.toFixed(1)}% ${__("of cost")}`,
					c.color
				)
			);
		});

		// Peak / best day (days with treated water only)
		const days = d.daily.filter((x) => x.treated_water > 0);
		if (days.length) {
			const peak = days.reduce((a, b) => (b.total_cost_per_m3 > a.total_cost_per_m3 ? b : a));
			const best = days.reduce((a, b) => (b.total_cost_per_m3 < a.total_cost_per_m3 ? b : a));
			cards.push(
				this.kpi(__("Peak Day / m³"), this.fmt_m3(peak.total_cost_per_m3), "", this.user_date(peak.date), "#e24c4c")
			);
			cards.push(
				this.kpi(__("Best Day / m³"), this.fmt_m3(best.total_cost_per_m3), "", this.user_date(best.date), "#2e9e6f")
			);
		}

		this.$body.find(".dd-kpis").html(cards.join(""));
	}

	// --------------------------------------------------------
	// Charts
	// --------------------------------------------------------
	chart(name, config) {
		const $el = this.$body.find(`[data-chart="${name}"]`);
		$el.empty();
		try {
			new frappe.Chart($el[0], Object.assign({ height: 260 }, config));
		} catch (e) {
			console.error(`DOR dashboard chart ${name} failed`, e);
		}
	}

	round(v) {
		return Math.round(flt(v) * 10000) / 10000;
	}

	render_charts() {
		const d = this.data;
		const target = this.target();
		const markers = target
			? [{ label: __("Target"), value: target, options: { labelPos: "left" } }]
			: [];
		const tip = { formatTooltipY: (v) => this.fmt_m3(v) };
		const colors = CATS.map((c) => c.color);
		const on = (...tabs) => tabs.includes(this.active_tab);

		// 1. Monthly stacked cost / m3
		if (on("overview"))
			this.chart("monthly", {
			type: "bar",
			colors,
			data: {
				labels: d.monthly.map((m) => m.month_label),
				datasets: CATS.map((c) => ({
					name: __(c.label),
					values: d.monthly.map((m) => this.round(m[`${c.key}_cost_per_m3`])),
				})),
				yMarkers: markers,
			},
			barOptions: { stacked: 1, spaceRatio: 0.4 },
			tooltipOptions: tip,
		});

		// 2. Cost mix donut
		const k = d.kpis;
		if (!on("overview")) {
			// not visible - skip
		} else if (k.total_cost > 0) {
			this.chart("mix", {
				type: "donut",
				colors,
				data: {
					labels: CATS.map((c) => __(c.label)),
					datasets: [{ values: CATS.map((c) => this.round(k[`${c.key}_cost`])) }],
				},
				tooltipOptions: { formatTooltipY: (v) => this.fmt_cur(v) },
			});
		} else {
			this.$body.find('[data-chart="mix"]').html(`<div class="text-muted">${__("No cost data")}</div>`);
		}

		// 3. Daily trend + 7-day average (SUM cost / SUM volume over the window)
		const daily = d.daily;
		const avg7 = daily.map((_, i) => {
			const win = daily.slice(Math.max(0, i - 6), i + 1);
			const cost = win.reduce((s, x) => s + x.total_cost, 0);
			const vol = win.reduce((s, x) => s + x.treated_water, 0);
			return vol ? this.round(cost / vol) : 0;
		});
		if (on("trends"))
			this.chart("daily", {
			type: "line",
			colors: ["#1976a8", "#f0a030"],
			data: {
				labels: daily.map((x) => moment(x.date).format("DD MMM")),
				datasets: [
					{ name: __("Total Cost / M3"), values: daily.map((x) => this.round(x.total_cost_per_m3)) },
					{ name: __("7-day average"), values: avg7 },
				],
				yMarkers: markers,
			},
			axisOptions: { xIsSeries: 1 },
			lineOptions: { hideDots: daily.length > 31 ? 1 : 0, regionFill: 0 },
			tooltipOptions: tip,
		});

		// 4. Project comparison (top 12 by total cost, stacked per category)
		const top = d.projects.slice(0, 12);
		this.$body
			.find(".dd-projects-title")
			.text(
				d.projects.length > 12
					? __("Project Comparison - Cost / M3 (top 12 by cost)")
					: __("Project Comparison - Cost / M3")
			);
		if (on("projects"))
			this.chart("projects", {
			type: "bar",
			colors,
			data: {
				labels: top.map((x) => x.project_name),
				datasets: CATS.map((c) => ({
					name: __(c.label),
					values: top.map((x) => this.round(x[`${c.key}_cost_per_m3`])),
				})),
				yMarkers: markers,
			},
			barOptions: { stacked: 1, spaceRatio: 0.4 },
			tooltipOptions: tip,
		});

		// 5. Monthly volume
		if (on("trends"))
			this.chart("volume", {
			type: "bar",
			colors: ["#1976a8"],
			data: {
				labels: d.monthly.map((m) => m.month_label),
				datasets: [{ name: __("Treated Water (M3)"), values: d.monthly.map((m) => this.round(m.treated_water)) }],
			},
			barOptions: { spaceRatio: 0.4 },
			tooltipOptions: { formatTooltipY: (v) => `${this.fmt_num(v)} m³` },
		});
	}

	// --------------------------------------------------------
	// Tables
	// --------------------------------------------------------
	value_columns() {
		const display = this.display();
		const show_cost = display === "Both" || display === "Cost Only";
		const show_m3 = display === "Both" || display === "Cost per M3 Only";
		const cols = [{ key: "treated_water", label: __("Treated Water (M3)"), kind: "num" }];

		CATS.forEach((c) => {
			if (show_cost) cols.push({ key: `${c.key}_cost`, label: __(`${c.label} Cost`), kind: "cur" });
			if (show_m3) cols.push({ key: `${c.key}_cost_per_m3`, label: `${__(c.label)} / M3`, kind: "m3", m3: true });
		});
		if (show_cost) cols.push({ key: "total_cost", label: __("Total Cost"), kind: "cur" });
		if (show_m3) cols.push({ key: "total_cost_per_m3", label: __("Total Cost / M3"), kind: "m3", m3: true, total: true });
		return cols;
	}

	cell(col, row) {
		const v = row[col.key];
		switch (col.kind) {
			case "num":
				return this.fmt_num(v);
			case "cur":
				return this.fmt_cur(v);
			case "m3": {
				const over = col.total && this.target() && flt(v) > this.target();
				return `<span class="${over ? "dd-over" : ""}">${this.fmt_m3(v)}</span>`;
			}
			case "int":
				return cstr(v);
			case "pct":
				return `${flt(v).toFixed(1)}%`;
			case "html":
				return col.render(row);
			default:
				return this.esc(v);
		}
	}

	raw_cell(col, row) {
		if (col.kind === "html") return col.raw ? col.raw(row) : "";
		const v = row[col.key];
		return v == null ? "" : v;
	}

	sorted_rows(id, rows, columns) {
		const s = this.sort[id];
		if (!s) return rows;
		const col = columns.find((c) => c.key === s.key);
		const get = (r) => (col && col.sort_value ? col.sort_value(r) : r[s.key]);
		return rows.slice().sort((a, b) => {
			const x = get(a);
			const y = get(b);
			let cmp;
			if (typeof x === "number" && typeof y === "number") cmp = x - y;
			else cmp = String(x == null ? "" : x).localeCompare(String(y == null ? "" : y));
			return s.dir === "asc" ? cmp : -cmp;
		});
	}

	table(id, columns, rows, total_row, default_limit = 100) {
		rows = this.sorted_rows(id, rows, columns);
		const limit = this.limit[id] || default_limit;
		const shown = rows.slice(0, limit);
		const s = this.sort[id];

		this.tables = this.tables || {};
		this.tables[id] = { columns, rows, total_row };

		const head = columns
			.map((c) => {
				const arrow = s && s.key === c.key ? (s.dir === "asc" ? " &#9650;" : " &#9660;") : "";
				const align = c.kind === "text" || c.kind === "html" ? "" : "dd-r";
				return `<th class="${align} ${c.m3 ? "dd-m3" : ""}" data-sort="${c.key}">${c.label}${arrow}</th>`;
			})
			.join("");

		const body = shown
			.map(
				(row) =>
					`<tr>${columns
						.map((c) => {
							const align = c.kind === "text" || c.kind === "html" ? "" : "dd-r";
							return `<td class="${align} ${c.m3 ? "dd-m3" : ""}">${this.cell(c, row)}</td>`;
						})
						.join("")}</tr>`
			)
			.join("");

		let foot = "";
		if (total_row) {
			foot = `<tr class="dd-total">${columns
				.map((c, i) => {
					const align = c.kind === "text" || c.kind === "html" ? "" : "dd-r";
					const content = i === 0 && c.kind !== "num" && c.kind !== "cur" && c.kind !== "m3" ? __("Total") : this.total_cell(c, total_row);
					return `<td class="${align} ${c.m3 ? "dd-m3" : ""}">${content}</td>`;
				})
				.join("")}</tr>`;
		}

		const more =
			rows.length > shown.length
				? `<div class="dd-more-wrap"><button class="btn btn-xs btn-default dd-more" data-table="${id}">${__(
						"Show more"
				  )} (${shown.length} / ${rows.length})</button></div>`
				: "";

		return `<div class="dd-table-wrap"><table class="dd-table" data-table="${id}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody>${
			foot ? `<tfoot>${foot}</tfoot>` : ""
		}</table></div>${more}`;
	}

	total_cell(col, row) {
		if (col.kind === "html" || col.kind === "text") return "";
		if (col.kind === "pct") return "100.0%";
		if (row[col.key] == null) return "";
		return this.cell(col, row);
	}

	render_tables() {
		const d = this.data;
		const k = d.kpis;
		const value_cols = this.value_columns();

		// Projects
		const project_rows = d.projects.map((p) =>
			Object.assign({}, p, { share: k.total_cost ? (p.total_cost / k.total_cost) * 100 : 0 })
		);
		const project_cols = [
			{
				key: "project_name",
				label: __("Project"),
				kind: "html",
				render: (r) => this.project_link(r.project, r.project_name),
				raw: (r) => r.project_name,
				sort_value: (r) => r.project_name,
			},
			{ key: "dor_count", label: __("DORs"), kind: "int" },
			...value_cols,
			{ key: "share", label: __("Share of Cost"), kind: "pct" },
		];
		this.$body.find('[data-tbl="projects"]').html(this.table("projects", project_cols, project_rows, k));

		// Monthly
		const monthly_cols = [
			{ key: "month_sort", label: __("Month"), kind: "html", render: (r) => this.esc(r.month_label), raw: (r) => r.month_label, sort_value: (r) => r.month_sort },
			{ key: "dor_count", label: __("DORs"), kind: "int" },
			...value_cols,
		];
		this.$body.find('[data-tbl="monthly"]').html(this.table("monthly", monthly_cols, d.monthly, k));

		// DOR detail
		const detail_cols = [
			{ key: "dor", label: __("DOR"), kind: "html", render: (r) => this.dor_link(r.dor), raw: (r) => r.dor, sort_value: (r) => r.dor },
			{ key: "date", label: __("Date"), kind: "html", render: (r) => this.esc(this.user_date(r.date)), raw: (r) => r.date, sort_value: (r) => r.date },
			{
				key: "project_name",
				label: __("Project"),
				kind: "html",
				render: (r) => this.project_link(r.project, r.project_name),
				raw: (r) => r.project_name || r.project,
				sort_value: (r) => r.project_name || r.project,
			},
			...value_cols,
		];
		this.$body.find('[data-tbl="detail"]').html(this.table("detail", detail_cols, d.rows, null));

		// Flagged days
		const a = d.anomalies;
		const flagged_cols = [
			{ key: "dor", label: __("DOR"), kind: "html", render: (r) => this.dor_link(r.dor), raw: (r) => r.dor, sort_value: (r) => r.dor },
			{ key: "date", label: __("Date"), kind: "html", render: (r) => this.esc(this.user_date(r.date)), raw: (r) => r.date, sort_value: (r) => r.date },
			{
				key: "project_name",
				label: __("Project"),
				kind: "html",
				render: (r) => this.project_link(r.project, r.project_name),
				raw: (r) => r.project_name,
				sort_value: (r) => r.project_name,
			},
			{ key: "treated_water", label: __("Treated Water (M3)"), kind: "num" },
			{ key: "total_cost_per_m3", label: __("Total Cost / M3"), kind: "m3", m3: true },
			{ key: "mean", label: __("Period Average / M3"), kind: "m3" },
			{ key: "pct_above", label: __("Above Average"), kind: "pct" },
			{ key: "driver", label: __("Main Driver"), kind: "text" },
		];
		const flagged_note = a.items.length
			? `<div class="dd-note">${__(
					"DORs with Total Cost / M3 above {0} (average + 2 standard deviations). Main driver = category furthest above its own average.",
					[this.fmt_m3(a.threshold)]
			  )}</div>`
			: `<div class="dd-note">${__(
					"No unusual days found (needs at least 8 DORs with treated water and some variation)."
			  )}</div>`;
		this.$body
			.find('[data-tbl="flagged"]')
			.html(flagged_note + (a.items.length ? this.table("flagged", flagged_cols, a.items, null) : ""));
		this.$body.find(".dd-badge").text(a.items.length ? a.items.length : "");
	}

	render_tabs() {
		const tab = this.active_tab;
		this.$body.find(".dd-tab").removeClass("active");
		this.$body.find(`.dd-tab[data-tab="${tab}"]`).addClass("active");
		this.$body.find(".dd-pane").hide();
		this.$body.find(`.dd-pane[data-pane="${tab}"]`).show();

		const table_tabs = { projects: "projects", monthly: "monthly", detail: "detail", flagged: "flagged" };
		this.current_table = table_tabs[tab] || null;
		this.$body.find(".dd-export").toggle(!!this.current_table);

		// Charts are drawn only when their tab is visible (frappe-charts
		// cannot size itself inside a hidden container).
		if (this.data && this.data.kpis) this.render_charts();
	}

	// --------------------------------------------------------
	// Export / drill-down
	// --------------------------------------------------------
	export_csv() {
		const t = this.tables && this.tables[this.current_table];
		if (!t) {
			frappe.show_alert({ message: __("Nothing to export yet"), indicator: "orange" });
			return;
		}

		const q = (v) => `"${String(v == null ? "" : v).replace(/"/g, '""')}"`;
		const header = t.columns.map((c) => q(c.label)).join(",");
		const lines = t.rows.map((r) => t.columns.map((c) => q(this.raw_cell(c, r))).join(","));
		const csv = "\ufeff" + [header, ...lines].join("\n");

		const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `dor_cost_${this.current_table}_${frappe.datetime.get_today()}.csv`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	open_report() {
		const f = this.get_filters();
		const q = (k, v) => `${k}=${encodeURIComponent(v)}`;
		const params = [
			q("from_date", f.from_date),
			q("to_date", f.to_date),
			q("display", this.display()),
		];
		if (f.project) params.push(q("project", f.project));
		if (f.exclude_zero) params.push(q("exclude_zero_volume", 1));

		const url = `/app/query-report/${encodeURIComponent(REPORT_NAME)}?${params.join("&")}`;
		window.open(url, "_blank");
	}

	// --------------------------------------------------------
	// Full professional print (opens a print preview in a new tab)
	// --------------------------------------------------------
	print_full_report() {
		const d = this.data;
		if (!d || !d.kpis) {
			frappe.show_alert({ message: __("Nothing to print - no data for the selected filters"), indicator: "orange" });
			return;
		}

		const w = window.open("", "_blank");
		if (!w) {
			frappe.msgprint(__("Please allow pop-ups for this site to open the print preview."));
			return;
		}
		w.document.write(this.build_print_html());
		w.document.close();
	}

	svg_nice_max(v) {
		if (!(v > 0)) return 1;
		const exp = Math.pow(10, Math.floor(Math.log10(v)));
		const f = v / exp;
		const nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10;
		return nf * exp;
	}

	svg_num(v) {
		v = flt(v);
		if (Math.abs(v) >= 10000) return (v / 1000).toFixed(0) + "k";
		if (Math.abs(v) >= 1000) return (v / 1000).toFixed(1) + "k";
		return String(Math.round(v * 1000) / 1000);
	}

	svg_trunc(text, n) {
		text = String(text == null ? "" : text);
		return text.length > n ? text.slice(0, n - 1) + "…" : text;
	}

	svg_grid(w, h, m, max) {
		let out = "";
		const steps = 5;
		for (let i = 0; i <= steps; i++) {
			const val = (max / steps) * i;
			const y = m.t + (h - m.t - m.b) * (1 - i / steps);
			out += `<line x1="${m.l}" y1="${y}" x2="${w - m.r}" y2="${y}" stroke="#e3e8ec" stroke-width="1"/>`;
			out += `<text x="${m.l - 6}" y="${y + 3}" text-anchor="end" font-size="9" fill="#6b7c85">${this.svg_num(val)}</text>`;
		}
		return out;
	}

	svg_wrap(w, h, inner) {
		return `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;font-family:Segoe UI,Arial,sans-serif">${inner}</svg>`;
	}

	svg_stacked({ labels, series, target, width = 520, height = 240 }) {
		const rotate = labels.length > 6;
		const m = { l: 44, r: 8, t: 10, b: rotate ? 58 : 28 };
		const totals = labels.map((l, i) => series.reduce((s, x) => s + flt(x.values[i]), 0));
		const max = this.svg_nice_max(Math.max(0, flt(target), ...totals));
		const ph = height - m.t - m.b;
		const slot = (width - m.l - m.r) / Math.max(labels.length, 1);
		const bar = Math.min(slot * 0.62, 56);

		let out = this.svg_grid(width, height, m, max);
		labels.forEach((label, i) => {
			const x = m.l + slot * i + (slot - bar) / 2;
			let y = m.t + ph;
			series.forEach((s) => {
				const bh = (flt(s.values[i]) / max) * ph;
				if (bh > 0) {
					y -= bh;
					out += `<rect x="${x}" y="${y}" width="${bar}" height="${bh}" fill="${s.color}"/>`;
				}
			});
			const lx = m.l + slot * i + slot / 2;
			const ly = height - m.b + 12;
			out += rotate
				? `<text transform="translate(${lx},${ly}) rotate(-38)" text-anchor="end" font-size="9" fill="#44525b">${this.esc(label)}</text>`
				: `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="9" fill="#44525b">${this.esc(label)}</text>`;
		});
		if (target) {
			const ty = m.t + ph * (1 - flt(target) / max);
			out += `<line x1="${m.l}" y1="${ty}" x2="${width - m.r}" y2="${ty}" stroke="#e24c4c" stroke-width="1.2" stroke-dasharray="5 3"/>`;
		}
		return this.svg_wrap(width, height, out);
	}

	svg_line({ labels, series, target, width = 1060, height = 230 }) {
		const m = { l: 44, r: 10, t: 10, b: 28 };
		const all = series.flatMap((s) => s.values.map((v) => flt(v)));
		const max = this.svg_nice_max(Math.max(0, flt(target), ...all));
		const pw = width - m.l - m.r;
		const ph = height - m.t - m.b;
		const n = labels.length;
		const x = (i) => m.l + (n > 1 ? (pw * i) / (n - 1) : pw / 2);
		const y = (v) => m.t + ph * (1 - flt(v) / max);

		let out = this.svg_grid(width, height, m, max);
		const step = Math.max(1, Math.ceil(n / 12));
		labels.forEach((label, i) => {
			if (i % step === 0) {
				out += `<text x="${x(i)}" y="${height - m.b + 14}" text-anchor="middle" font-size="9" fill="#44525b">${this.esc(label)}</text>`;
			}
		});
		series.forEach((s) => {
			const pts = s.values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
			out += `<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="1.8" ${
				s.dash ? `stroke-dasharray="${s.dash}"` : ""
			}/>`;
			if (n <= 31 && !s.dash) {
				s.values.forEach((v, i) => {
					out += `<circle cx="${x(i)}" cy="${y(v)}" r="2.2" fill="${s.color}"/>`;
				});
			}
		});
		if (target) {
			const ty = y(target);
			out += `<line x1="${m.l}" y1="${ty}" x2="${width - m.r}" y2="${ty}" stroke="#e24c4c" stroke-width="1.2" stroke-dasharray="5 3"/>`;
		}
		return this.svg_wrap(width, height, out);
	}

	svg_donut(values, colors, size = 170) {
		const total = values.reduce((a, b) => a + flt(b), 0);
		if (!(total > 0)) return "";
		const r = size / 2;
		const ro = r - 4;
		const ri = ro * 0.58;
		const pt = (rad, ang) => [r + rad * Math.cos(ang), r + rad * Math.sin(ang)];
		let a0 = -Math.PI / 2;
		let out = "";
		values.forEach((v, i) => {
			const frac = flt(v) / total;
			if (frac <= 0) return;
			if (frac >= 0.9999) {
				out += `<circle cx="${r}" cy="${r}" r="${(ro + ri) / 2}" fill="none" stroke="${colors[i]}" stroke-width="${ro - ri}"/>`;
				return;
			}
			const a1 = a0 + frac * 2 * Math.PI;
			const large = frac > 0.5 ? 1 : 0;
			const [x0, y0] = pt(ro, a0);
			const [x1, y1] = pt(ro, a1);
			const [x2, y2] = pt(ri, a1);
			const [x3, y3] = pt(ri, a0);
			out += `<path d="M${x0},${y0} A${ro},${ro} 0 ${large} 1 ${x1},${y1} L${x2},${y2} A${ri},${ri} 0 ${large} 0 ${x3},${y3} Z" fill="${colors[i]}"/>`;
			a0 = a1;
		});
		return `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="width:${size}px;height:${size}px">${out}</svg>`;
	}

	print_table(id, title, note) {
		return this.print_table_from(this.tables && this.tables[id], title, note, false);
	}

	print_table_from(t, title, note, flow) {
		if (!t || !t.rows || !t.rows.length) return "";

		const cols = t.columns;
		const align = (c) => (c.kind === "text" || c.kind === "html" ? "" : "pr-r");
		const text_cell = (c, row) => {
			if (c.kind === "html") {
				return c.key === "date" ? this.esc(this.user_date(row.date)) : this.esc(c.raw ? c.raw(row) : "");
			}
			return this.cell(c, row);
		};

		const head = cols.map((c) => `<th class="${align(c)} ${c.m3 ? "pr-m3" : ""}">${c.label}</th>`).join("");
		const body = t.rows
			.map(
				(row) =>
					`<tr>${cols
						.map((c) => `<td class="${align(c)} ${c.m3 ? "pr-m3" : ""}">${text_cell(c, row)}</td>`)
						.join("")}</tr>`
			)
			.join("");

		let foot = "";
		if (t.total_row) {
			foot = `<tfoot><tr>${cols
				.map((c, i) => {
					const label_first = i === 0 && !["num", "cur", "m3"].includes(c.kind);
					const content = label_first ? __("Total") : this.total_cell(c, t.total_row);
					return `<td class="${align(c)} ${c.m3 ? "pr-m3" : ""}">${content}</td>`;
				})
				.join("")}</tr></tfoot>`;
		}

		return `
			<div class="pr-section pr-table-section${flow ? " pr-flow" : ""}">
				<h2>${title}<span class="pr-count">${t.rows.length}</span></h2>
				${note ? `<div class="pr-note">${note}</div>` : ""}
				<table class="pr-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody>${foot}</table>
			</div>`;
	}

	build_print_html() {
		const d = this.data;
		const k = d.kpis;
		const company = d.company || {};
		const target = this.target();
		const f = this.get_filters();
		const p = d.period;
		const esc = (v) => this.esc(v);

		// ---- filter line
		const project_name = f.project && d.projects.length ? d.projects[0].project_name : "";
		const bits = [
			`${__("Period")}: <b>${this.user_date(p.from_date)}</b> &rarr; <b>${this.user_date(p.to_date)}</b> (${__("{0} days", [p.days])})`,
		];
		if (f.project) {
			const extra = project_name && project_name !== f.project ? ` &ndash; ${esc(project_name)}` : "";
			bits.push(`${__("Project")}: <b>${esc(f.project)}${extra}</b>`);
		}
		if (d.previous_period) {
			bits.push(
				`${__("Compared with")} ${this.user_date(d.previous_period.from_date)} &rarr; ${this.user_date(d.previous_period.to_date)}`
			);
		}
		if (target) bits.push(`${__("Target Cost / M3")}: <b>${this.fmt_m3(target)}</b>`);
		if (f.exclude_zero) bits.push(__("Zero treated water days excluded"));
		const filter_line = bits.join(" &nbsp;|&nbsp; ");

		// ---- charts
		const cat_series = (rows) =>
			CATS.map((c) => ({
				name: __(c.label),
				color: c.color,
				values: rows.map((r) => r[`${c.key}_cost_per_m3`]),
			}));
		const legend = (items, with_target) =>
			`<div class="pr-legend">${items
				.map((i) => `<span><i style="background:${i.color}"></i>${esc(i.name)}</span>`)
				.join("")}${with_target && target ? `<span><i class="pr-dash"></i>${__("Target")}</span>` : ""}</div>`;
		const cat_legend = legend(
			CATS.map((c) => ({ name: __(c.label), color: c.color })),
			true
		);

		const months = d.monthly.map((m) => m.month_label);
		const monthly_svg = this.svg_stacked({ labels: months, series: cat_series(d.monthly), target });
		const volume_svg = this.svg_stacked({
			labels: months,
			series: [{ name: __("Treated Water (M3)"), color: "#1976a8", values: d.monthly.map((m) => m.treated_water) }],
		});

		const daily = d.daily;
		const avg7 = daily.map((x, i) => {
			const win = daily.slice(Math.max(0, i - 6), i + 1);
			const cost = win.reduce((s, y) => s + y.total_cost, 0);
			const vol = win.reduce((s, y) => s + y.treated_water, 0);
			return vol ? cost / vol : 0;
		});
		const daily_svg = this.svg_line({
			labels: daily.map((x) => moment(x.date).format("DD MMM")),
			series: [
				{ name: __("Total Cost / M3"), color: "#1976a8", values: daily.map((x) => x.total_cost_per_m3) },
				{ name: __("7-day average"), color: "#f0a030", values: avg7, dash: "4 3" },
			],
			target,
		});
		const daily_legend = legend(
			[
				{ name: __("Total Cost / M3"), color: "#1976a8" },
				{ name: __("7-day average"), color: "#f0a030" },
			],
			true
		);

		const top = d.projects.slice(0, 12);
		const projects_svg = this.svg_stacked({
			labels: top.map((x) => this.svg_trunc(x.project_name, 16)),
			series: cat_series(top),
			target,
		});

		const mix_values = CATS.map((c) => k[`${c.key}_cost`]);
		const donut = this.svg_donut(
			mix_values,
			CATS.map((c) => c.color)
		);
		const mix_rows = CATS.map((c) => {
			const cost = k[`${c.key}_cost`];
			const share = k.total_cost ? (cost / k.total_cost) * 100 : 0;
			return `<tr><td><i class="pr-dot" style="background:${c.color}"></i>${__(c.label)}</td><td class="pr-r">${this.fmt_cur(cost)}</td><td class="pr-r">${share.toFixed(1)}%</td></tr>`;
		}).join("");

		// ---- tables

		// Monthly breakdown for every project, one table per project
		const pm = d.project_monthly || [];
		const pm_cols = [
			{ key: "month_sort", label: __("Month"), kind: "html", raw: (r) => r.month_label },
			{ key: "dor_count", label: __("DORs"), kind: "int" },
			...this.value_columns(),
		];
		const project_monthly_html = pm.length
			? `<div class="pr-section pr-table-section"><h2>${__("Monthly Summary by Project")}<span class="pr-count">${pm.length}</span></h2></div>` +
			  pm
					.map((x) =>
						this.print_table_from(
							{ columns: pm_cols, rows: x.months, total_row: x.total },
							esc(x.project_name),
							"",
							true
						)
					)
					.join("")
			: "";

		const tables_html =
			this.print_table("projects", __("Projects")) +
			this.print_table("monthly", __("Monthly Summary")) +
			project_monthly_html;

		const logo = company.logo ? `<img src="${esc(company.logo)}" class="pr-logo"/>` : "";
		const user = frappe.session.user_fullname || frappe.session.user || "";

		return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>${__("DOR Cost Dashboard")}</title>
<style>
	@page { size: A4 landscape; margin: 10mm 9mm 14mm; }
	:root { --dark: #0b3d5c; --blue: #1976a8; --light: #eaf4fa; --accent: #2e9e6f; }
	* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
	body { font-family: "Segoe UI", Arial, sans-serif; color: #222; margin: 0; font-size: 11px; }

	.pr-header { display: flex; align-items: center; justify-content: space-between; background: linear-gradient(135deg, var(--dark), var(--blue)); color: #fff; padding: 12px 18px; border-radius: 8px; margin-bottom: 10px; }
	.pr-header .left { display: flex; align-items: center; gap: 12px; }
	.pr-logo { max-height: 42px; max-width: 130px; background: #fff; padding: 4px 8px; border-radius: 6px; }
	.pr-company { font-size: 16px; font-weight: 600; }
	.pr-sub { font-size: 11px; opacity: .9; margin-top: 2px; }
	.pr-header .right { text-align: right; }
	.pr-title { font-size: 19px; font-weight: 700; }
	.pr-meta { font-size: 10px; opacity: .9; margin-top: 4px; }

	.pr-filter { background: var(--light); border-left: 4px solid var(--blue); padding: 7px 12px; font-size: 11px; color: var(--dark); border-radius: 4px; margin-bottom: 12px; }

	.pr-section { margin-bottom: 14px; }
	.pr-section h2 { font-size: 13px; color: var(--dark); border-bottom: 2px solid var(--blue); padding-bottom: 4px; margin: 0 0 10px; display: flex; align-items: center; gap: 8px; }
	.pr-count { font-size: 10px; font-weight: 400; color: #6b7c85; background: #f1f4f6; border-radius: 10px; padding: 1px 8px; }
	.pr-note { font-size: 10px; color: #6b7c85; margin: -4px 0 8px; }

	.dd-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
	.dd-kpi { border: 1px solid #e0e6ea; border-top: 3px solid var(--blue); border-radius: 6px; padding: 8px 12px; break-inside: avoid; }
	.dd-kpi-over { background: #fdf0f0; }
	.dd-kpi-label { font-size: 9px; text-transform: uppercase; letter-spacing: .5px; color: #6b7c85; margin-bottom: 3px; }
	.dd-kpi-value { font-size: 17px; font-weight: 700; color: var(--dark); }
	.dd-kpi-foot { display: flex; gap: 8px; align-items: center; margin-top: 4px; font-size: 9.5px; flex-wrap: wrap; }
	.dd-kpi-sub { color: #6b7c85; }
	.dd-delta { font-weight: 700; }
	.dd-good, .dd-good-text { color: #1f8a5b; }
	.dd-bad, .dd-bad-text { color: #c0392b; }
	.dd-na { color: #8a97a0; }
	.dd-over { color: #c0392b; font-weight: 700; }

	.pr-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
	.pr-card { border: 1px solid #e0e6ea; border-radius: 6px; padding: 8px 10px; break-inside: avoid; }
	.pr-card.wide { grid-column: 1 / -1; }
	.pr-card h3 { font-size: 11px; margin: 0 0 6px; color: var(--dark); }
	.pr-legend { display: flex; gap: 12px; flex-wrap: wrap; font-size: 9.5px; color: #44525b; margin-top: 4px; }
	.pr-legend i, .pr-dot { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 4px; }
	.pr-dash { border-top: 2px dashed #e24c4c; background: none !important; height: 0 !important; border-radius: 0 !important; }
	.pr-mix { display: flex; align-items: center; gap: 16px; }
	.pr-mix table { border-collapse: collapse; font-size: 10.5px; flex: 1; }
	.pr-mix td { padding: 4px 6px; border-bottom: 1px solid #e6ebee; }

	.pr-table-section { page-break-before: always; }
	.pr-table-section ~ .pr-table-section { page-break-before: always; }
	.pr-table-section.pr-flow { page-break-before: auto; break-inside: avoid; margin-bottom: 12px; }
	table.pr-table { width: 100%; border-collapse: collapse; font-size: 8.5px; }
	.pr-table thead { display: table-header-group; }
	.pr-table tfoot { display: table-row-group; }
	.pr-table th { background: var(--dark); color: #fff; padding: 5px 6px; text-align: left; font-weight: 600; }
	.pr-table td { padding: 4px 6px; border-bottom: 1px solid #e6ebee; white-space: nowrap; }
	.pr-table tbody tr:nth-child(even) { background: #f7fafc; }
	.pr-table tr { page-break-inside: avoid; }
	.pr-r { text-align: right !important; }
	.pr-table td.pr-m3 { color: var(--blue); background: #f4fafd; font-weight: 600; }
	.pr-table tfoot td { background: var(--light); font-weight: 700; color: var(--dark); border-top: 2px solid var(--blue); }
	.pr-table tfoot td.pr-m3 { background: var(--blue); color: #fff; }

	.pr-footer { position: fixed; bottom: 0; left: 0; right: 0; font-size: 9px; color: #8a97a0; display: flex; justify-content: space-between; border-top: 1px solid #e0e6ea; padding-top: 4px; background: #fff; }
</style>
</head>
<body>
	<div class="pr-header">
		<div class="left">
			${logo}
			<div>
				<div class="pr-company">${esc(company.name || "")}</div>
				<div class="pr-sub">${__("Water Treatment Operations")}</div>
			</div>
		</div>
		<div class="right">
			<div class="pr-title">${__("DOR Cost Dashboard Report")}</div>
			<div class="pr-meta">${__("Generated")}: ${esc(d.generated_at)}${user ? ` &nbsp;|&nbsp; ${esc(user)}` : ""}</div>
		</div>
	</div>

	<div class="pr-filter">${filter_line}</div>

	<div class="pr-section">
		<h2>${__("Key Performance Indicators")}</h2>
		<div class="dd-kpis">${this.$body.find(".dd-kpis").html()}</div>
	</div>

	<div class="pr-section">
		<h2>${__("Cost Analysis")}</h2>
		<div class="pr-grid">
			<div class="pr-card"><h3>${__("Monthly Cost / M3 by Category")}</h3>${monthly_svg}${cat_legend}</div>
			<div class="pr-card"><h3>${__("Cost Mix")}</h3>
				<div class="pr-mix">${donut}<table>${mix_rows}</table></div>
			</div>
			<div class="pr-card wide"><h3>${__("Daily Total Cost / M3 (with 7-day average)")}</h3>${daily_svg}${daily_legend}</div>
			<div class="pr-card"><h3>${__("Monthly Treated Water (M3)")}</h3>${volume_svg}</div>
			<div class="pr-card"><h3>${d.projects.length > 12 ? __("Project Comparison - Cost / M3 (top 12 by cost)") : __("Project Comparison - Cost / M3")}</h3>${projects_svg}${cat_legend}</div>
		</div>
	</div>

	${tables_html}

	<div class="pr-footer">
		<span>${esc(company.name || "")} &mdash; ${__("DOR Cost Dashboard Report")}</span>
		<span>${this.user_date(p.from_date)} &rarr; ${this.user_date(p.to_date)}</span>
	</div>

	<script>
		window.onload = function () { setTimeout(function () { window.print(); }, 300); };
	</script>
</body>
</html>`;
	}

	// --------------------------------------------------------
	// Styles
	// --------------------------------------------------------
	inject_css() {
		if (document.getElementById("dor-dashboard-style")) return;
		const style = document.createElement("style");
		style.id = "dor-dashboard-style";
		style.textContent = `
			.dd-root { padding: 6px 0 30px; }
			.dd-root.dd-loading .dd-content { opacity: .5; pointer-events: none; transition: opacity .15s; }
			.dd-period { font-size: 12px; color: var(--text-muted); margin: 4px 0 12px; }
			.dd-empty { padding: 40px; text-align: center; color: var(--text-muted); background: var(--card-bg); border: 1px dashed var(--border-color); border-radius: 8px; }

			.dd-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-bottom: 14px; }
			.dd-kpi { background: var(--card-bg); border: 1px solid var(--border-color); border-top: 3px solid #1976a8; border-radius: 8px; padding: 12px 14px; }
			.dd-kpi-over { background: rgba(226, 76, 76, .06); }
			.dd-kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: .4px; color: var(--text-muted); margin-bottom: 4px; }
			.dd-kpi-value { font-size: 22px; font-weight: 700; color: var(--heading-color); line-height: 1.2; }
			.dd-kpi-foot { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 11px; flex-wrap: wrap; }
			.dd-kpi-sub { color: var(--text-muted); }
			.dd-delta { font-weight: 600; }
			.dd-good, .dd-good-text { color: #2e9e6f; }
			.dd-bad, .dd-bad-text { color: #e24c4c; }
			.dd-na { color: var(--text-muted); }
			.dd-over { color: #e24c4c; font-weight: 700; }

			.dd-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
			.dd-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 14px; min-width: 0; }
			.dd-wide { grid-column: 1 / -1; }
			.dd-card-title { font-weight: 600; font-size: 13px; margin-bottom: 8px; color: var(--heading-color); }
			.dd-chart .chart-container { margin: 0; }

			.dd-tbl { padding: 0; overflow: hidden; margin-bottom: 14px; }
			.dd-gap { margin-bottom: 14px; }
			.dd-main-tabs { margin-bottom: 14px; padding: 0; }
			.dd-tabbar { display: flex; align-items: center; gap: 2px; padding: 8px 10px 0; border-bottom: 1px solid var(--border-color); flex-wrap: wrap; }
			.dd-tab { background: none; border: none; padding: 8px 14px; font-size: 13px; color: var(--text-muted); border-bottom: 2px solid transparent; cursor: pointer; }
			.dd-tab.active { color: var(--heading-color); font-weight: 600; border-bottom-color: #1976a8; }
			.dd-badge { margin-left: 6px; background: #e24c4c; color: #fff; border-radius: 10px; padding: 0 6px; font-size: 10px; }
			.dd-badge:empty { display: none; }
			.dd-spacer { flex: 1; }
			.dd-export { margin-bottom: 6px; }
			.dd-pane { padding: 0; }
			.dd-note { padding: 10px 14px; font-size: 12px; color: var(--text-muted); }

			.dd-table-wrap { overflow-x: auto; }
			.dd-table { width: 100%; border-collapse: collapse; font-size: 12px; }
			.dd-table th { position: sticky; top: 0; background: var(--subtle-fg, var(--control-bg)); padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; cursor: pointer; border-bottom: 1px solid var(--border-color); user-select: none; }
			.dd-table td { padding: 7px 10px; border-bottom: 1px solid var(--border-color); white-space: nowrap; }
			.dd-table tbody tr:hover { background: var(--control-bg); }
			.dd-table .dd-r { text-align: right; }
			.dd-table .dd-m3 { color: #1976a8; font-weight: 600; }
			.dd-table .dd-m3 .dd-over { color: #e24c4c; }
			.dd-table tfoot td { font-weight: 700; background: var(--control-bg); border-top: 2px solid #1976a8; }
			.dd-more-wrap { text-align: center; padding: 10px; }
			.dd-footer { font-size: 11px; margin-top: 10px; }

			@media (max-width: 900px) { .dd-grid { grid-template-columns: 1fr; } }
			@media print {
				.page-head, .navbar, .dd-tabbar, .dd-more-wrap { display: none !important; }
				.dd-pane { page-break-inside: avoid; }
				.dd-card, .dd-kpi { break-inside: avoid; }
			}
		`;
		document.head.appendChild(style);
	}
}