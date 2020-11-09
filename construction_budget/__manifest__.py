# -*- coding: utf-8 -*-


{
    'author':  'Dennis Boy Silva - (Agilis Enterprise Solutions Inc.)',
    'website': 'agilis.com.ph',
    'license': 'AGPL-3',
    'category': 'custom project',
    'depends': [
            'account',
            'analytic',
            'project',
            'stock',
            'hr',
            'web_fontawesome',
            'construction_project_management_base',
            'grid_view'
        ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/supplement_contract_amount.xml',
        'views/project_task.xml',
        'views/project_phase.xml',
        'views/project.xml',
        'views/analytic_account.xml',
        ],
    'description': '''Construction Project Budget Management''',
    'installable': True,
    'auto_install': False,
    'application': True,

    'name': "Construction Budget",
    'summary': 'Construction Project Budget Management',
    'test': [],
    'version': '13.0.0'

}
