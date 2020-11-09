# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'enterprise theme',
    'category': 'Branding',
    'version': '2.0',
    'description':
        """
Enterprise theme
        """,
    'depends': ['base_setup', 'web'],
    'data': [
        'views/webclient_templates.xml',
        'views/res_config.xml',
    ],
    'demo': [
        'data/demo.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
