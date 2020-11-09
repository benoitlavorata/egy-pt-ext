# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (https://akretion.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Purchase Order Line menu",
    "summary": "Adds a menu to see purchase order lines",
    "version": "11",
    "author": "Akretion and Dennis Boy Silva -Agilis Enterprise Solutions, Inc.",
    "website": "https://github.com/akretion/odoo-usability",
    "category": "custom project",
    "depends": ["purchase"],
    "data": [
        'views/purchase_order_line.xml',
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": True,
}
