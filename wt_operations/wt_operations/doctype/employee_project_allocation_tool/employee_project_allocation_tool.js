// client_script.js for Employee Allocation Dashboard DocType

frappe.ui.form.on('Employee Project Allocation Tool', {
    // refresh: function(frm) {
    //     frm.trigger('load_all_employee_allocations');
    // },
    
    load_all_employee_allocations: function(frm) {
        let wrapper = frm.get_field('allocation_details').$wrapper;
        wrapper.html('<div style="text-align: center; padding: 50px;"><i class="fa fa-spinner fa-spin"></i> Loading dashboard...</div>');
        
        // Fetch all employee allocations from server
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Employee Project Allocation',
                filters: {
                    docstatus: 0  // Submitted only
                },
                fields: ['name', 'employee', 'employee_name', 'from_date', 'to_date', 'total_percentage'],
                limit_page_length: 1000
            },
            callback: function(r) {
                if (r.message && r.message?.length > 0) {
                    fetch_allocation_details(frm, r.message);
                } else {
                    wrapper.html('<div class="alert alert-info">No employee allocations found. Please create allocations first.</div>');
                }
            }
        });
    }
});

function fetch_allocation_details(frm, allocations) {
    let employee_data = {};
    let processed = 0;
    let all_projects = new Set(); // Track all unique projects
    let all_activities = new Set(); // Track all unique activities (Operation, Installation, etc.)
    
    allocations.forEach(alloc => {
        // Fetch employee details
        frappe.db.get_value('Employee', alloc.employee, ['employee_name', 'department', 'designation'], (emp_data) => {
            // Fetch child table details using the correct field name
            frappe.db.get_list('Employee Project Allocation Details', {
                filters: { parent: alloc.name },
                fields: ["*"]
            }).then(details => {
                console.log(details);
                
                if (!employee_data[alloc.employee]) {
                    employee_data[alloc.employee] = {
                        employee_name: alloc.employee_name || emp_data.employee_name || alloc.employee,
                        department: emp_data.department || 'N/A',
                        designation: emp_data.designation || 'N/A',
                        allocations: [],
                        total_percentage: alloc.total_percentage || 0,
                        from_date: alloc.from_date,
                        to_date: alloc.to_date
                    };
                }
                
                details.forEach(detail => {
                    employee_data[alloc.employee].allocations.push({
                        project: detail.project,
                        activity: detail.activity,  // Using 'activity' field
                        percentage: detail.percentage
                    });
                    
                    // Collect unique projects and activities for dynamic table headers
                    all_projects.add(detail.project);
                    all_activities.add(detail.activity);
                });
                
                processed++;
                if (processed === allocations.length) {
                    render_complete_dashboard(frm, employee_data, Array.from(all_projects), Array.from(all_activities));
                }
            });
        });
    });
}

function render_complete_dashboard(frm, employee_data, all_projects, all_activities) {
    let wrapper = frm.get_field('allocation_details').$wrapper;
    
    // Convert to array for easier manipulation
    let employees = Object.values(employee_data);
    
    // Sort for consistent display
    all_projects.sort();
    all_activities.sort();
    
    // Calculate summary statistics
    let total_employees = employees.length;
    let fully_allocated = employees.filter(emp => emp.total_percentage === 100).length;
    let total_activity_hours = {};
    
    all_activities.forEach(activity => {
        total_activity_hours[activity] = 0;
    });
    
    employees.forEach(emp => {
        emp.allocations.forEach(alloc => {
            if (total_activity_hours[alloc.activity] !== undefined) {
                total_activity_hours[alloc.activity] += alloc.percentage;
            }
        });
    });
    
    let dashboard_html = `
        <div class="global-allocation-dashboard" style="padding: 20px; background: #f4f6f9; border-radius: 10px;">
            
            
            
            <!-- Main Matrix Table -->
            <div style="background: white; border-radius: 10px; overflow-x: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <table class="employee-matrix-table" style="width: 100%; border-collapse: collapse; min-width: 800px;">
                    <thead>
                        <tr style="background: #2c3e50; color: white;">
                            <th rowspan="2" style="padding: 12px; text-align: center; vertical-align: middle; width: 180px;">Employee</th>
                            ${generate_activity_headers(all_activities, all_projects)}
                            <th rowspan="2" style="padding: 12px; text-align: center; vertical-align: middle; width: 100px;">Total %</th>
                            <th rowspan="2" style="padding: 12px; text-align: center; vertical-align: middle; width: 100px;">Status</th>
                        </tr>
                        <tr style="background: #34495e; color: white;">
                            ${generate_project_subheaders(all_activities, all_projects)}
                        </tr>
                    </thead>
                    <tbody id="employeeTableBody">
                        ${generate_dynamic_employee_rows(employees, all_activities, all_projects)}
                    </tbody>
                    <tfoot style="background: #f8f9fa; font-weight: bold;">
                        ${generate_dynamic_table_footer(employees, all_activities, all_projects)}
                    </tfoot>
                </table>
            </div>
            
          
            
            <!-- Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 25px;">
                <div style="background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #3498db; font-size: 32px;">${total_employees}</h3>
                    <div style="color: #666;">Total Employees</div>
                </div>
                <div style="background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 style="margin: 0; color: #27ae60; font-size: 32px;">${fully_allocated}</h3>
                    <div style="color: #666;">Fully Allocated (100%)</div>
                </div>
                ${generate_activity_summary_cards(all_activities, total_activity_hours)}
            </div>
            
            <!-- Filters -->
            <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <div style="flex: 1;">
                        <label>Search Employee:</label>
                        <input type="text" id="searchEmployee" class="form-control" placeholder="Type employee name..." onkeyup="filterEmployeeTable()">
                    </div>
                    <div style="flex: 1;">
                        <label>Filter by Department:</label>
                        <select id="deptFilter" class="form-control" onchange="filterEmployeeTable()">
                            <option value="">All Departments</option>
                            ${get_unique_departments(employees)}
                        </select>
                    </div>
                    <div style="flex: 1;">
                        <label>Allocation Status:</label>
                        <select id="statusFilter" class="form-control" onchange="filterEmployeeTable()">
                            <option value="all">All</option>
                            <option value="complete">Complete (100%)</option>
                            <option value="incomplete">Incomplete (<100%)</option>
                            <option value="over">Over (>100%)</option>
                        </select>
                    </div>
                    <div style="flex: 1;">
                        <label>Activity Type:</label>
                        <select id="activityFilter" class="form-control" onchange="filterEmployeeTable()">
                            <option value="all">All Activities</option>
                            ${generate_activity_filter_options(all_activities)}
                        </select>
                    </div>
                </div>
            </div>

              <!-- Dashboard Header -->
            <div style="background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0;">🏢 Global Employee Allocation Matrix</h2>
                        <p style="margin: 5px 0 0;">Dynamic View from Employee Project Allocation Data</p>
                    </div>
                    <div>
                        <button class="btn btn-light btn-sm" onclick="refreshGlobalDashboard()">
                            <i class="fa fa-refresh"></i> Refresh
                        </button>
                        <button class="btn btn-success btn-sm" onclick="exportGlobalData()">
                            <i class="fa fa-file-excel-o"></i> Export to Excel
                        </button>
                    </div>
                </div>
            </div>

            
        
        <script>
            // Store data for filtering
            window.allEmployees = ${JSON.stringify(employees)};
            window.allActivities = ${JSON.stringify(all_activities)};
            window.allProjects = ${JSON.stringify(all_projects)};
            
            // Global filter function
            window.filterEmployeeTable = function() {
                let searchTerm = document.getElementById('searchEmployee').value.toLowerCase();
                let department = document.getElementById('deptFilter').value;
                let status = document.getElementById('statusFilter').value;
                let activity = document.getElementById('activityFilter').value;
                
                let rows = document.querySelectorAll('#employeeTableBody tr');
                rows.forEach(row => {
                    let employeeName = row.getAttribute('data-name') || '';
                    let employeeDept = row.getAttribute('data-dept') || '';
                    let employeeTotal = parseFloat(row.getAttribute('data-total')) || 0;
                    let employeeStatus = employeeTotal === 100 ? 'complete' : (employeeTotal < 100 ? 'incomplete' : 'over');
                    
                    let matchesSearch = employeeName.toLowerCase().includes(searchTerm);
                    let matchesDept = !department || employeeDept === department;
                    let matchesStatus = status === 'all' || employeeStatus === status;
                    
                    // Activity filtering - hide rows that don't have the selected activity
                    let matchesActivity = true;
                    if (activity !== 'all') {
                        let hasActivity = row.getAttribute('data-activities') || '';
                        matchesActivity = hasActivity.includes(activity);
                    }
                    
                    row.style.display = (matchesSearch && matchesDept && matchesStatus && matchesActivity) ? '' : 'none';
                });
            };
            
            window.refreshGlobalDashboard = function() {
                location.reload();
            };
            
            window.exportGlobalData = function() {
                let csv = [];
                let headers = ['Employee', 'Department', 'Period', ${generate_csv_headers(all_activities, all_projects)} 'Total%', 'Status'];
                csv.push(headers.join(','));
                
                document.querySelectorAll('#employeeTableBody tr').forEach(row => {
                    if (row.style.display !== 'none') {
                        let cells = row.querySelectorAll('td');
                        let rowData = [];
                        cells.forEach(cell => {
                            let text = cell.innerText.trim().replace(/,/g, ';');
                            rowData.push('"' + text + '"');
                        });
                        csv.push(rowData.join(','));
                    }
                });
                
                let blob = new Blob([csv.join('\\n')], {type: 'text/csv'});
                let link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'employee_allocations_global.csv';
                link.click();
                frappe.show_alert({message: 'Data exported!', indicator: 'green'}, 3);
            };
            
            // Render charts after table is loaded
            setTimeout(() => {
                renderDynamicCharts();
            }, 500);
            
            function renderDynamicCharts() {
                let projectData = ${JSON.stringify(get_dynamic_project_totals(employees, all_projects, all_activities))};
                
                let barCanvas = document.getElementById('globalBarChart');
                if (barCanvas && typeof frappe.Chart !== 'undefined') {
                    let datasets = [];
                    all_activities.forEach(activity => {
                        datasets.push({
                            name: activity,
                            values: projectData[activity] || []
                        });
                    });
                    
                    new frappe.Chart(barCanvas, {
                        title: "Project Allocation Distribution",
                        data: {
                            labels: ${JSON.stringify(all_projects)},
                            datasets: datasets
                        },
                        type: 'bar',
                        height: 300,
                        colors: ['#3498db', '#e67e22', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f']
                    });
                }
                
                let pieCanvas = document.getElementById('globalPieChart');
                if (pieCanvas && typeof frappe.Chart !== 'undefined') {
                    let activityTotals = {};
                    all_activities.forEach(activity => { activityTotals[activity] = 0; });
                    
                    employees.forEach(emp => {
                        emp.allocations.forEach(alloc => {
                            if (activityTotals[alloc.activity] !== undefined) {
                                activityTotals[alloc.activity] += alloc.percentage;
                            }
                        });
                    });
                    
                    new frappe.Chart(pieCanvas, {
                        title: "Activity Distribution (All Employees)",
                        data: {
                            labels: all_activities,
                            datasets: [{
                                name: "Total %",
                                values: all_activities.map(activity => activityTotals[activity])
                            }]
                        },
                        type: 'pie',
                        height: 300,
                        colors: ['#3498db', '#e67e22', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f']
                    });
                }
            }
        </script>
    `;
    charts_html = `
        <!-- Charts Section -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 25px;">
                <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h5 style="margin-bottom: 15px;">📊 Allocation by Project</h5>
                    <canvas id="globalBarChart" style="height: 300px;"></canvas>
                </div>
                <div style="background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h5 style="margin-bottom: 15px;">🥧 Activity Distribution (All Employees)</h5>
                    <canvas id="globalPieChart" style="height: 300px;"></canvas>
                </div>
            </div>
        </div>
        `;
    wrapper.html(dashboard_html);
}

// ============ Summary Card Generators ============

function generate_activity_summary_cards(all_activities, total_activity_hours) {
    let cards = '';
    let colors = ['#3498db', '#e67e22', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f'];
    let colorIndex = 0;
    
    all_activities.forEach(activity => {
        let color = colors[colorIndex % colors.length];
        let icon = activity === 'Operation' ? '🛠️' : (activity === 'Installation' ? '🔧' : '📋');
        cards += `
            <div style="background: white; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: ${color}; font-size: 32px;">${total_activity_hours[activity]}%</h3>
                <div style="color: #666;">${icon} Total ${activity}</div>
            </div>
        `;
        colorIndex++;
    });
    
    return cards;
}

function generate_activity_filter_options(all_activities) {
    let options = '';
    all_activities.forEach(activity => {
        let icon = activity === 'Operation' ? '🛠️' : (activity === 'Installation' ? '🔧' : '📋');
        options += `<option value="${activity}">${icon} ${activity}</option>`;
    });
    return options;
}

// ============ Dynamic Header Generators ============

function generate_activity_headers(all_activities, all_projects) {
    let headers = '';
    let colors = ['#3498db', '#e67e22', '#2ecc71', '#e74c3c', '#9b59b6', '#f1c40f'];
    let colorIndex = 0;
    
    all_activities.forEach(activity => {
        let color = colors[colorIndex % colors.length];
        let icon = activity === 'Operation' ? '🛠️' : (activity === 'Installation' ? '🔧' : '📋');
        headers += `<th colspan="${all_projects.length}" style="padding: 12px; text-align: center; background: ${color};">
                        ${icon} ${activity}
                    </th>`;
        colorIndex++;
    });
    return headers;
}

function generate_project_subheaders(all_activities, all_projects) {
    let subheaders = '';
    all_activities.forEach(() => {
        all_projects.forEach(project => {
            console.log(all_activities, all_projects);
            
            // Shorten project name for display
            let shortName = project?.length > 15 ? project.substring(0, 12) + '...' : project;
            subheaders += `<th style="padding: 8px; text-align: center; font-size: 11px;">${shortName}</th>`;
        });
    });
    return subheaders;
}

function generate_csv_headers(all_activities, all_projects) {
    let headers = [];
    all_activities.forEach(activity => {
        all_projects.forEach(project => {
            headers.push(`"${activity}-${project}"`);
        });
    });
    return headers.join(',') + ',';
}

// ============ Dynamic Row Generators ============

function generate_dynamic_employee_rows(employees, all_activities, all_projects) {
    let rows = '';
    
    employees.forEach(emp => {
        // Build dynamic allocation map from child table data
        let allocation_map = {};
        let employee_activities = new Set(); // Track activities for this employee
        
        // Initialize map with zeros
        all_activities.forEach(activity => {
            allocation_map[activity] = {};
            all_projects.forEach(project => {
                allocation_map[activity][project] = 0;
            });
        });
        
        // Fill map from actual allocations
        emp.allocations.forEach(alloc => {
            if (allocation_map[alloc.activity] && allocation_map[alloc.activity][alloc.project] !== undefined) {
                allocation_map[alloc.activity][alloc.project] = alloc.percentage;
                employee_activities.add(alloc.activity);
            }
        });
        
        let status_color = emp.total_percentage === 100 ? '#27ae60' : (emp.total_percentage < 100 ? '#f39c12' : '#c0392b');
        let status_text = emp.total_percentage === 100 ? '✓ Complete' : (emp.total_percentage < 100 ? `⚠️ ${emp.total_percentage}%` : `❌ Over`);
        let period = `${emp.from_date || 'N/A'} to ${emp.to_date || 'N/A'}`;
        
        rows += `
            <tr data-name="${emp.employee_name}" 
                data-dept="${emp.department}" 
                data-total="${emp.total_percentage}"
                data-activities="${Array.from(employee_activities).join(',')}"
                style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; font-weight: bold; background: #f8f9fa;">
                    ${emp.employee_name}
                    <div style="font-size: 11px; color: #666;">${emp.designation}</div>
                </td>
                ${generate_dynamic_allocation_cells(allocation_map, all_activities, all_projects)}
                <td style="padding: 10px; text-align: center; font-weight: bold; background: #e8f4f8;">
                    ${emp.total_percentage}%
                    <div style="height: 3px; background: #e9ecef; margin-top: 5px; border-radius: 2px;">
                        <div style="height: 100%; width: ${Math.min(emp.total_percentage, 100)}%; background: ${status_color}; border-radius: 2px;"></div>
                    </div>
                </td>
                <td style="padding: 10px; text-align: center;">
                    <span style="background: ${status_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">
                        ${status_text}
                    </span>
                </td>
            </tr>
        `;
    });
    
    return rows;
}

function generate_dynamic_allocation_cells(allocation_map, all_activities, all_projects) {
    let cells = '';
    all_activities.forEach(activity => {
        all_projects.forEach(project => {
            let percentage = allocation_map[activity][project] || 0;
            cells += `<td style="padding: 10px; text-align: center;">${render_percentage_dynamic(percentage, activity, project)}</td>`;
        });
    });
    return cells;
}

function render_percentage_dynamic(value, activity, project) {
    if (value === 0) return '<span style="color: #bdc3c7;">—</span>';
    
    let color = value >= 40 ? '#fee2e2' : (value >= 20 ? '#fff3cd' : '#d4edda');
    let text_color = value >= 40 ? '#c0392b' : (value >= 20 ? '#856404' : '#155724');
    
    return `
        <div style="background: ${color}; padding: 5px; border-radius: 5px; cursor: pointer;" 
             onclick="frappe.msgprint({
                 title: 'Allocation Details', 
                 message: '<strong>Activity:</strong> ${activity}<br><strong>Project:</strong> ${project}<br><strong>Allocation:</strong> ${value}%<br><strong>Monthly Hours:</strong> ${(value/100*160).toFixed(1)}h'
             })">
            <strong style="color: ${text_color};">${value}%</strong>
            <div style="height: 3px; background: #e9ecef; margin-top: 5px; border-radius: 2px; overflow: hidden;">
                <div style="height: 100%; width: ${Math.min(value, 100)}%; background: ${text_color};"></div>
            </div>
        </div>
    `;
}

// ============ Dynamic Footer Generator ============

function generate_dynamic_table_footer(employees, all_activities, all_projects) {
    // Initialize totals map
    let totals = {};
    all_activities.forEach(activity => {
        totals[activity] = {};
        all_projects.forEach(project => {
            totals[activity][project] = 0;
        });
    });
    
    // Calculate totals from all employees
    employees.forEach(emp => {
        emp.allocations.forEach(alloc => {
            if (totals[alloc.activity] && totals[alloc.activity][alloc.project] !== undefined) {
                totals[alloc.activity][alloc.project] += alloc.percentage;
            }
        });
    });
    
    // Calculate overall totals
    let all_totals = [];
    let grand_total = 0;
    all_activities.forEach(activity => {
        all_projects.forEach(project => {
            let val = totals[activity][project];
            all_totals.push(val);
            grand_total += val;
        });
    });
    
    let total_employees = employees.length;
    let avg_per_employee = total_employees > 0 ? (grand_total / total_employees).toFixed(1) : 0;
    
    let footer_cells = '';
    all_totals.forEach(total => {
        footer_cells += `<td style="padding: 10px; text-align: center;"><strong>${total}%</strong></td>`;
    });
    
    return `
        <tr style="background: #2c3e50; color: white;">
            <td colspan="1" style="padding: 10px; text-align: center;"><strong>📊 TOTALS</strong></td>
            ${footer_cells}
            <td style="padding: 10px; text-align: center;"><strong>${grand_total}%</strong></td>
            <td style="padding: 10px; text-align: center;"><strong>Avg: ${avg_per_employee}%</strong></td>
        </tr>
    `;
}

// ============ Dynamic Chart Helpers ============

function get_dynamic_project_totals(employees, all_projects, all_activities) {
    let result = {};
    console.log(employees,all_activities,all_projects);
    
    all_activities.forEach(activity => {
        result[activity] = [];
        all_projects.forEach(project => {
            let total = 0;
            employees.forEach(emp => {
                emp.allocations.forEach(alloc => {
                    if (alloc.activity === activity && alloc.project === project) {
                        total += alloc.percentage;
                    }
                });
            });
            result[activity].push(total);
        });
    });
    return result;
}

function get_unique_departments(employees) {
    let depts = [...new Set(employees.map(emp => emp.department).filter(dept => dept && dept !== 'N/A'))];
    return depts.map(dept => `<option value="${dept}">${dept}</option>`).join('');
}