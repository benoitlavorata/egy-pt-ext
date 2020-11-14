'''
Created on 22 July 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp

class ProjectOverheadBudget(models.Model):
    _name = 'project.overhead.budget'

    category_id = fields.Many2one('boq.overhead.category', string='Category')
    name = fields.Char(string='Name')
    qty = fields.Float(string="Quantity",
                       digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    unit_rate = fields.Float(string="Unit Rate",
                             digits=dp.get_precision('Product Price'))
    subtotal = fields.Float(string="Subtotal",
                            compute='_compute_overhead_subtotal',
                            digits=dp.get_precision('Product Price'))
    project_id = fields.Many2one('project.project', string='Project',
                             ondelete='cascade', index=True, copy=False)

    @api.depends('qty', 'unit_rate')
    def _compute_overhead_subtotal(self):
        for overhead in self:
            subtotal = (overhead.unit_rate * overhead.qty)
            overhead.update({'subtotal': subtotal})


class OverheadCategory(models.Model):
    _name = 'boq.overhead.category'

    name = fields.Char("Name", required=True)


class ProjectLaborBudget(models.Model):
    _name = 'project.labor.budget'

    job_id = fields.Many2one('hr.job', string='Name')
    description = fields.Char(string='Description')
    head_count = fields.Integer("Head Count")
    budget_head_count = fields.Integer("Budget/Head Count")
    uom_id = fields.Many2one('uom.uom', string="UOM",
                             help="Unit of Measure")
    dur_payment_term = fields.Float("Duration of Payment Terms",
                                    digits=dp.get_precision('Product Price'))
    labor_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_labor_subtotal',
                                  digits=dp.get_precision('Product Price'))
    labor_total = fields.Float(string="Total", compute='_compute_labor_total',
                               digits=dp.get_precision('Product Price'))
    project_id = fields.Many2one('project.project', string='Project',
                             ondelete='cascade', index=True, copy=False)

    @api.depends('head_count', 'budget_head_count')
    def _compute_labor_subtotal(self):
        for labor in self:
            subtotal = (labor.head_count*labor.budget_head_count)
            labor.update({'labor_subtotal': subtotal})

    @api.depends('labor_subtotal', 'dur_payment_term')
    def _compute_labor_total(self):
        for labor in self:
            total = (labor.labor_subtotal*labor.dur_payment_term)
            labor.update({'labor_total': total})

    @api.onchange('job_id')
    def _onchange_hr_jobs(self):
        self.update({'description': self.job_id.description})


class ProjectBudgetAdjustmentLog(models.Model):
    _name = 'project.budget.adjustment.log'

    @api.depends('project_id', 'phase_id', 'task_id', 'budget_adjustment')
    def _get_document(self):
        for i in self:
            if i.task_id and i.phase_id:
                i.document = 'Task - ' + i.phase_id.name + '/' + i.task_id.name
            elif i.phase_id:
                i.document = 'Phase - ' + i.phase_id.name
            else:
                if i.budget_adjustment:
                    if i.project_id.project_type == 'project':
                        i.document = 'Project - Budget Adjustment'
                    else: i.document = 'Portfolio - Budget Adjustment'
                else:
                    if i.project_id.project_type == 'project':
                        i.document = 'Project - Contract Supplement'
                    else: i.document = 'Portfolio - Contract Supplement'

    currency_id = fields.Many2one('res.currency', related='project_id.company_id.currency_id', string="Company Currency")
    project_id = fields.Many2one('project.project', string="Project")
    phase_id = fields.Many2one('project.phase', string="Phase")
    task_id = fields.Many2one('project.task', string="Task")
    user_id = fields.Many2one('res.users', string="User")
    record_date = fields.Datetime(string="Date")
    date = string = fields.Date(string="Approved Date")
    prev_contract_amount = fields.Monetary(string="Previous Amount", store=True, compute="_get_amount")
    supplement_amount = fields.Monetary(string="Supplemental/Adjustment Amount", required=True)
    new_amount = fields.Monetary(string="New Amount", store=True, compute="_get_amount")
    name = fields.Text(string="Description", required=True)
    document = fields.Char(string="Document", store=True, compute="_get_document")
    budget_adjustment = fields.Boolean(string="Budget Adjustment")


class Project(models.Model):
    _inherit = "project.project"

    @api.depends('project_budget_amount', 'phase_ids', 'phase_ids.phase_budget_amount', 'labor_budget_ids', 'labor_budget_ids.labor_total', 'overhead_budget_ids', 'overhead_budget_ids.subtotal', 'project_ids', 'project_ids.project_contract_amount', 'project_type')
    def _get_budget_computation(self):
        for i in self:
            labor_budget = sum(line.labor_total for line in i.labor_budget_ids)
            overhead_budget = sum(line.subtotal for line in i.overhead_budget_ids)
            budget = sum(line.phase_budget_amount for line in i.phase_ids)
            if i.project_type != 'project':
                budget = sum(line.project_contract_amount for line in i.project_ids)
            reserve = i.project_budget_amount - (labor_budget + budget + overhead_budget)
            i.project_budget_allocated = (labor_budget + budget + overhead_budget)
            i.project_budget_reserve = reserve

    #@api.depends('account_analytic_line_ids', 'account_analytic_line_ids.account_id', 'account_analytic_line_ids.phase_id', 'account_analytic_line_ids.task_id', 'account_analytic_line_ids.project_boq_category')
    def _get_project_expense(self):
        for i in self:
            material_expense = 0.0
            service_expense = 0.0
            labor_expense = 0.0
            equipment_expense = 0.0
            overhead_expense = 0.0
            analytic_account = [i.analytic_account_id.id]
            if i.analytic_account_id.group_id:
                analytic_group = i.env['account.analytic.group'].search([('id', 'child_of', i.analytic_account_id.group_id.id)]).ids
                analytic_account = i.env['account.analytic.account'].search([('group_id', 'in', analytic_group)]).ids
            for line in i.env['account.analytic.line'].search([('account_id', 'in', analytic_account), ('amount', '<=', 0.0)]):
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
            i.project_actual_expense = sum([material_expense, service_expense, labor_expense, equipment_expense, overhead_expense])
            i.total_expense = sum([material_expense, service_expense, labor_expense, equipment_expense, overhead_expense])
            i.material_expense = material_expense
            i.service_expense = service_expense
            i.labor_expense = labor_expense
            i.equipment_expense = equipment_expense
            i.overhead_expense = overhead_expense

    # @api.depends('task_ids',
    #              'task_ids.material_budget',
    #              'task_ids.service_budget',
    #              'task_ids.overhead_budget',
    #              'task_ids.equipment_budget',
    #              'task_ids.labor_budget',
    #              'labor_budget_ids',
    #              'overhead_budget_ids',
    #              'project_type')
    def _get_budget_summary(self):
        for i in self:
            material = service = equipment = labor = overhead = 0.0
            if i.project_type == 'project':
                labor = sum(line.labor_total for line in i.labor_budget_ids)
                overhead = sum(line.subtotal for line in i.overhead_budget_ids)
                for task in i.task_ids:
                    material += task.material_budget
                    service += task.service_budget
                    labor += task.labor_budget
                    equipment += task.equipment_budget
                    overhead += task.overhead_budget
            else:
                for project in i.project_ids:
                    labor += sum(line.labor_total for line in project.labor_budget_ids)
                    overhead += sum(line.subtotal for line in project.overhead_budget_ids)
                    for task in i.task_ids:
                        material += task.material_budget
                        service += task.service_budget
                        labor += task.labor_budget
                        equipment += task.equipment_budget
                        overhead += task.overhead_budget
            i.material_budget = material
            i.service_budget = service
            i.labor_budget = labor
            i.equipment_budget = equipment
            i.overhead_budget = overhead
            i.total_budget = sum([material, service, labor, equipment, overhead])

    def _compute_actual_accomplishment(self):
        for i in self:
            rec = [line.actual for line in i.projection_accomplishment_ids]
            if rec:
                i.actual_accomplishment = max(rec)
            else:
                i.actual_accomplishment = 0

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    project_contract_amount = fields.Monetary(String='Contract Amount', readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    project_budget_amount = fields.Monetary(string="Budget Amount", readonly=True, states={'draft': [('readonly', False)]}, track_visibility="always")
    project_budget_allocated = fields.Monetary(string="Budget Allocated", store=True, compute='_get_budget_computation', help="Total Division Budget + Total Human Resource Budget + Total Overheads Budget")
    project_budget_reserve = fields.Monetary(stirng="Budget Reserve", store=True, compute='_get_budget_computation')
    project_actual_expense = fields.Monetary(string="Actual Expense", compute='_get_project_expense')
    account_analytic_line_ids = fields.One2many('account.analytic.line', 'project_id')
    supplement_log_ids = fields.One2many('project.budget.adjustment.log', 'project_id', string="Logs")
    material_expense = fields.Monetary(string="Material Expense", compute='_get_project_expense')
    service_expense = fields.Monetary(string="Service Expense", compute='_get_project_expense')
    labor_expense = fields.Monetary(string="Labor Expense", compute='_get_project_expense')
    equipment_expense = fields.Monetary(string="Equipment Expense", compute='_get_project_expense')
    overhead_expense = fields.Monetary(string="Overhead Expense", compute='_get_project_expense')
    total_expense = fields.Monetary(string="Total Expense", compute='_get_project_expense')

    material_budget = fields.Monetary(string="Material Budget", compute="_get_budget_summary")
    service_budget = fields.Monetary(string="Service Budget", compute="_get_budget_summary")
    labor_budget = fields.Monetary(string="Labor Budget", compute="_get_budget_summary")
    equipment_budget = fields.Monetary(string="Equipment Budget", compute="_get_budget_summary")
    overhead_budget = fields.Monetary(string="Overhead Budget", compute="_get_budget_summary")
    total_budget = fields.Monetary(string="Total Budget", compute="_get_budget_summary")

    project_ids = fields.One2many('project.project', 'parent_id', string="Projects")
    actual_accomplishment = fields.Float(string="Actual Accomplishment", compute="_compute_actual_accomplishment")
    labor_budget_ids = fields.One2many('project.labor.budget', 'project_id', string="Labor Budget")
    overhead_budget_ids = fields.One2many('project.overhead.budget', 'project_id', string="Overheads Budget")
