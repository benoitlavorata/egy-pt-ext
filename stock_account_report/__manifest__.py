# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Stock account reports",
    'version': "1.0",
    'category': 'Operations/Inventory',
    'summary': "Advanced features for stock_account",
    'description': """
Contains the enterprise views for Stock account
    """,
    'depends': ['stock_account', 'stock_reports', 'dash_view'],
    'data': [
        'report/stock_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
