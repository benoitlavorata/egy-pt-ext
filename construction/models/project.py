# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class Project(models.Model):
    _inherit = "project.project"

    def _compute_jobcost_count(self):
        jobcost = self.env['job.costing']
        job_cost_ids = self.mapped('job_cost_ids')
        for project in self:
            project.job_cost_count = jobcost.search_count([('id', 'in', job_cost_ids.ids)])

    def _compute_estimated_count(self):
        estimated = self.env['estimated.sheet']
        estimated_ids = self.mapped('job_cost_ids')
        for project in self:
            project.estimated_count = estimated.search_count([('id', 'in', estimated_ids.ids)])

    def _compute_phase_count(self):
        phase = self.env['project.phase']
        phase_ids = self.mapped('phase_ids')
        for project in self:
            project.phase_count = phase.search_count([('id', 'in', phase_ids.ids)])

    def _compute_asset_order_count(self):
        for project in self:
            order_count = self.env['asset.work.order'].search([('project_id', '=', project.id)])
            if len(order_count) > 0:
                project.asset_order_count = order_count
            else:
                project.asset_order_count = 0

    def _compute_boq_amount(self):
        for pro in self:
            boq = self.env['project.boq'].search([('project_id', '=', pro.id)], limit=1)
            pro.boq_amount = boq.boq_total_price
            pro.boq_qty_amount = boq.boq_total_qty

    def _compute_actual_amount(self):
        for pro in self:
            amount = 0
            qty = 0
            act = self.env['job.costing'].search([('project_id', '=', pro.id)])
            for cost in act:
                amount += cost.jobcost_total
            pro.actual_amount = amount
            pro.actual_qty_amount = qty
            print(amount)

    def _compute_estimated(self):
        for pro in self:
            amount = 0
            es = self.env['estimated.sheet'].search([('project_id', '=', pro.id)])
            for cost in es:
                amount += cost.es_total
            pro.total_es = amount
            print(amount)

    job_cost_count = fields.Integer(compute='_compute_jobcost_count')
    job_cost_ids = fields.One2many('job.costing', 'project_id')
    phase_count = fields.Integer(compute='_compute_phase_count')
    phase_ids = fields.One2many('project.phase', 'project_id')
    boq_id = fields.One2many(comodel_name='project.boq', inverse_name='project_id')
    poq_line_ids = fields.One2many(related='boq_id.poq_line_ids')
    payment_ids = fields.One2many(comodel_name='project.payments', inverse_name='project_id')
    estimated_count = fields.Integer(string='Estimated Sheet', compute='_compute_estimated_count')
    estimated_ids = fields.One2many(comodel_name='estimated.sheet', inverse_name='project_id')
    start_date = fields.Date('Start Date', track_visibility="always")
    end_date = fields.Date(string='End Date', track_visibility="always")
    extension_date = fields.Date(string='Requested Extension Date', track_visibility="always")
    state = fields.Selection([('draft', 'Draft'), ('study', 'Study'),
                              ('inprogress', 'In Progress'),
                              ('closed', 'Closed'),
                              ('canceled', 'Canceled'),
                              ('halted', 'Halted')], string="Status", readonly=True, default='draft', track_visibility="always")
    act_date_start = fields.Datetime(string='Actual Starting Date', index=True, copy=False)
    act_date_end = fields.Datetime(string='Actual Ending Date', index=True, copy=False)
    stock_warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", track_visibility="always")
    stock_location_id = fields.Many2one('stock.location', string="Inventory Location", track_visibility="always")
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Operation", track_visibility="always")
    employee_id = fields.Many2one("res.users", string="Employee")
    project_deduction_line_ids = fields.One2many(comodel_name='deductions.line', inverse_name='project_id',
                                                 string=_("Deduction"))
    asset_order_count = fields.Integer(compute='_compute_asset_order_count', string="Asset work order")
    privacy_visibility = fields.Selection([('followers', 'Invited employees'), ('employees', 'All employees'),
                                          ('portal', 'Portal users and all employees')], string='Visibility',
                                          required=True, default='followers')
    boq_amount = fields.Integer(string="BOQ amount", compute='_compute_boq_amount')
    actual_amount = fields.Integer(string="Actual amount", compute='_compute_actual_amount', store=True)
    boq_qty_amount = fields.Integer(string="BOQ amount", compute='_compute_boq_amount', store=True)
    actual_qty_amount = fields.Integer(string="Actual amount", compute='_compute_actual_amount', store=True)
    type_of_construction = fields.Selection([('post_tension', 'Post Tension'), ('other', 'other')],
                                            string='Types of Construction', default="post_tension")
    location_id = fields.Many2one('res.partner', string='Location')
    notes_ids = fields.One2many('note.note', 'project_id', string='Notes Id')
    notes_count = fields.Integer(compute='_compute_notes_count', string="Notes")
    partner_email = fields.Char(related='partner_id.email', string='Customer Email', readonly=False)
    partner_phone = fields.Char(related='partner_id.phone', readonly=False)
    partner_mobile = fields.Char(related='partner_id.mobile', readonly=False)
    partner_zip = fields.Char(related='partner_id.zip', readonly=False)
    partner_street = fields.Char(related='partner_id.street', readonly=False)
    partner_city = fields.Char(related='partner_id.city', readonly=False)
    total_es = fields.Integer("Total Estimated", compute='_compute_estimated', store=True)

    @api.depends()
    def _compute_notes_count(self):
        for project in self:
            project.notes_count = len(project.notes_ids)

    def set_study(self):
        for pro in self:
            pro.write({'state': 'study'})

    def set_inprogress(self):
        for pro in self:
            pro.write({'state': 'inprogress'})

    def set_draft(self):
        for pro in self:
            pro.write({'state': 'draft'})

    def set_closed(self):
        for pro in self:
            pro.write({'state': 'closed'})

    def set_canceled(self):
        for pro in self:
            pro.write({'state': 'closed'})

    def view_notes(self):
        for rec in self:
            res = self.env.ref('construction.action_project_note_note')
            res = res.read()[0]
            res['domain'] = str([('project_id', 'in', rec.ids)])
        return res

    def project_to_stock_action(self):
        for rec in self:
            res = self.env.ref('stock.action_view_quants')
            res = res.read()[0]
            res['domain'] = str([('location_id', '=', '1')])
        return res

    def project_to_jobcost_action(self):
        job_cost = self.mapped('job_cost_ids')
        action = self.env.ref('construction.action_job_costing').read()[0]
        action['domain'] = [('id', 'in', job_cost.ids)]
        action['context'] = {'default_project_id': self.id, 'default_analytic_id': self.analytic_account_id.id,
                             'default_user_id': self.user_id.id}
        return action


class MaterialPlanning(models.Model):
    _name = 'material.plan'
    _description = 'Material Plan'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.description = self.product_id.name

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Integer('Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    material_task_id = fields.Many2one('project.task', 'Material Plan Task')


class ConsumedMaterial(models.Model):
    _name = 'consumed.material'
    _description = 'Consumed Material'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        self.description = self.product_id.name

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Integer('Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    consumed_task_material_id = fields.Many2one('project.task', string='Consumed Material Plan Task')


class ProjectPhase(models.Model):
    _name = 'project.phase'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _compute_task_count(self):
        phase_data = self.env['project.task'].read_group([('phase_id', 'in', self.ids)], ['phase_id'], ['phase_id'])
        result = dict((data['phase_id'][0], data['phase_id_count']) for data in phase_data)
        for phase in self:
            phase.task_count = result.get(phase.id, 0)

    def _compute_cost(self):
        for pro in self:
            amount = 0
            mes = self.env['act.materials'].search([('phase_id', '=', pro.id)])
            for cost in mes:
                amount += cost.total_material
            les = self.env['act.labours'].search([('phase_id', '=', pro.id)])
            for cost in les:
                amount += cost.total_labour
            aes = self.env['act.assets'].search([('phase_id', '=', pro.id)])
            for cost in aes:
                amount += cost.total_asset
            ees = self.env['act.expenses'].search([('phase_id', '=', pro.id)])
            for cost in ees:
                amount += cost.total_expense
            pro.total_act = amount

    def _compute_est(self):
        for pro in self:
            amount = 0
            mes = self.env['es.materials'].search([('phase_id', '=', pro.id)])
            for cost in mes:
                amount += cost.total_material
            les = self.env['es.labours'].search([('phase_id', '=', pro.id)])
            for cost in les:
                amount += cost.total_labour
            aes = self.env['es.assets'].search([('phase_id', '=', pro.id)])
            for cost in aes:
                amount += cost.total_asset
            ees = self.env['es.expenses'].search([('phase_id', '=', pro.id)])
            for cost in ees:
                amount += cost.total_expense
            pro.total_es = amount

    project_id = fields.Many2one('project.project', string="Project")
    name = fields.Char(string="Name", required=True)
    user_id = fields.Many2one('res.users', string="Assigned User")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    date_started = fields.Date('Actual Start Date')
    date_ended = fields.Date('Actual End Date')
    task_ids = fields.One2many(comodel_name='project.task', inverse_name='phase_id', string="Jop Orders")
    task_count = fields.Integer(compute='_compute_task_count', string="Jop Orders")
    material_plan_ids = fields.One2many('es.materials', 'phase_id', string='Estimated Materials')
    labour_plan_ids = fields.One2many('es.labours', 'phase_id', string='Estimated Labours')
    asset_plan_ids = fields.One2many('es.assets', 'phase_id', string='Estimated Equipments')
    exp_plan_ids = fields.One2many('es.expenses', 'phase_id', string='Estimated Overhead')
    state = fields.Selection([('draft', 'Draft'),
                              ('inprogress', 'In Progress'),
                              ('finished', 'Finished'),
                              ('canceled', 'Canceled'),
                              ('halted', 'Halted')], string="Status", readonly=True, default='draft')
    description = fields.Text(string='Description')
    total_es = fields.Integer("Total Estimated", compute='_compute_est')
    total_act = fields.Integer("Total Cost", compute='_compute_cost')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # def _compute_jobcost_count(self):
    #     jobcost = self.env['job.costing']
    #     job_cost_ids = self.mapped('job_cost_ids')
    #     for task in self:
    #         task.job_cost_count = jobcost.search_count([('id', 'in', job_cost_ids.ids)])

    @api.depends('picking_ids.requisition_line_ids')
    def _compute_stock_picking_moves(self):
        for rec in self:
            rec.ensure_one()
            rec.move_ids = self.env['material.purchase.requisition.line']
            for picking in rec.picking_ids:
                rec.move_ids = picking.requisition_line_ids.ids

    def total_stock_moves_count(self):
        for task in self:
            task.stock_moves_count = len(task.move_ids)

    def _compute_notes_count(self):
        for task in self:
            task.notes_count = len(task.notes_ids)

    def _compute_cost(self):
        for pro in self:
            amount = 0
            mes = self.env['act.materials'].search([('task_id', '=', pro.id)])
            for cost in mes:
                amount += cost.total_material
            les = self.env['act.labours'].search([('task_id', '=', pro.id)])
            for cost in les:
                amount += cost.total_labour
            aes = self.env['act.assets'].search([('task_id', '=', pro.id)])
            for cost in aes:
                amount += cost.total_asset
            ees = self.env['act.expenses'].search([('task_id', '=', pro.id)])
            for cost in ees:
                amount += cost.total_expense
            pro.total_act = amount

    def _compute_est(self):
        for pro in self:
            amount = 0
            mes = self.env['es.materials'].search([('task_id', '=', pro.id)])
            for cost in mes:
                amount += cost.total_material
            les = self.env['es.labours'].search([('task_id', '=', pro.id)])
            for cost in les:
                amount += cost.total_labour
            aes = self.env['es.assets'].search([('task_id', '=', pro.id)])
            for cost in aes:
                amount += cost.total_asset
            ees = self.env['es.expenses'].search([('task_id', '=', pro.id)])
            for cost in ees:
                amount += cost.total_expense
            pro.total_es = amount

    # job_cost_count = fields.Integer(compute='_compute_jobcost_count')
    # job_cost_ids = fields.One2many('job.costing', 'task_id')
    phase_id = fields.Many2one('project.phase', string="Phase")
    picking_ids = fields.One2many('material.purchase.requisition', 'task_id', string='Stock Pickings')
    move_ids = fields.Many2many('material.purchase.requisition.line', compute='_compute_stock_picking_moves',
                                store=True)
    material_plan_ids = fields.One2many('es.materials', 'task_id', string='Estimated Materials')
    labour_plan_ids = fields.One2many('es.labours', 'task_id', string='Estimated Labours')
    asset_plan_ids = fields.One2many('es.assets', 'task_id', string='Estimated Equipments')
    exp_plan_ids = fields.One2many('es.expenses', 'task_id', string='Estimated Overhead')
    consumed_material_ids = fields.One2many('consumed.material', 'consumed_task_material_id',
                                            string='Consumed Materials')
    stock_moves_count = fields.Integer(compute='total_stock_moves_count', string='# of Stock Moves', store=True)
    parent_task_id = fields.Many2one('project.task', string='Project Parent Task', readonly=True)
    child_task_ids = fields.One2many('project.task', 'parent_task_id', string='Child Tasks')
    notes_ids = fields.One2many('note.note', 'task_id', string='Notes Id')
    notes_count = fields.Integer(compute='_compute_notes_count', string="Notes")
    job_number = fields.Char(string="Task Number", copy=False)
    total_es = fields.Integer("Total Estimated", compute='_compute_est')
    total_act = fields.Integer("Total Cost", compute='_compute_cost')
    task_progress = fields.Float(string="Task Progress", default=0.0)

    def task_to_jobcost_action(self):
        job_cost = self.mapped('job_cost_ids')
        action = self.env.ref('construction.action_job_costing').read()[0]
        action['domain'] = [('id', 'in', job_cost.ids)]
        action['context'] = {'default_task_id': self.id, 'default_project_id': self.project_id.id,
                             'default_analytic_id': self.project_id.analytic_account_id.id,
                             'default_user_id': self.user_id.id}
        return action

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('project.task')
        name = vals.get('name')
        vals.update({
            'job_number': number,
        })
        if vals.get('phase_id'):
            phase_id = vals.get('phase_id')
            phase = self.env['project.phase'].search([('id', '=', phase_id)], limit=1)
            if phase:
                if vals.get('date_started'):
                    dt = fields.Date.from_string(vals.get('date_started'))
                    if fields.Date.from_string(phase.date_started) > fields.Date.from_string(vals.get('date_started')):
                        phase.update({'date_started': dt})
                if vals.get('date_finished'):
                    dt = vals.get('date_finished')
                    if fields.Date.from_string(phase.date_ended) < fields.Date.from_string(vals.get('date_finished')):
                        phase.update({'date_ended': dt})
                vals.update({
                    'name': phase.name + " " + name,
                })
        return super(ProjectTask, self).create(vals)

    def write(self, values):
        if self.phase_id:
            phase = self.phase_id
            if values.get('date_started'):
                dt = fields.Date.from_string(values.get('date_started'))
                if fields.Date.from_string(phase.date_started) > fields.Date.from_string(values.get('date_started')):
                    phase.update({'date_started': dt})
            if values.get('date_finished'):
                dt = values.get('date_finished')
                if fields.Date.from_string(phase.date_ended) < fields.Date.from_string(values.get('date_finished')):
                    phase.update({'date_ended': dt})
        return super(ProjectTask, self).write(values)

    def view_stock_moves(self):
        for rec in self:
            stock_move_list = []
            for move in rec.move_ids:
                # stock_move_list.append(move.id)
                stock_move_list += move.requisition_id.delivery_picking_id.move_lines.ids
        result = self.env.ref('stock.stock_move_action')
        action_ref = result or False
        result = action_ref.read()[0]
        result['domain'] = str([('id', 'in', stock_move_list)])
        return result

    def view_notes(self):
        for rec in self:
            res = self.env.ref('construction.action_task_note_note')
            res = res.read()[0]
            res['domain'] = str([('task_id', 'in', rec.ids)])
        return res

    def action_subtask(self):
        res = super(ProjectTask, self).action_subtask()
        res['context'].update({
            'default_parent_task_id': self.id,
        })
        return res


class Deductions(models.Model):
    _name = "deductions"
    _inherit = ['mail.thread']
    _description = "Project invoice deductions"

    name = fields.Char(string=_("Name"), required=True)
    account_id = fields.Many2one('account.account', string=_("Account"), required=True)
    value_type = fields.Selection([('percent', 'Percent'), ('fixed', 'Fixed Value')],
                                  string=_("Type"), required=True)
    value = fields.Float(required=True)


class ProjectDeductionsLines(models.Model):
    _name = "deductions.line"
    _description = "Project invoice deductions line"

    project_id = fields.Many2one('project.project', string=_("Project"))
    deduction_id = fields.Many2one('deductions', string=_("Account"))
    value = fields.Float(related='deduction_id.value')
    custom_value = fields.Float(string=_('Custom Value'))
    deducted = fields.Float(string=_("Deducted"))


class AssetWorkOrder(models.Model):
    _name = "asset.work.order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project asset work order"

    name = fields.Char(string=_("Name"), copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'),
                       tracking=True, track_visibility="onchange")
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string='Status',
                             readonly=True, index=True, copy=False, default='draft', tracking=True)
    date = fields.Date(string="Order Date", default=fields.Date.context_today, tracking=True,
                       track_visibility="onchange")
    project_id = fields.Many2one('project.project', tracking=True, track_visibility="onchange")
    employee_id = fields.Many2one('hr.employee', tracking=True, track_visibility="onchange")
    asset_order_ids = fields.One2many(comodel_name='asset.work.order.line', inverse_name='asset_order_id',
                                      tracking=True, track_visibility="onchange")
    notes = fields.Html(string=_("Notes"))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.work.order') or 'New'
        result = super(AssetWorkOrder, self).create(vals)
        return result

    def action_approve(self):
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_lines = all(
            float_is_zero(order_line.period, precision_digits=precision_digits) for order_line in
            self.asset_order_ids)
        if no_lines:
            raise UserError(_('You cannot validate order without lines.'))

        self.write({'state': 'approved'})

    def action_draft(self):
        self.write({'state': 'draft'})


class AssetWorkOrderLine(models.Model):
    _name = "asset.work.order.line"
    _description = "Project asset work order line"

    asset_order_id = fields.Many2one('asset.work.order')
    asset_id = fields.Many2one('account.asset', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', required=True, tracking=True)
    period_type = fields.Selection([('hour', 'Hours'), ('day', 'Days')], default='day',
                                   required=True, tracking=True)
    period = fields.Float(tracking=True, required=True, string=_("Period"))
    cost = fields.Float(string=_("Cost"), digits=dp.get_precision('Product Price'), readonly=True)

    @api.onchange('asset_id', 'period_type', 'period')
    def _onchange_asset_id(self):
        if self.asset_id:
            rent = 0
            if self.period_type == 'hour':
                rent = (self.asset_id.rent_per_day / 24) * self.period
            elif self.period_type == 'day':
                rent = self.asset_id.rent_per_day * self.period
            self.cost = rent


class AccountAsset(models.Model):
    _inherit = "account.asset"

    cost_per_day = fields.Float(string=_("Cost Per Day"))
    rent_per_day = fields.Float(string=_("Rent Per Day"))


class Note(models.Model):
    _inherit = 'note.note'

    @api.onchange('task_id')
    def onchange_task(self):
        for rec in self:
            rec.project_id = rec.task_id.project_id.id

    project_id = fields.Many2one('project.project', string='Construction Project')
    task_id = fields.Many2one('project.task', string='Task / Job Order')
    is_task = fields.Boolean(string='Is Job Order?')
    is_project = fields.Boolean(string='Is Project?')


class Product(models.Model):
    _inherit = 'product.product'

    boq_type = fields.Selection([('project_boq', 'Boq Line'),
                                ('eqp_machine', 'Machinery / Equipment'),
                                ('worker_resource', 'Worker / Resource'),
                                ('work_cost_package', 'Work Cost Package'),
                                ('subcontract', 'Subcontract')],
                                string='BOQ Type')


class ProjectPayments(models.Model):
    _name = 'project.payments'
    _description = "Project Payment Terms"

    name = fields.Char(string="Name", required=True)
    project_id = fields.Many2one("project.project")
    phase_id = fields.Many2one("project.phase")
    task_id = fields.Many2one("project.task")
    type = fields.Selection([('fixed', 'Fixed'), ('percent', 'Percent')])
    val = fields.Float(string="Value", default=0.0)
    paid = fields.Float(string="Paid", default=0.0)
    state = fields.Boolean(default=False)


class ProjectCrm(models.Model):
    _inherit = 'crm.lead'

    project_id = fields.Many2one("project.project")

    def send_whats_msg(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Whatsapp Message'),
            'res_model': 'whatsapp.message.wizard',
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_user_id': self.name, 'default_phone': self.phone},
        }
