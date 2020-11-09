# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Stock reports",
    'version': "2.0",
    'category': 'Operations/Inventory',
    'summary': "Advanced features for Stock",
    'description': """
Contains the enterprise views for Stock management
    """,
    'depends': ['stock', 'dash_view', 'cohort_view', 'map_view', 'grid_view'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_views.xml',
        'views/stock_picking_map_views.xml',
        'views/stock_reports_templates.xml',
        'report/stock_report_views.xml',
        'report/report_stock_quantity.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
