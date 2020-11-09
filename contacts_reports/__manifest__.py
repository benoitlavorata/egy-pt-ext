# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Contacts Reports',
    'summary': 'Enterprise features on contacts',
    'description': 'Adds notably the map view of contact',
    'version': '1.0',
    'depends': [
        'contacts',
        'map_view'
    ],
    'data': [
        "views/contact_views.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
