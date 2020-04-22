{
    'name': 'Google Task Calendar',
    'category': 'Calendar',
    'author': 'ITMusketeers Consultancy Services LLP',
    'description': """
================================================================================

1.Sync. google calendar with odoo project tasks
================================================================================
""",
    'depends': ['project','web', 'base','calendar','hr'],
    'summary': 'Sync. google calendar with odoo project tasks',

    'data': [
	    'security/ir.model.access.csv',
            'views/google_task_calendar.xml',
            ],

    'installable': True,
}
