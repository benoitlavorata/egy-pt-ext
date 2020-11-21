# -*- coding: utf-8 -*-

{
    'name': 'Account Payment Voucher',
    'category': 'Account',
    'author': 'ITMusketeers Consultancy Services LLP',
    'website': 'www.itmusketeers.com',
    'description': """
================================================================================

1. Account Payment Management.

================================================================================
""",
    'depends': ['base', 'web', 'account', 'payment'],
    'summary': 'Manage internal transfer For Payment.',
    'data': [
        'views/account_payment_view.xml',
        'views/payment_voucher_view.xml'],
    'images': ['static/description/Banner.png'],
    'installable': True,
}
