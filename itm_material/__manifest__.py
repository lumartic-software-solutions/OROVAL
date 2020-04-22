# -*- coding: utf-8 -*-
# Odoo, Open Source Itm  Material Theme.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).# 
{
    "name": "Itm Material Theme",
    "summary": "Odoo 10.0 community backend theme",
    "version": "10.0.1.0.23",
    "category": "Themes/Backend",
    "author": 'ITMusketeers Consultancy Services LLP',
    "description": """
================================================================================

1.Generate Dynamic Itm Material Theme Color.

================================================================================
""",
    'depends': ['base', 'web'],
    'data': [
        'views/res_company_view.xml',
        'views/assets.xml',
        'views/web.xml',
        'views/users.xml',
        'views/sidebar.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
    'web_preload': True,
    'currency': 'EUR',
}
