# -*- coding: utf-8 -*-
{
    'name': "dash_view",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Branding',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/dashboard.xml'],
    'installable': True,
    'auto_install': False,
    'application': True
}
