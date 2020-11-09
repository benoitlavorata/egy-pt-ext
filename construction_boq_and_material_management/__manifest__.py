# -*- coding: utf-8 -*-

{
    'author':  'Srikesh Infotech',
    'website': 'www.srikeshinfotech.com',
    'license': 'AGPL-3',
    'version': '13.0.0',
    'category': 'custom project',
    'name': "Construction BOQ and Material Management",
    'summary': 'Construction Project Management customized module',
    'description': '''
        Construction Project Management''',
    'depends': [
            'project',
            'construction_project_management_base',
            'hr'
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_boq.xml',
        'views/project.xml',
        'wizard/project_wizard.xml',
        'views/project_task.xml',
        'views/task.xml',
        'views/material_req.xml',
        'views/project_eco.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
