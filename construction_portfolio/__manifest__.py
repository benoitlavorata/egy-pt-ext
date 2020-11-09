# -*- coding: utf-8 -*-

{
    'name': "Construction Portfolio",
    'summary': 'Construction Project Portfolio Management',
    'description': '''Construction Project Portfolio Management''',
    'test': [],
    'version': '13.0.0',
    'author':  'Dennis Boy Silva - (Agilis Enterprise Solutions Inc.)',
    'website': 'agilis.com.ph',
    'license': 'AGPL-3',
    'category': 'custom project',
    'depends': [
            'project',
            'construction_project_management_base',
            'project_description',
        ],
    'data': [
            'views/project.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True
}
