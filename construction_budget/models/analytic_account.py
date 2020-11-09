# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.depends('account_id')
    def _get_project_value(self):
        for i in self:
            project = i.env['project.project'].search([('analytic_account_id', '=', i.account_id.id)], limit=1)
            if project[:1]:
                i.project_id = project.id

    @api.depends('amount')
    def _get_analytic_type(self):
        for i in self:
            i.abs_amount = abs(i.amount)
            if i.amount <= 0.0:
                i.analytic_type = 'Expense'
            else:
                i.analytic_type = 'Income'

    @api.depends('project_id', 'project_id.project_type')
    def _get_project_type(self):
        for i in self:
            if i.project_id:
                i.project_type = i.project_id.project_type

    project_type = fields.Selection([('project', 'Project'),
                                     ('portfolio', 'Portfolio')], string="Project Type", store=True, compute="_get_project_type")
    analytic_type = fields.Selection([('Income', 'Income'), ('Expense', 'Expense')], string="Type", store=True, compute='_get_analytic_type')
    abs_amount = fields.Monetary(string="Absolute Amount", store=True, compute='_get_analytic_type')
    project_id = fields.Many2one('project.project', store=True, compute='_get_project_value')
    phase_id = fields.Many2one('project.phase', string="Phase")
    task_id = fields.Many2one('project.task', string="Task")
    project_boq_category = fields.Selection([
                                        ('meterial', 'Material'),
                                        ('subcon', 'Subcontractor'),
                                        ('labor', 'Human Resource/Labor'),
                                        ('equipment', 'Equipment'),
                                        ('overhead', 'Overhead'),
                                        ('other', 'Other')], string="Category")

    @api.onchange("project_id", "phase_id")
    def _onchange_project(self):
        vals = {}
        if self.project_id.project_type == 'project' and self.phase_id:
            vals['domain'] = {
                "task_id": [("phase_id", "=", self.phase_id.id)],
            }
        elif self.project_id.project_type == 'portfolio':
            vals['domain'] = {
                "task_id": [("project_id", "=", self.project_id.id)],
            }
        return vals
