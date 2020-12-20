# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, exceptions, _
from datetime import datetime
from odoo.exceptions import Warning, UserError, ValidationError


class JobType(models.Model):
    _name = 'job.type'
    _description = 'Task Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    job_type = fields.Selection(selection=[('material', 'Material'), ('labour', 'Labour'), ('overhead', 'Overhead')],
                                string='Type', required=True)


class TaskCosting(models.Model):
    _name = 'job.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Task Costing"

    @api.depends('material_ids', 'material_ids.product_qty', 'material_ids.act_per_unit')
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum([(p.product_qty * p.act_per_unit) for p in rec.material_ids])

    @api.depends('labour_ids', 'labour_ids.labour_no', 'labour_ids.work_day', 'labour_ids.total_labour')
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.labour_no * p.work_day * p.total_labour) for p in rec.labour_ids])

    @api.depends('asset_ids', 'asset_ids.total_asset')
    def _compute_equipment_total(self):
        for rec in self:
            rec.equipment_total = sum([p.total_asset for p in rec.asset_ids])

    @api.depends('expense_ids', 'expense_ids.total_expense')
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([p.total_expense for p in rec.expense_ids])

    @api.depends('material_total', 'labor_total', 'overhead_total', 'equipment_total')
    def _compute_task_cost_total(self):
        for rec in self:
            rec.jobcost_total = rec.material_total + rec.labor_total + rec.equipment_total + rec.overhead_total

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id
            rec.partner_id = rec.project_id.partner_id.id
            last_sheet_date = self.env['job.costing'].search([('project_id', '=', rec.project_id.id)])
            if last_sheet_date:
                dt = rec.project_id.start_date
                for sheet in last_sheet_date:
                    if sheet.complete_date and dt:
                        if sheet.complete_date > dt:
                            dt = sheet.complete_date
                rec.start_date = dt

    @api.depends('material_ids.stock_move_id')
    def _compute_stock_move(self):
        for rec in self:
            rec.stock_move_ids = rec.mapped('material_ids.stock_move_id')

    name = fields.Char(required=True, copy=True, string="Reference Number", default='New')
    notes_job = fields.Text(required=False, copy=True, string='Job Cost Details')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user,  string='Created By', readonly=True)
    description = fields.Html(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Company', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    analytic_id = fields.Many2one(related='project_id.analytic_account_id', string='Analytic Account')
    start_date = fields.Date(string='From', required=True, default=fields.Date.today())
    complete_date = fields.Date(string='To', required=True, default=fields.Date.today())
    material_total = fields.Float(string='Total Material Cost', compute='_compute_material_total', store=True)
    labor_total = fields.Float(string='Total Labour Cost', compute='_compute_labor_total', store=True)
    equipment_total = fields.Float(string='Total Equipment Cost', compute='_compute_equipment_total', store=True)
    overhead_total = fields.Float(string='Total Overhead Cost', compute='_compute_overhead_total', store=True)
    jobcost_total = fields.Float(string='Total Cost', compute='_compute_task_cost_total', store=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'),
                             ('done', 'Done'), ('cancel', 'Canceled')], string='State', track_visibility='onchange',
                             default='draft')
    confirmed_by = fields.Char("Confirmed By", readonly=True, copy=False)
    cancelled_by = fields.Char("Cancelled By", readonly=True, copy=False)
    approved_by = fields.Char("Approved By", readonly=True, copy=False)
    confirmed_date = fields.Datetime("Confirmed Date", readonly=True, copy=False)
    cancelled_date = fields.Datetime("Cancelled Date", readonly=True, copy=False)
    approved_date = fields.Datetime("Approved Date", readonly=True, copy=False)
    labour_ids = fields.One2many(comodel_name='act.labours', inverse_name='act_labour_id', string=_("Labours"))
    material_ids = fields.One2many(comodel_name='act.materials', inverse_name='act_product_id', string=_("Materials"))
    asset_ids = fields.One2many(comodel_name='act.assets', inverse_name='act_asset_id', string=_("Equipments"))
    expense_ids = fields.One2many(comodel_name='act.expenses', inverse_name='act_expenses_id', string=_("Overhead"))
    task_progress = fields.One2many(comodel_name='task.progress', inverse_name='act_progress',
                                    string=_("Task Progress"))
    stock_state = fields.Selection(selection=[('pending', 'Pending'), ('confirmed', 'Confirmed'),
                                              ('assigned', 'Assigned'), ('done', 'Done')])
    stock_move_ids = fields.Many2many(comodel_name='stock.move', compute='_compute_stock_move', string='Stock Moves')
    picking_id = fields.Many2one("stock.picking", related="stock_move_ids.picking_id")

    @api.model
    def create(self, values):
        number = self.env['ir.sequence'].next_by_code('job.costing')
        values.update({
            'name': number,
        })
        return super(TaskCosting, self).create(values)

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise Warning(_('You can not delete Task Cost Sheet which is not draft or cancelled.'))
        return super(TaskCosting, self).unlink()

    def action_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft',
            })
    
    def action_confirm(self):
        user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            rec.write({
                'state': 'confirm',
                'confirmed_by': user.name,
                'confirmed_date': datetime.today()
            })
        
    def action_approve(self):
        user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            rec.write({
                'state': 'approve',
                'approved_by': user.name,
                'approved_date': datetime.today()
            })
    
    def action_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'complete_date': date.today(),
            })
        
    def action_cancel(self):
        user = self.env['res.users'].browse(self.env.uid)
        for rec in self:
            rec.write({
                'state': 'cancel',
                'cancelled_by': user.name,
                'cancelled_date': datetime.today()
            })

    def action_assign(self):
        self.mapped('stock_move_ids')._action_assign()

    def stock_move_done(self):
        for move in self.mapped('stock_move_ids'):
            move.quantity_done = move.product_uom_qty
        self.mapped('stock_move_ids')._action_done()

    def write(self, values):
        res = super(TaskCosting, self).write(values)
        for jc in self:
            if 'material_ids' in values:
                if jc.project_id.stock_warehouse_id and jc.project_id.stock_location_id and jc.project_id.picking_type_id:
                    todo_lines = jc.material_ids.filtered(lambda m: not m.stock_move_id)
                    if todo_lines:
                        todo_lines.create_stock_move()
                        # todo_lines.create_analytic_line()
                else:
                    raise exceptions.Warning(_("Please Complete Project Information"))
        return res


class MaterialsLines(models.Model):
    _name = 'act.materials'
    _description = "Task Cost Materials"

    act_product_id = fields.Many2one('job.costing', required=True)
    project = fields.Integer()
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    product_id = fields.Many2one('product.product', required=True)
    product_qty = fields.Integer('Qty', required=True, default=1)
    product_uom = fields.Many2one(related='product_id.uom_id', required=True, readonly=True)
    act_per_unit = fields.Float('Value', required=True, default=0)
    total_material = fields.Float('Total', readonly=True, store=True, default=0)
    description = fields.Char(string='Description')
    stock_move_id = fields.Many2one(comodel_name='stock.move', string='Stock Move')

    @api.onchange('product_id', 'product_qty')
    def _onchange_product(self):
        for mat in self:
            if mat.product_id and mat.product_qty > 0:
                cost = self.env['product.template'].search([('id', '=', mat.product_id.id)], limit=1).standard_price
                if cost:
                    mat.act_per_unit = cost
                mat.total_material = mat.act_per_unit * mat.product_qty

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id

    def _prepare_stock_move(self):
        product = self.product_id
        res = {
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': self.product_uom.id or product.uom_id.id,
            'product_uom_qty': self.product_qty,
            'origin': self.task_id.name,
            'location_id': self.act_product_id.project_id.stock_location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        }
        return res

    def create_stock_move(self):
        pick_type = self.env.ref('construction.task_cost_material_picking_type')
        task = self[0].act_product_id
        picking_id = task.picking_id or self.env['stock.picking'].create({
            'origin': "{}/{}".format(task.project_id.name, task.name),
            'partner_id': task.project_id.partner_id.id,
            'picking_type_id': pick_type.id,
            'location_id': pick_type.default_location_src_id.id,
            'location_dest_id': pick_type.default_location_dest_id.id,
        })
        for line in self:
            if not line.stock_move_id:
                move_vals = line._prepare_stock_move()
                move_vals.update({'picking_id': picking_id.id or False})
                move_id = self.env['stock.move'].create(move_vals)
                line.stock_move_id = move_id.id

    def _update_unit_amount(self):
        for sel in self.filtered(lambda x: x.stock_move_id.state == 'done' and
                                 x.analytic_line_id.amount !=
                                 x.stock_move_id.value):
            sel.analytic_line_id.amount = sel.stock_move_id.value


class LaboursLines(models.Model):
    _name = 'act.labours'
    _description = "Task Cost Labours"

    act_labour_id = fields.Many2one('job.costing', required=True)
    project = fields.Integer()
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    name = fields.Many2one('hr.contract.type', required=True, string="Type")
    labour_no = fields.Integer('Number of Labour', required=True, default=1)
    work_day = fields.Integer('Days', required=True, default=1)
    total_labour = fields.Float('Total', readonly=True, store=True, default=0)
    description = fields.Char(string='Description')

    @api.onchange('name', 'labour_no', 'work_day')
    def _onchange_labour(self):
        for lab in self:
            if lab.name and lab.work_day > 0 and lab.labour_no > 0:
                cost = 0
                avg = self.env['hr.contract'].search([('type_id', '=', lab.name.id), ('state', '=', 'open')],
                                                     limit=1).wage
                if avg:
                    cost += avg / 30
                lab.total_labour = lab.labour_no * cost * lab.work_day

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class AssetsLines(models.Model):
    _name = 'act.assets'
    _description = "Task Cost Assets"

    act_asset_id = fields.Many2one('job.costing', required=True)
    project = fields.Integer()
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    asset_id = fields.Many2one('account.asset', required=True)
    asset_qty = fields.Integer('Qty', required=True, default=1)
    asset_w_days = fields.Float('Days', required=True, default=1)
    total_asset = fields.Float('Total', readonly=True, store=True, default=0)
    description = fields.Char(string='Description')

    @api.onchange('asset_id', 'asset_qty', 'asset_w_days', 'es_per_asset')
    def _onchange_asset(self):
        for ass in self:
            if ass.asset_id and ass.asset_qty > 0 and ass.asset_w_days > 0:
                cost = self.env['account.asset'].search([('id', '=', ass.asset_id.id)], limit=1).rent_per_day
                ass.total_asset = cost * ass.asset_qty * ass.asset_w_days

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class ExpensesLines(models.Model):
    _name = 'act.expenses'
    _description = "Task Cost Expenses"

    act_expenses_id = fields.Many2one('job.costing', required=True)
    project = fields.Integer()
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    expenses_id = fields.Many2one('account.account', domain="[('user_type_id', 'in', ['Expenses'])]", required=True)
    total_expense = fields.Float('Total', required=True, default=0)
    description = fields.Text(string='Description')

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id


class TaskProgress(models.Model):
    _name = 'task.progress'
    _description = "Task Progress"

    act_progress = fields.Many2one('job.costing', required=True)
    project = fields.Integer()
    phase_id = fields.Many2one('project.phase')
    task_id = fields.Many2one('project.task')
    progress_before = fields.Float("Before", default=0.0)
    progress_current = fields.Float("Current", required=True)
    description = fields.Text(string='Description')

    @api.onchange('task_id')
    def _onchange_task(self):
        for line in self:
            line.phase_id = line.task_id.phase_id
            line.progress_before = line.task_id.task_progress

    @api.model
    def create(self, values):
        if values.get('progress_current') > values.get('progress_before'):
            progress = values.get('progress_current')
            if progress:
                task = self.env['project.task'].search([('id', '=', values.get('task_id'))])
                task.update({
                    'task_progress': progress
                })
        else:
            raise ValidationError(_("Wrong value"))
        return super(TaskProgress, self).create(values)

    def write(self, values):
        if values.get('progress_current') > values.get('progress_before'):
            progress = values.get('progress_current')
            if progress:
                task = self.env['project.task'].search([('id', '=', self.task_id.id)])
                task.update({
                    'task_progress': progress
                })
            return super(TaskProgress, self).write(values)
        else:
            raise ValidationError(_("Wrong value"))

    def unlink(self):
        for line in self:
            task = self.env['project.task'].search([('id', '=', self.task_id.id)])
            task.update({
                'task_progress': line.progress_before
            })
        return super(TaskProgress, self).unlink()


class StockMove(models.Model):
    _inherit = 'stock.move'

    task_material_id = fields.One2many('act.materials', 'stock_move_id', string='Project Task Material')

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        self.mapped('task_material_id')._update_unit_amount()
        return res