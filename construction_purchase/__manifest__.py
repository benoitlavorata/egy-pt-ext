# -*- coding: utf-8 -*-

{
    'name': "Construction Purchase",
    'summary': 'Construction Project Purchase Management',
    'description': '''Construction Project Purchase Management''',
    'test': [],
    'version': '13.0.0',
    'author':  'Dennis Boy Silva - (Agilis Enterprise Solutions Inc.)',
    'website': 'agilis.com.ph',
    'license': 'AGPL-3',
    'category': 'custom project',
    'depends': [
            'account',
            'analytic',
            'project',
            'stock',
            'purchase_requisition',
            'construction_project_management_base',
            'construction_budget',
            'purchase_request',
            'purchase_order_line_menu',
            'construction_boq_and_material_management',
        ],
    'data': [
            'wizard/do_purchase_requisition.xml',
            'wizard/do_create_po.xml',
            'report/purchase_requisition_report.xml',
            'report/purchase_tender_report.xml',
            'report/purchase_order_report.xml',
            'report/material_issuance_slip.xml',
            'views/project.xml',
            'views/invoice.xml',
            'views/purchase.xml',
            'views/stock.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True

}
