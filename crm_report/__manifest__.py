# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "CRM Report",
    'version': "1.0",
    'category': "Sales/CRM",
    'summary': "Advanced features for CRM",
    'description': """
Contains advanced features for CRM such as new views
    """,
    'depends': ['crm', 'dash_view', 'cohort_view', 'map_view'],
    'data': [
        'views/crm_lead_views.xml',
        'report/crm_activity_report_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True
}
