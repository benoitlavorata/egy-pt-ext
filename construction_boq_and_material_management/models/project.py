# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
from datetime import datetime


class Project(models.Model):
    _inherit = "project.project"
    _description = "Project Inherited"

    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
 
    def _kanban_dashboard_line_graph(self):
        self.kanban_dashboard_line_graph = json.dumps(self.get_line_graph_datas())

    # START Added SKIT
    boq_count = fields.Integer(compute='_compute_boq_count', string="BOQ")
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    kanban_dashboard_line_graph = fields.Text(compute='_kanban_dashboard_line_graph')

    def get_bar_graph_datas(self):
 
        datas = [{"value": self.material_budget, "labels":["1.Material","Budget"]},
                 {"value": self.material_expense, "labels":["1.Material","Actual Expense"]},
                 {"value": self.service_budget, "labels":["2.Subcontract...","Budget"]},
                 {"value": self.service_expense, "labels":["2.Subcontract...","Actual Expense"]},
                 {"value": self.labor_budget, "labels":["3.Labor","Budget"]},
                 {"value": self.labor_expense, "labels":["3.Labor","Actual Expense"]},
                 {"value": self.equipment_budget, "labels":["4.Equipm...","Budget"]},
                 {"value": self.equipment_expense, "labels":["4.Equipm...","Actual Expense"]},
                 {"value": self.overhead_budget, "labels":["5.Overhea...","Budget"]},
                 {"value": self.overhead_expense, "labels":["5.Overhea...","Actual Expense"]}]
        return [{'values': datas, 'id': self.id}]

    def get_line_graph_datas(self):
        datas = []
        for project in self.projection_accomplishment_ids:
            if project.date:
                pdate = datetime.strptime(project.date, '%Y-%m-%d')
                project_date = pdate.strftime("%Y-%m-%d")
            else:
                project_date = ""
            datas.append({"value": ((project.projected) / 100), "labels": [project_date,"Projected Accomplishment"]})
            datas.append({"value": ((project.actual) / 100), "labels": [project_date,"Actual Accomplishment"]})

        return [{'values': datas, 'id': self.id}]

    def _compute_boq_count(self):
        boq_data = self.env['project.boq'].read_group([
            ('project_id', 'in', self.ids)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in boq_data)
        for project in self:
            project.update({'boq_count': result.get(project.id, 0)})
    # END
