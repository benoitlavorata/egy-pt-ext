from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class EstimatedSheet(models.Model):
    _name = 'estimated.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Estimated Sheet"

    name = fields.Char(string='Reference Number', index=True, readonly=True, copy=False,
                       default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', required=True, tracking=True, track_visibility="onchange")
    partner_id = fields.Many2one(related='project_id.partner_id', readonly=True, index=True, store=True)
    boq_id = fields.Many2one('project.boq', string="BOQ", readonly=True, required=True)
    date = fields.Date(default=fields.Date.context_today, track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
                              ('cancelled', 'Cancelled')], string='Status', readonly=True,
                             copy=False, index=True, track_visibility='onchange', default='draft')
    submitted_by = fields.Char("Submitted By", readonly=True, copy=False)
    cancelled_by = fields.Char("Cancelled By", readonly=True, copy=False)
    approved_by = fields.Char("Approved By", readonly=True, copy=False)
    submitted_date = fields.Datetime("Submitted Date", readonly=True, copy=False)
    cancelled_date = fields.Datetime("Cancelled Date", readonly=True, copy=False)
    approved_date = fields.Datetime("Approved Date", readonly=True, copy=False)
    labour_ids = fields.One2many(comodel_name='es.labours', inverse_name='es_labour_id',
                                 string=_("Labours"))
    material_ids = fields.One2many(comodel_name='es.materials', inverse_name='es_product_id',
                                   string=_("Materials"))
    asset_ids = fields.One2many(comodel_name='es.assets', inverse_name='es_asset_id',
                                string=_("Equipments"))
    expense_ids = fields.One2many(comodel_name='es.expenses', inverse_name='es_expenses_id',
                                  string=_("Overhead"))
    total_labour = fields.Float("Labours", compute='_compute_total', store=True)
    total_product = fields.Float("Materials", compute='_compute_total', store=True)
    total_assets = fields.Float("Equipments", compute='_compute_total', store=True)
    total_expenses = fields.Float("Overhead", compute='_compute_total', store=True)
    es_total_labour = fields.Float("Average Labours", compute='_compute_total', store=True)
    es_total_product = fields.Float("Average Materials", compute='_compute_total', store=True)
    es_total_assets = fields.Float("Average Equipments", compute='_compute_total', store=True)
    total = fields.Float("Total", compute='_compute_total', store=True)
    es_total = fields.Float("Total Average", compute='_compute_total', store=True)
    notes = fields.Html()

    @api.depends('labour_ids', 'material_ids', 'asset_ids', 'expense_ids')
    def _compute_total(self):
        for boq in self:
            total_material = total_labour = total_asset = total_expenses = 0
            total_avg_material = total_avg_labour = total_avg_asset = 0
            if boq.material_ids:
                for line in boq.material_ids:
                    total_material += line.total_material
                    total_avg_material += line.total_avg_material
            if boq.labour_ids:
                for line in boq.labour_ids:
                    total_labour += line.total_labour
                    total_avg_labour += line.total_labour
            if boq.asset_ids:
                for line in boq.asset_ids:
                    total_asset += line.total_asset
                    total_avg_asset += line.total_average_asset
            if boq.expense_ids:
                for line in boq.expense_ids:
                    total_expenses += line.total_expense
            boq.total_product = total_material
            boq.es_total_product = total_avg_material
            boq.total_labour = total_labour
            boq.es_total_labour = total_avg_labour
            boq.total_assets = total_asset
            boq.es_total_assets = total_avg_asset
            boq.total_expenses = total_expenses
            boq.total = total_material + total_labour + total_asset + total_expenses
            boq.es_total = total_avg_material + total_avg_labour + total_avg_asset

    @api.onchange('project_id')
    def _onchange_project(self):
        for boq in self:
            if boq.project_id:
                boq_id = self.env['project.boq'].search([('project_id', '=', boq.project_id.id)], limit=1)
                boq.boq_id = boq_id
            else:
                boq.boq_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('estimated.sheet') or 'New'
        result = super(EstimatedSheet, self).create(vals)
        return result

    def es_action_submit(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'submitted',
                    'submitted_by': user.name,
                    'submitted_date': datetime.today()})
        if self.name == 'New':
            val = self.env['ir.sequence'].next_by_code('estimated.sheet')
            self.write({'name': val})

    def es_action_approve(self):
        user = self.env['res.users'].browse(self.env.uid)
        self.write({'state': 'approved',
                    'approved_by': user.name,
                    'approved_date': datetime.today()})

    def es_action_cancel(self):
        user = self.env['res.users'].browse(self.env.uid)
        return self.write({'state': 'cancelled',
                           'cancelled_by': user.name,
                           'cancelled_date': datetime.today()})

    def es_action_draft(self):
        return self.write({
            'state': 'draft',
        })


class LaboursLines(models.Model):
    _name = 'es.labours'
    _description = "Estimated Labours"

    es_labour_id = fields.Many2one('estimated.sheet', required=True)
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    labour_boq = fields.Many2one('project.boq')
    name = fields.Many2one('hr.contract.type', required=True, string="Type")
    labour_no = fields.Integer('Number of Labour', required=True, default=1)
    work_day = fields.Integer('Days', required=True, default=1)
    es_per_day = fields.Float('Value', required=True)
    avg_per_day = fields.Float('Average', readonly=True, store=True, default=0)
    total_labour = fields.Float('Total', readonly=True, store=True, default=0)
    avg_total_labour = fields.Float('Total Average', readonly=True, store=True, default=0)

    @api.onchange('name', 'labour_no', 'work_day', 'es_per_day')
    def _onchange_project(self):
        for lab in self:
            if lab.name and lab.work_day > 0 and lab.labour_no > 0:
                avg = self.env['hr.contract'].search([('type_id', '=', lab.name.id), ('state', '=', 'open')], limit=1).wage
                if avg:
                    lab.avg_per_day = avg / 30
                    lab.avg_total_labour = lab.labour_no * (avg / 30) * lab.work_day
                lab.total_labour = lab.labour_no * lab.es_per_day * lab.work_day

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class MaterialsLines(models.Model):
    _name = 'es.materials'
    _description = "Estimated Materials"

    es_product_id = fields.Many2one('estimated.sheet', required=True)
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    product_id = fields.Many2one('product.product', required=True)
    product_qty = fields.Integer('Qty', required=True, default=1)
    product_uom = fields.Many2one(related='product_id.uom_id', required=True, readonly=True)
    es_per_unit = fields.Float('Value', required=True, default=0)
    avg_per_unit = fields.Float('Average', readonly=True, store=True, default=0)
    total_material = fields.Float('Total', readonly=True, store=True, default=0)
    total_avg_material = fields.Float('Total Average', readonly=True, store=True, default=0)

    @api.onchange('product_id', 'product_qty', 'es_per_unit')
    def _onchange_product(self):
        for mat in self:
            if mat.product_id and mat.product_qty > 0:
                cost = self.env['product.template'].search([('id', '=', mat.product_id.id)], limit=1).standard_price
                if cost:
                    mat.avg_per_unit = cost
                    mat.total_avg_material = cost * mat.product_qty
                mat.total_material = mat.es_per_unit * mat.product_qty

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class AssetsLines(models.Model):
    _name = 'es.assets'
    _description = "Estimated Assets"

    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    es_asset_id = fields.Many2one('estimated.sheet', required=True)
    asset_id = fields.Many2one('account.asset', required=True)
    asset_qty = fields.Integer('Qty', required=True, default=1)
    asset_w_days = fields.Float('Days', required=True, default=1)
    es_per_asset = fields.Float('Value', required=True)
    avg_per_asset = fields.Float('Average', readonly=True, store=True, default=0)
    total_asset = fields.Float('Total', readonly=True, store=True, default=0)
    total_average_asset = fields.Float('Total Average', readonly=True, store=True, default=0)

    @api.onchange('asset_id', 'asset_qty', 'asset_w_days', 'es_per_asset')
    def _onchange_asset(self):
        for ass in self:
            if ass.asset_id and ass.asset_qty > 0 and ass.asset_w_days > 0:
                cost = self.env['account.asset'].search([('id', '=', ass.asset_id.id)], limit=1).rent_per_day
                if cost:
                    ass.avg_per_asset = cost
                    ass.total_average_asset = cost * ass.asset_qty * ass.asset_w_days
                ass.total_asset = ass.es_per_asset * ass.asset_qty * ass.asset_w_days

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class ExpensesLines(models.Model):
    _name = 'es.expenses'
    _description = "Estimated Expenses"

    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    es_expenses_id = fields.Many2one('estimated.sheet', required=True)
    expenses_id = fields.Many2one('account.account', domain="[('user_type_id', 'in', ['Expenses'])]", required=True)
    total_expense = fields.Float('Total', required=True, default=0)

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id
