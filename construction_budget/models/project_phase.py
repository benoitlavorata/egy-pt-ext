
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProjectPhase(models.Model):
    _inherit = 'project.phase'

    @api.depends('task_ids', 'task_ids.task_budget', 'phase_budget_amount')
    def _get_budget_computation(self):
        for i in self:
            allocated = sum(line.task_budget for line in i.task_ids)
            reserve = i.phase_budget_amount - allocated
            i.phase_budget_allocated = allocated
            i.phase_budget_reserve = reserve

    def _get_project_expense(self):
        for i in self:
            analytic_account = [i.project_id.analytic_account_id.id]
            # if i.project_id.analytic_account_id.group_id:
            #     analytic_group = i.env['account.analytic.group'].search([('id', 'child_of', i.project_id.analytic_account_id.group_id.id)]).ids
            #     analytic_account = i.env['account.analytic.account'].search([('group_id', 'in', analytic_group)]).ids
            i.phase_actual_expense = abs(sum(line.amount for line in i.env['account.analytic.line'].
                                             search([('account_id', 'in', analytic_account),
                                                     ('amount', '<=', 0.0), ('phase_id', '=', i.id)])))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id',
                                  string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    phase_budget_amount = fields.Monetary(string="Budget Amount")
    phase_budget_allocated = fields.Monetary(string="Budget Allocated", store=True,
                                             compute='_get_budget_computation')
    phase_budget_reserve = fields.Monetary(stirng="Budget Reserve", store=True,
                                           compute='_get_budget_computation')
    phase_actual_expense = fields.Monetary(string="Actual Expense",
                                           compute='_get_project_expense')
