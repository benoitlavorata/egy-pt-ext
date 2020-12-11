# -*- coding: utf-8 -*-
{
    'name': "construction",

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
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale',
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

    # always loaded
    'data': [
        'security/construction_security.xml',
        'security/ir.model.access.csv',
        'data/jobcost_sequence.xml',
        'views/assets.xml',
        'wizard/project_user_subtask_view.xml',
        #             'wizard/purchase_order_view.xml',
        'wizard/job_costing_invoice_wiz.xml',
        'views/job_costing_view.xml',
        'views/project.xml',
        'views/job_type.xml',
        'views/job_cost_to_lines.xml',
        'views/construction_management_view.xml',
        'views/note_view.xml',
        'views/product_view.xml',
        'report/project_report.xml',
        'views/project_task_view.xml',
        'views/project_view_construct.xml',
        'views/purchase_view.xml',
        'report/report_noteview.xml',
        'report/report_reg.xml',
        'views/stock_picking.xml',
        'report/task_report.xml',
        'views/order_lines_view.xml',
        'report/job_costing_report.xml',
        'views/purchase_requisition_view.xml',
        'report/purchase_requisition_report.xml',
        'views/account_analytic_view.xml',
        'views/account_invoice_view.xml',
        'views/estimated_sheet.xml',
        'views/project_boq.xml',
        'views/crm_view.xml',
        'wizard/whatsapp_wizard.xml',
        'views/menu.xml'
    ],
}
