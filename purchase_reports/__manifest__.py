# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Purchase reports",
    'version': "1.0",
    'category': "Operations/Purchase",
    'summary': "Advanced Features for Purchase Management",
    'description': """
Contains advanced features for purchase management
    """,
    'depends': ['purchase', 'dash_view'],
    'data': [
        'report/purchase_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
