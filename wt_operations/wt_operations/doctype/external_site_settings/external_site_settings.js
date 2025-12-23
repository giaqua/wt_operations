frappe.ui.form.on('External Site Settings', {
	test_connection: function(frm) {
		// Validate required fields before testing
		if (!frm.doc.site_url) {
			frappe.msgprint(__('Please enter Site URL'));
			return;
		}
		if (!frm.doc.api_key) {
			frappe.msgprint(__('Please enter API Key'));
			return;
		}
		if (!frm.doc.api_secret) {
			frappe.msgprint(__('Please enter API Secret'));
			return;
		}
		
		frappe.call({
			method: 'test_connection',
			doc: frm.doc,
			freeze: true,
			freeze_message: __('Testing connection...'),
			callback: function(r) {
				if (r.message) {
					frm.refresh_field('connection_status');
					if (r.message.status === 'success') {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						}, 5);
					} else {
						// Show detailed error message
						let error_msg = r.message.message;
						if (r.message.error_detail) {
							error_msg += '\n' + __('Details: {0}', [r.message.error_detail]);
						}
						if (r.message.status_code === 401) {
							frappe.msgprint({
								title: __('Authentication Failed'),
								message: error_msg,
								indicator: 'red'
							});
						} else {
							frappe.show_alert({
								message: error_msg,
								indicator: 'red'
							}, 8);
						}
					}
				}
			},
			error: function(r) {
				frappe.show_alert({
					message: __('Error testing connection: {0}', [r.message || 'Unknown error']),
					indicator: 'red'
				}, 8);
			}
		});
	}
});
