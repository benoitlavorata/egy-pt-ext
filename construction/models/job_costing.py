# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class JobType(models.Model):
    _name = 'job.type'
    _description = 'Job Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    job_type = fields.Selection(selection=[
            ('material', 'Material'),
            ('labour', 'Labour'),
            ('overhead', 'Overhead')],
        string='Type',
        required=True,
    )


class JobCosting(models.Model):
    _name = 'job.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Job Costing"
    _rec_name = 'number'

    def _invocie_count(self):
        invoice_obj = self.env['account.move']
        for cost_sheet in self:
            cost_sheet.invoice_count = invoice_obj.search_count([('job_cost_id', '=', cost_sheet.id)])

    @api.model
    def create(self,vals):
        number = self.env['ir.sequence'].next_by_code('job.costing')
        vals.update({
            'number': number,
        })
        return super(JobCosting, self).create(vals) 

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise Warning(_('You can not delete Job Cost Sheet which is not draft or cancelled.'))
        return super(JobCosting, self).unlink()

    @api.depends('job_cost_line_ids', 'job_cost_line_ids.product_qty', 'job_cost_line_ids.cost_price')
    def _compute_material_total(self):
        for rec in self:
            rec.material_total = sum([(p.product_qty * p.cost_price) for p in rec.job_cost_line_ids])

    @api.depends('job_labour_line_ids', 'job_labour_line_ids.hours', 'job_labour_line_ids.cost_price')
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.hours * p.cost_price) for p in rec.job_labour_line_ids])

    @api.depends('job_overhead_line_ids', 'job_overhead_line_ids.product_qty', 'job_overhead_line_ids.cost_price')
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([(p.product_qty * p.cost_price) for p in rec.job_overhead_line_ids])

    @api.depends('material_total', 'labor_total', 'overhead_total')
    def _compute_jobcost_total(self):
        for rec in self:
            rec.jobcost_total = rec.material_total + rec.labor_total + rec.overhead_total

    def _purchase_order_line_count(self):
        purchase_order_lines_obj = self.env['purchase.order.line']
        for order_line in self:
            order_line.purchase_order_line_count = purchase_order_lines_obj.search_count([('job_cost_id','=',order_line.id)])
    
    def _job_costsheet_line_count(self):
        job_costsheet_lines_obj = self.env['job.cost.line']
        for jobcost_sheet_line in self:
            jobcost_sheet_line.job_costsheet_line_count = job_costsheet_lines_obj.search_count([('direct_id','=',jobcost_sheet_line.id)])

    def _timesheet_line_count(self):
        hr_timesheet_obj = self.env['account.analytic.line']
        for timesheet_line in self:
            timesheet_line.timesheet_line_count = hr_timesheet_obj.search_count([('job_cost_id', '=', timesheet_line.id)])

    def _account_invoice_line_count(self):
        account_invoice_lines_obj = self.env['account.move.line']
        for invoice_line in self:
            invoice_line.account_invoice_line_count = account_invoice_lines_obj.search_count([('job_cost_id', '=', invoice_line.id)])

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for rec in self:
            rec.analytic_id = rec.project_id.analytic_account_id.id

    number = fields.Char(readonly=True, default='New', copy=False)
    name = fields.Char(required=True, copy=True, default='New', string='Name')
    notes_job = fields.Text(required=False, copy=True, string='Job Cost Details')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user,  string='Created By', readonly=True)
    description = fields.Char(string='Description')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Company', readonly=True)
    project_id = fields.Many2one('project.project', string='Project')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    contract_date = fields.Date(string='Contract Date')
    start_date = fields.Date(string='Create Date', readonly=True, default=fields.Date.today())
    complete_date = fields.Date(string='Closed Date', readonly=True)
    material_total = fields.Float(string='Total Material Cost', compute='_compute_material_total', store=True)
    labor_total = fields.Float(string='Total Labour Cost', compute='_compute_labor_total', store=True)
    overhead_total = fields.Float(string='Total Overhead Cost', compute='_compute_overhead_total', store=True)
    jobcost_total = fields.Float(string='Total Cost', compute='_compute_jobcost_total', store=True)
    job_cost_line_ids = fields.One2many('job.cost.line', 'direct_id', string='Direct Materials', copy=False,
                                        domain=[('job_type', '=', 'material')])
    job_labour_line_ids = fields.One2many('job.cost.line', 'direct_id', string='Direct Labours', copy=False,
                                          domain=[('job_type', '=', 'labour')])
    job_overhead_line_ids = fields.One2many('job.cost.line', 'direct_id', string='Direct Overheads',
                                            copy=False, domain=[('job_type', '=', 'overhead')])
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    state = fields.Selection(
        selection=[
                    ('draft', 'Draft'),
                    ('confirm', 'Confirmed'),
                    ('approve', 'Approved'),
                    ('done', 'Done'),
                    ('cancel', 'Canceled')
                  ], string='State', track_visibility='onchange', default='draft')
    task_id = fields.Many2one('project.task', string='Task')
    so_number = fields.Char(string='Sale Reference')
    purchase_order_line_count = fields.Integer(compute='_purchase_order_line_count')
    job_costsheet_line_count = fields.Integer(compute='_job_costsheet_line_count')
    purchase_order_line_ids = fields.One2many("purchase.order.line", 'job_cost_id')
    timesheet_line_count = fields.Integer(compute='_timesheet_line_count')
    timesheet_line_ids = fields.One2many('account.analytic.line', 'job_cost_id')
    account_invoice_line_count = fields.Integer(compute='_account_invoice_line_count')
    account_invoice_line_ids = fields.One2many('account.move.line', 'job_cost_id')
    
    def action_draft(self):
        for rec in self:
            rec.write({
                'state' : 'draft',
            })
    
    def action_confirm(self):
        for rec in self:
            rec.write({
                'state': 'confirm',
            })
        
    def action_approve(self):
        for rec in self:
            rec.write({
                'state': 'approve',
            })
    
    def action_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'complete_date': date.today(),
            })
        
    def action_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancel',
            })

    def action_view_purchase_order_line(self):
        self.ensure_one()
        purchase_order_lines_obj = self.env['purchase.order.line']
        cost_ids = purchase_order_lines_obj.search([('job_cost_id', '=', self.id)]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order Line',
            'res_model': 'purchase.order.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
        }
        return action
        
    def action_view_hr_timesheet_line(self):
        hr_timesheet = self.env['account.analytic.line']
        cost_ids = hr_timesheet.search([('job_cost_id','=',self.id)]).ids
        action = self.env.ref('hr_timesheet.act_hr_timesheet_line').read()[0]
        action['domain'] = [('id', 'in', cost_ids)]
        return action
    
    def action_view_jobcost_sheet_lines(self):
        jobcost_line = self.env['job.cost.line']
        cost_ids = jobcost_line.search([('direct_id','=',self.id)]).ids
        action = self.env.ref('construction.action_job_cost_line_custom').read()[0]
        action['domain'] = [('id', 'in', cost_ids)]
        ctx = 'context' in action and action['context'] and eval(action['context']).copy() or {}
        ctx.update(create=False)
        ctx.update(edit=False)
        ctx.update(delete=False)
        action['context'] = ctx
        return action
        
    def action_view_vendor_bill_line(self):
        account_invoice_lines_obj = self.env['account.move.line']
        cost_ids = account_invoice_lines_obj.search([('job_cost_id','=',self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Account Invoice Line',
            'res_model': 'account.move.line',
            'res_id': self.id,
            'domain': "[('id','in',[" + ','.join(map(str, cost_ids)) + "])]",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target' : self.id,
            'context': {
                'create': False,
                'edit': False,
            }
        }

    invoice_ids = fields.One2many('account.move', 'job_cost_id', store=True)
    invoice_count = fields.Integer(compute="_invocie_count")
    billable_method = fields.Selection(
        string='Customer Invoice Billable Method',
        selection=[('based_on_apq', 'Based On Actual Purchase Qty'),
                   ('based_on_avbq', 'Based On Actual Vendor Bill Qty'),
                   ('based_on_mi', 'Based On Manual Invoice')],
        required=True,
        default='based_on_avbq'
    )

    def action_view_invoice(self):
        invoice_lst = []
        for invoice in self.invoice_ids:
            invoice_lst.append(invoice.id)
        action = self.env.ref('account.action_invoice_tree1')
        action = action.read()[0]
        action['domain'] = "[('id','in',[" + ','.join(map(str, invoice_lst)) + "])]"

        return action


class JobCostLine(models.Model):
    _name = 'job.cost.line'
    _description = 'Job Cost Line'
    _rec_name = 'description'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.product_qty = 1.0
            rec.uom_id = rec.product_id.uom_id.id
            rec.cost_price = rec.product_id.standard_price
            rec.sale_price = rec.product_id.lst_price

    @api.depends('product_qty', 'hours', 'cost_price', 'direct_id')
    def _compute_total_cost(self):
        for rec in self:
            if rec.job_type == 'labour':
                rec.product_qty = 0.0
                rec.total_cost = rec.hours * rec.cost_price
            else:
                rec.hours = 0.0
                rec.total_cost = rec.product_qty * rec.cost_price

    @api.depends('purchase_order_line_ids', 'purchase_order_line_ids.product_qty',
                 'purchase_order_line_ids.order_id.state')
    def _compute_actual_quantity(self):
        for rec in self:
            rec.actual_quantity = sum(
                [p.order_id.state in ['purchase', 'done'] and p.product_qty for p in rec.purchase_order_line_ids])

    @api.depends('timesheet_line_ids', 'timesheet_line_ids.unit_amount')
    def _compute_actual_hour(self):
        for rec in self:
            rec.actual_hour = sum([p.unit_amount for p in rec.timesheet_line_ids])

    @api.depends('account_invoice_line_ids', 'account_invoice_line_ids.quantity',
                 'account_invoice_line_ids.move_id.state',
                 'account_invoice_line_ids.move_id.invoice_payment_state')
    def _compute_actual_invoice_quantity(self):
        for rec in self:
            rec.actual_invoice_quantity = sum([p.quantity or 0.0 for p in rec.account_invoice_line_ids if
                                               p.move_id.state in ['posted'] or p.move_id.invoice_payment_state in [
                                                   'paid']])

    direct_id = fields.Many2one('job.costing', string='Task Costing')
    product_id = fields.Many2one('product.product', string='Product', copy=False, required=True)
    description = fields.Char(string='Description', copy=False)
    reference = fields.Char(string='Reference', copy=False)
    date = fields.Date(string='Date', required=True, copy=False)
    product_qty = fields.Float(string='Planned Qty', copy=False)
    uom_id = fields.Many2one('uom.uom', string='Uom')
    cost_price = fields.Float(string='Cost / Unit', copy=False)
    total_cost = fields.Float(string='Cost Price Sub Total', compute='_compute_total_cost', store=True)
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    job_type_id = fields.Many2one('job.type', string='Job Type')
    job_type = fields.Selection(selection=[('material', 'Material'),
                                           ('labour', 'Labour'),
                                           ('overhead', 'Overhead')], string="Type", required=True)
    basis = fields.Char(string='Basis')
    hours = fields.Float(string='Hours')
    purchase_order_line_ids = fields.One2many('purchase.order.line', 'job_cost_line_id')
    timesheet_line_ids = fields.One2many('account.analytic.line', 'job_cost_line_id')
    account_invoice_line_ids = fields.One2many('account.move.line', 'job_cost_line_id')
    actual_quantity = fields.Float(string='Actual Purchased Quantity',
                                   compute='_compute_actual_quantity')
    actual_invoice_quantity = fields.Float(string='Actual Vendor Bill Quantity',
                                           compute='_compute_actual_invoice_quantity')
    actual_hour = fields.Float(string='Actual Timesheet Hours', compute='_compute_actual_hour')

    @api.model
    def _default_billable(self):
        rec = self._context.get('default_job_type')
        if rec == 'overhead':
            billable = 'not_billable'
        else:
            billable = 'billable'

        return billable

    def _compute_invoice_qty(self):
        for rec in self:
            if rec.job_type_id.job_type != 'labour':
                rec.invoice_qty = 0.0
                qty = 0.0
                for line in rec.invoice_line_ids:
                    qty += line.quantity
                    rec.invoice_qty = qty

    def _compute_invoice_hour(self):
        for rec in self:
            if rec.job_type_id.job_type == 'labour':
                rec.invoice_hours = 0.0
                hour = 0.0
                for line in rec.invoice_line_ids:
                    hour += line.quantity
                    rec.invoice_hours = hour

    billable = fields.Selection(
        selection=[('billable', 'Billable'),
                   ('not_billable', 'Not Billable'),
                   ],
        string="Is Billable",
        default=_default_billable,
    )
    invoice_line_ids = fields.Many2many('account.move.line')
    invoice_qty = fields.Float('Customer Invoiced Qty', compute="_compute_invoice_qty")
    invoice_hours = fields.Float('Invoiced Hour', compute="_compute_invoice_hour")
    manual_invoice_qty = fields.Float('Manual Invoiced Qty')
    manual_invoice_hours = fields.Float('Manual Invoiced Hour')
    sale_price = fields.Float(string='Sale Price / Unit', copy=False)
