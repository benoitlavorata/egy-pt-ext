# -*- coding: utf-8 -*-

{
    'author':  'Srikesh Infotech',
    'website': 'www.srikeshinfotech.com',
    'license': 'AGPL-3',
    'version': '13.0.0',
    'category': 'custom project',
    'name': 'Project Report XLS',
    'depends': ['base', 'project', 'report_xlsx', 'construction_project_management_base',
                'construction_visual_inspection'],
    'license': 'AGPL-3',
    'summary': 'Project report in Excel',
    'description': '''
        Project report in Excel''',
    'data': [
             'wizard/project_report_wizard_view.xml',
             'views/project_report_template.xml',
             'views/project_report.xml'
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
