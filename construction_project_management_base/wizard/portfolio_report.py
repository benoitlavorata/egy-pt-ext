# -*- coding: utf-8 -*-
'''
Created on 08 of January 2020
@author: Dennis
'''

from odoo import api, fields, models, tools, SUPERUSER_ID, _


class ProjectPortfolioReport(models.TransientModel):
    _name = 'project.portfolio.report'

    project_id = fields.Many2one('project.project', string="Portfolio", domain="['project_type', '=', 'portfolio']",
                                 required=True)
    include_budget_status = fields.Boolean(string="Include Budget Status", default=True)
    include_project_status = fields.Boolean(string="Include Project Status", default=True)
    include_timeline_status = fields.Boolean(string="Include Timeline Status", default=True)

    def generate_report(self):
        return self.env.ref('construction_project_management_base.portfolio_report_xlsx').report_action(self)
