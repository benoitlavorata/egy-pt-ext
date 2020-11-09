# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectReport(models.TransientModel):
    _name = 'wizard.project.report'


    project_id = fields.Many2one('project.project', required=True,
                                 string="Project")
    asof_date = fields.Date(string="As of")


    def print_project_report_xls(self):
        active_record = self.id
        record = self.env['project.project'].browse(active_record)
        data = {
            'ids': self.ids,
            'model': self._name,
            'record': record.id,
        }
        return self.env.ref('project_report_xls.project_xlsx').report_action(self, data=data)
