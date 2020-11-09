
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.depends('account_analytic_line_ids', 'account_analytic_line_ids.project_id', 'account_analytic_line_ids.phase_id', 'account_analytic_line_ids.task_id', 'account_analytic_line_ids.amount', 'account_analytic_line_ids.project_boq_category',
                 'material_budget', 'service_budget', 'labor_budget', 'equipment_budget', 'overhead_budget', 'total_budget')
    def _compute_budget_expense(self):
        for i in self:
            material_expense = 0.0
            service_expense = 0.0
            labor_expense = 0.0
            equipment_expense = 0.0
            overhead_expense = 0.0
            for line in i.account_analytic_line_ids:
                if line.project_boq_category in ['meterial'] and line.amount <= 0.0:
                    material_expense += abs(line.amount)
                elif line.project_boq_category in ['subcon'] and line.amount <= 0.0:
                    service_expense += abs(line.amount)
                elif line.project_boq_category in ['equipment'] and line.amount <= 0.0:
                    equipment_expense += abs(line.amount)
                elif line.project_boq_category in ['labor'] and line.amount <= 0.0:
                    labor_expense += abs(line.amount)
                elif line.project_boq_category in ['overhead'] and line.amount <= 0.0:
                    overhead_expense += abs(line.amount)
            i.material_expense = material_expense
            i.service_expense = service_expense
            i.labor_expense = labor_expense
            i.equipment_expense = equipment_expense
            i.overhead_expense = overhead_expense
            i.material_balance = i.material_budget - material_expense
            i.service_balance = i.service_budget - service_expense
            i.labor_balance = i.labor_budget - labor_expense
            i.equipment_balance = i.equipment_budget - equipment_expense
            i.overhead_balance = i.overhead_budget - overhead_expense
            i.total_expense = sum([material_expense, service_expense, labor_expense, equipment_expense, overhead_expense])
            i.total_balance = sum([i.material_balance, i.labor_balance, i.service_balance, i.equipment_balance, i.overhead_balance])

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")
    account_analytic_line_ids = fields.One2many('account.analytic.line', 'task_id', string="Expenses")
    # Budget And Actual Expeditures
    material_expense = fields.Monetary(string="Material Expense", store=True, compute='_compute_budget_expense')
    material_balance = fields.Monetary(string="Material Balance", store=True, compute='_compute_budget_expense')
    service_expense = fields.Monetary(string="Service Expense", store=True, compute='_compute_budget_expense')
    service_balance = fields.Monetary(string="Service Balance", store=True, compute='_compute_budget_expense')
    labor_expense = fields.Monetary(string="Labor Expense", store=True, compute='_compute_budget_expense')
    labor_balance = fields.Monetary(string="Labor Balance", store=True, compute='_compute_budget_expense')
    equipment_expense = fields.Monetary(string="Equipment Expense", store=True, compute='_compute_budget_expense')
    equipment_balance = fields.Monetary(string="Equipment Balance", store=True, compute='_compute_budget_expense')
    overhead_expense = fields.Monetary(string="Overhead Expense", store=True, compute='_compute_budget_expense')
    overhead_balance = fields.Monetary(string="Overhead balance", store=True, compute='_compute_budget_expense')
    total_expense = fields.Monetary(string="Total Expense", store=True, compute='_compute_budget_expense')
    total_balance = fields.Monetary(string="Total Balance", store=True, compute='_compute_budget_expense')
