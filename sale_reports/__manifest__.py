# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Sale reports",
    'version': "1.0",
    'category': "Sales/Sales",
    'summary': "Advanced Features for Sale Management",
    'description': """
Contains advanced features for sale management
    """,
    'depends': ['sale', 'dash_view'],
    'data': [
        'report/sale_report_views.xml',
        'views/sale_reports_templates.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
