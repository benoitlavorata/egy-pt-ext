# -*- coding: utf-8 -*-
{
    'name': "map_view",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Branding',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': ['web', 'base_setup'],

    'data': [
        "views/assets.xml",
        "views/res_config_settings.xml",
        "views/res_partner.xml",
    ],
    'qweb': [
        "static/xml/templates.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
