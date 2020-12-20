# -*- coding: utf-8 -*-
{
    'name': "construction",

    'summary': """
        Construction Management""",

    'description': """
        Construction Management Build By Raqmi
    """,

    'author': "Raqmi",
    'website': "http://www.raqmisoultions.com",

    'category': 'Construction',
    'version': '0.1',

    'depends': ['dash_view', 'map_view', 'sale',
                'project',
                'hr_timesheet',
                'purchase',
                'note',
                'stock',
                'stock_account',
                'material_purchase_requisitions',
                'account',
                'analytic',
                'account_asset',
                'stock',
                'crm'],

    'data': [
        'security/construction_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/task_sequence.xml',
        'views/assets.xml',
        'wizard/project_user_subtask_view.xml',
        'wizard/task_costing_invoice_wiz.xml',
        'views/task_cost_view.xml',
        'views/project.xml',
        'views/construction_management_view.xml',
        'views/note_view.xml',
        'views/project_task_view.xml',
        'views/project_view_construct.xml',
        'views/purchase_view.xml',
        'report/report_note_view.xml',
        'views/accounting_view.xml',
        'views/estimated_sheet.xml',
        'views/project_boq.xml',
        'views/crm_view.xml',
        'wizard/whatsapp_wizard.xml',
        'views/menu.xml'
    ],
}
