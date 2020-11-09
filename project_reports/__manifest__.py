# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Project Reports",
    'summary': """Bridge module for project and enterprise""",
    'description': """
Bridge module for project and enterprise
    """,
    'category': 'Operations/Project',
    'version': '1.0',
    'depends': ['project', 'map_view', 'web_gantt_view'],
    'data': [
        'report/project_report_views.xml',
        'views/res_config_settings_views.xml',
        'views/project_task_views.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/task_gantt.xml',
    ],
    "installable": True,
    'auto_install': False,
    'application': True,
}
