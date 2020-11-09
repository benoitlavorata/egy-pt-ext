
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class SupplementContractAmount(models.TransientModel):
    _name = 'supplement.contract.amount'

    @api.depends('project_id', 'supplement_amount', 'phase_id', 'task_id', 'budget_adjustment', 'adjustment_category')
    def _get_amount(self):
        for i in self:
            if not i.budget_adjustment:
                i.prev_contract_amount = i.project_id.project_contract_amount
                i.new_amount = sum([i.project_id.project_contract_amount, i.supplement_amount])
            elif i.budget_adjustment and i.adjustment_category in ['project']:
                i.prev_contract_amount = i.project_id.project_budget_amount
                i.new_amount = sum([i.project_id.project_budget_amount, i.supplement_amount])
            elif i.budget_adjustment and i.adjustment_category in ['phase']:
                i.prev_contract_amount = i.phase_id.phase_budget_amount
                i.new_amount = sum([i.phase_id.phase_budget_amount, i.supplement_amount])
            elif i.budget_adjustment and i.adjustment_category in ['task']:
                i.prev_contract_amount = i.task_id.task_budget
                i.new_amount = sum([i.task_id.task_budget, i.supplement_amount])

    budget_adjustment = fields.Boolean(string="Budget Adjustment")
    project_type = fields.Selection([('project', 'Project'),
                                     ('portfolio', 'Portfolio')], string="Project Type", default='project')
    adjustment_category = fields.Selection([
                        ('project', 'Project'),
                        ('phase', 'Phase'),
                        ('task', 'Task')
                    ], string="Mode", default="project")
    phase_budget_adjustment = fields.Boolean(string="Task Budget Adjustment")
    task_budget_adjustment = fields.Boolean(string="Task Budget Adjustment")
    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id', string="Company Currency")
    project_id = fields.Many2one('project.project')
    phase_id = fields.Many2one('project.phase', string="Phase", domain="[('project_id', '=', project_id)]")
    task_id = fields.Many2one('project.task', string="Task", domain="[('phase_id', '=', phase_id)]")
    prev_contract_amount = fields.Monetary(string="Previous Amount", store=True, compute="_get_amount")
    supplement_amount = fields.Monetary(string="Supplemental/Adjustment Amount", required=True)
    new_amount = fields.Monetary(string="New Amount", store=True, compute="_get_amount")
    date = string = fields.Date(string="Approved Date")
    name = fields.Text(string="Description", required=True)

    def set_adjustement(self):
        for i in self:
            if not i.budget_adjustment:
                if i.project_id.project_budget_amount > i.new_amount:
                    raise  ValidationError(_('Project Budget Amount must be not Greater than the Project Contract Amount.'))
                i.project_id.write({
                    'project_contract_amount': i.new_amount,
                    'supplement_log_ids': [[0, 0, {
                        'user_id': i._uid,
                        'date': i.date,
                        'record_date': datetime.now(),
                        'name': i.name,
                        'prev_contract_amount': i.prev_contract_amount,
                        'supplement_amount': i.supplement_amount,
                        'new_amount': i.new_amount
                        }]],
                    })
            elif i.budget_adjustment and i.adjustment_category in ['project']:
                current_allocation = sum(line.phase_budget_amount for line in i.project_id.phase_ids)
                if current_allocation > i.new_amount:
                    raise  ValidationError(_('Phase Budget allocation must be not Greater than the Project Budget Amount.'))
                if i.project_id.project_contract_amount < i.new_amount:
                    raise  ValidationError(_('Project budget adjustment must not be exceeding the contract amount.'))
                i.project_id.write({
                    'project_budget_amount': i.new_amount,
                    'supplement_log_ids': [[0, 0, {
                        'user_id': i._uid,
                        'date': i.date,
                        'record_date': datetime.now(),
                        'name': i.name,
                        'prev_contract_amount': i.prev_contract_amount,
                        'supplement_amount': i.supplement_amount,
                        'new_amount': i.new_amount,
                        'budget_adjustment': True,
                        }]],
                    })
            elif i.budget_adjustment and i.adjustment_category in ['phase']:
                current_allocation = sum(line.task_budget for line in i.phase_id.task_ids)
                if current_allocation > i.new_amount:
                    raise  ValidationError(_('Task Budget allocation must be not Greater than the Phase Budget Amount.'))
                if (i.project_id.project_budget_allocated + i.supplement_amount) > i.project_id.project_budget_amount:
                    raise  ValidationError(_('Phase budget adjustment must not be exceeding the Project budget amount.'))
                i.phase_id.write({'phase_budget_amount': i.new_amount})
                i.project_id.write({
                    'supplement_log_ids': [[0, 0, {
                        'user_id': i._uid,
                        'phase_id': i.phase_id.id,
                        'date': i.date,
                        'record_date': datetime.now(),
                        'name': i.name,
                        'prev_contract_amount': i.prev_contract_amount,
                        'supplement_amount': i.supplement_amount,
                        'new_amount': i.new_amount,
                        'budget_adjustment': True,
                        }]],
                    })
            elif i.budget_adjustment and i.adjustment_category in ['task']:
                if i.task_id.total_budget > i.new_amount:
                    raise  ValidationError(_('BOQ Budget must be not Greater than the Task Budget Amount.'))
                if (i.phase_id.phase_budget_allocated + i.supplement_amount) > i.phase_id.phase_budget_amount:
                    raise  ValidationError(_('Task budget adjustment must not be exceeding the Phase budget amount.'))
                i.task_id.write({'task_budget': i.new_amount})
                i.project_id.write({
                    'supplement_log_ids': [[0, 0, {
                        'user_id': i._uid,
                        'phase_id': i.phase_id.id,
                        'task_id': i.task_id.id,
                        'date': i.date,
                        'record_date': datetime.now(),
                        'name': i.name,
                        'prev_contract_amount': i.prev_contract_amount,
                        'supplement_amount': i.supplement_amount,
                        'new_amount': i.new_amount,
                        'budget_adjustment': True,
                        }]],
                    })
        return True
