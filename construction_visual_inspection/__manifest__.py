# -*- coding: utf-8 -*-

{
    'name': "Construction Visual Management",
    'version': '13.0.0',
    'license': 'AGPL-3',
    'author':  'Srikesh Infotech',
    'website': 'www.srikeshinfotech.com',
    'category': 'custom project',
    'description': '''Visual Inspection module''',
    'summary': 'Visual Inspection Management',
    'data': [
        'security/ir.model.access.csv',
        'views/visual_inspection.xml',
        ],
    'depends': [
            'project',
            'stock',
        ],
    'installable': True,
    'auto_install': False,
    'application': True
}
