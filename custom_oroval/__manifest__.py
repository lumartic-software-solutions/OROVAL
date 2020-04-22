{
    'name': ' custom oroval',
    'category': 'Sale',
    'author': 'ITMusketeers Consultancy Services LLP',
    'description': """
================================================================================

1.Opportunity Name to Customer Reference.
2.Changes in U.O.M.
3.Display of quotes, sales orders and invoices.
4.Design of quotation, orders of sale and invoices.
================================================================================
""",
    'depends': ['mail','google_task_calendar','calendar','crm_phonecall','hr_timesheet','hr_attendance','web_kanban','project', 'contacts','sales_team', 'product', 'web', 'base', 'sale', 'crm', 'report', 'sale_timesheet', 'sale_crm', 'account', 'account_accountant','web_readonly_bypass','kanban_draggable'],
    'summary': 'To Generate custom oroval',

    'data': [
		'security/ir.model.access.csv',
		'security/oroval_access.xml',
		'wizard/custom_wizard.xml',
		'wizard/login_popup.xml',
		'wizard/create_project_invoice_wizard.xml',
		'views/custom_task_view.xml',
        'views/custom_oroval_view.xml',
	'views/sale_report_template.xml',
        'views/custom_header_layout.xml',
        'views/all_search_view.xml',
	'views/invoice_template.xml',
	'custom_report.xml',
        'views/send_mail_template.xml',
        'views/assets.xml',
	#'views/custom_crm_view.xml',
        'views/res_company_view.xml',
        
		'views/project_view.xml',
        'views/crm_phonecall_view.xml',
        
             ],

    'installable': True,
}
