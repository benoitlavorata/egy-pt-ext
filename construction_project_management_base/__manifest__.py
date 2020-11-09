{
    'name': "Construction Project Management",
    'summary': 'Construction Project Management Base module',
    'test': [],
    'version': '13.0.0',
    'description': '''Construction Project Management''',
    'author':  'Dennis Boy Silva - (Agilis Enterprise Solutions Inc.)',
    'website': 'agilis.com.ph',
    'license': 'AGPL-3',
    'category': 'custom project',
    'data': [
            'security/ir.model.access.csv',
            'wizard/set_projection.xml',
            'wizard/portfolio_report.xml',
            'views/project_task.xml',
            'views/project_phase.xml',
            'views/project.xml',
        ],
    'depends': [
            'project',
            'stock',
            'report_xlsx'
        ],
    'installable': True,
    'auto_install': False,
    'application': True

}
