# -*- coding: utf-8 -*-

{
    'name': 'Petty Cash Management',
    'category': 'Account',
    'author': 'ITMusketeers Consultancy Services LLP',
    'website': 'www.itmusketeers.com',
    'description': """
================================================================================

1. Petty Cash Management .

================================================================================
""",
    'depends': ['itm_payment', 'itm_payment_analytic', 'hr', 'base', 'web', 'analytic', 'account'],
    'summary': 'Manage Petty Cash Funds',
    'data': [
        'security/ir.model.access.csv',
        'security/petty_cash_access.xml',
        'data/memo_sequence.xml',
        'report/petty_cash_report_template.xml',
        'views/petty_cash_view.xml',
        'views/employee_view.xml',
        'report/custom_report.xml',
        ],
    'images': ['static/description/Banner.png'],
    'installable': True,

}
