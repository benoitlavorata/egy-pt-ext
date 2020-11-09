'''
Created on 02 August 2019

@author: Dennis
'''
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger("_name_")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    project_related = fields.Boolean(string="A Project Related?", default=True, states=READONLY_STATES)
    purchase_request_merge_ids = fields.Many2many('sprogroup.purchase.request', 'requests_request_po_rel', 'f1', 'f2', string="Purchase Request Merged")
    sent_date = fields.Datetime(string="Sent Date")
    received_date = fields.Datetime(string="Quotation Received from Date")

    def get_print_date(self):
        today = datetime.now() + timedelta(hours=8)
        return today.strftime(DT)

    def get_print_user(self):
        user = self.env['res.users'].browse(self._uid)
        return user.name

    def write(self, vals):
        if vals.get('state') == 'sent':
            vals['sent_date'] = datetime.now()
        return super(PurchaseOrder, self).write(vals)


    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)
        try:
            res['project_related'] = self.env[self._context.get('active_model')].browse(self._context.get('active_id')).project_related
        except: pass
        return res

    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_project_related'] = self.project_related
        return result

    def button_confirm(self):
        self.check_order_parameters()
        return super(PurchaseOrder, self).button_confirm()

    def task_material_status(self, order_item):
        budget_item = self.env['project.material.consumption'].search([('task_id', '=', order_item.task_id.id), ('product_id', '=', order_item.product_id.id)], limit=1)
        if not budget_item[:1]:
            raise ValidationError(_("You are trying to purchase %s which is not Included in %s's BOM\nPlease request an Engeneering Change Order. Or you may log an Annotation to the concerned OrderLine to Proceed."%(order_item.name, order_item.task_id.name)))
        task_po_line = self.env['purchase.order.line'].search([('product_id', '=', order_item.product_id.id), ('task_id', '=', order_item.task_id.id), ('order_id.state', 'in', ['purchase','done', 'confirmed'])])
        total_po_qty = sum(line.product_qty for line in self.env['purchase.order.line'].search([('product_id', '=', order_item.product_id.id), ('task_id', '=', order_item.task_id.id), ('order_id.state', 'in', ['purchase','done', 'confirmed'])]))
        if budget_item[0].estimated_qty < (order_item.product_qty + total_po_qty):
            raise ValidationError(_("You are trying to purchase %s which would exceed in total (purchased + current purchase) the budgeted Quantity in %s's BOM\nPlease request an Engeneering Change Order. Or you may log an Annotation to the concerned OrderLine to Proceed."%(order_item.name, order_item.task_id.name)))
        return True

    def check_material_in_bom(self, order_item):
        material = self.env['boq.material'].search([('boq_id.task_id', '=', order_item.task_id.id), ('product_id', '=', order_item.product_id.id), ('boq_id.state', 'in', ['approved'])], limit=1)
        if not material[:1]:
            raise ValidationError(_("You are trying to purchase %s which is not Included in %s's BOM\nPlease request an Engeneering Change Order. Or you may log an Annotation to the concerned OrderLine to Proceed."%(order_item.name, order_item.task_id.name)))
        if order_item.price_unit > material[0].unit_rate:
            raise ValidationError(_("You are trying to purchase %s where the Price is Greater than the canvased price per quantity in %s's BOM\nPlease request an Engeneering Change Order. Or you may log an Annotation to the concerned OrderLine to Proceed."%(order_item.name, order_item.task_id.name)))
        if material[0].qty < order_item.product_qty:
            raise ValidationError(_("You are trying to purchase %s which would exceed the budgeted Quantity in %s's BOM\nPlease request an Engeneering Change Order. Or you may log an Annotation to the concerned OrderLine to Proceed."%(order_item.name, order_item.task_id.name)))
        self.task_material_status(order_item)
        return True

    def check_order_parameters(self):
        if not any(line.state != 'cancel' for line in self.order_line):
            raise Warning(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
        msg = ""
        material_current_po = 0.0
        labor_current_po = 0.0
        equipment_current_po = 0.0
        service_current_po = 0.0
        overhead_current_po = 0.0
        current_po = []
        for i in self.order_line:
            if i.task_id and i.project_boq_category:
                exceeding_budget = False
                task_po_line = self.env['purchase.order.line'].search([('task_id', '=', i.task_id.id), ('order_id.state', 'in', ['purchase','done', 'confirmed'])])
                material_po = 0.0
                labor_po = 0.0
                equipment_po = 0.0
                service_po = 0.0
                overhead_po = 0.0
                for line in task_po_line:
                    if line.project_boq_category in ['meterial']:
                        material_po +=line.price_subtotal
                    elif line.project_boq_category in ['labor']:
                        labor_po +=line.price_subtotal
                    elif line.project_boq_category in ['equipment']:
                        equipment_po +=line.price_subtotal
                    elif line.project_boq_category in ['subcon']:
                        service_po +=line.price_subtotal
                    elif line.project_boq_category in ['overhead']:
                        overhead_po +=line.price_subtotal

                if i.project_boq_category in ['meterial'] and i.task_id.project_id.monitor_boq_item_qty_and_price:
                    if not i.annotation:
                        self.check_material_in_bom(i)
                if i.task_id.project_id.monitor_boq_category_budget:
                    found = False
                    for rec in current_po:
                        if rec[2].get('task_id') == i.task_id.id and rec[2].get('project_boq_category'):
                            rec[2]['current_po_amount'] = rec[2].get('current_po_amount') + i.price_subtotal
                            found = True
                    if not found:
                        budget = 0.0
                        budget_balance = 0.0
                        previous_po = 0.0
                        if i.project_boq_category in ['meterial']:
                            previous_po = material_po
                            budget_balance = i.task_id.material_balance
                            budget = i.task_id.material_budget
                        elif i.project_boq_category in ['labor']:
                            previous_po = labor_po
                            budget_balance = i.task_id.labor_balance
                            budget = i.task_id.labor_budget
                        elif i.project_boq_category in ['equipment']:
                            previous_po = equipment_po
                            budget_balance = i.task_id.equipment_balance
                            budget = i.task_id.equipment_budget
                        elif i.project_boq_category in ['subcon']:
                            previous_po = service_po
                            budget_balance = i.task_id.service_balance
                            budget = i.task_id.service_budget
                        elif i.project_boq_category in ['overhead']:
                            previous_po = overhead_po
                            budget_balance = i.task_id.overhead_balance
                            budget = i.task_id.overhead_budget
                        current_po.append([0, 0, {
                                    'task_id': i.task_id.id,
                                    'name': '%s/%s/%s'%(i.task_id.project_id.name, i.task_id.phase_id.name, i.task_id.name),
                                    'task_budget': i.task_id.task_budget,
                                    'project_boq_category': i.project_boq_category,
                                    'category_budget': budget,
                                    'budget_balance': budget_balance,
                                    'previous_po': previous_po,
                                    'current_po_amount': i.price_subtotal,
                                    'budget_deferences': False,
                                }])
                if i.task_id.project_id.monitor_budget_task_level:
                    current_task_total_po_amount = 0.0
                    for line in self.order_line:
                        if line.task_id.id == i.task_id.id:
                            current_task_total_po_amount += line.price_subtotal
                    previous_task_total_po_amount = sum([material_po,labor_po, equipment_po, service_po, overhead_po])
                    if (previous_task_total_po_amount + current_task_total_po_amount) > i.task_id.task_budget or (i.task_id.total_expense + current_task_total_po_amount) > i.task_id.task_budget:
                        msg += 'Your Task Budget is %d. And the total of your previous PO is %s plus the current %d is %d \nPlease adjust the current Purchase Order or the task Budgeted Amount to be able to confirm this PO.'%(i.task_id.task_budget, previous_task_total_po_amount, current_task_total_po_amount,(previous_task_total_po_amount + current_task_total_po_amount))

        for rec in current_po:
            # task_po_line = self.env['purchase.order.line'].search([('task_id', '=', rec[2].get('task_id')), ('order_id.state', 'in', ['purchase', 'done', 'confirmed'])])
            # raise ValidationError(_('total: %s\n\n\n%s'%(sum(x.price_unit for x in task_po_line), str(rec[2].get('task_id')))))
            if rec[2].get('current_po_amount') > rec[2].get('budget_balance'):
                rec[2]['budget_deferences'] = True
                msg += "%s %s Budget Balance %s and is not sufficient to purchase worth %d. Please request for a budget adjustment.\n"%(rec[2].get('name'), (rec[2].get('project_boq_category')).title() , rec[2].get('budget_balance'), rec[2].get('current_po_amount'))

            elif (rec[2].get('current_po_amount') + rec[2].get('previous_po')) > rec[2].get('category_budget'):
                rec[2]['budget_deferences'] = True
                msg += "Task: %s. Your accumulated Purchase (previous) %d + (current) %d = %d is not sufficient for the alloted budget %d.\n"%(rec[2].get('name'), rec[2].get('previous_po'), rec[2].get('current_po_amount'), (rec[2].get('previous_po') + rec[2].get('current_po_amount')), rec[2].get('category_budget'))
        if msg:
                raise ValidationError(_(msg))
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('account_analytic_id')
    def _get_project_value(self):
        for i in self:
            project = i.env['project.project'].search([('analytic_account_id','=', i.account_analytic_id.id)], limit=1)
            if project[:1]:
                i.project_id = project.id

    project_id = fields.Many2one('project.project', string="Project", store=True, compute="_get_project_value")
    phase_id = fields.Many2one('project.phase', string="Phase", domain="[('project_id.analytic_account_id', '=', account_analytic_id)]")
    task_id = fields.Many2one('project.task', string="Task")
    project_boq_category = fields.Selection([
            ('meterial', 'Material'),
            ('subcon', 'Subcontractor'),
            # ('labor', 'Labor'),
            ('equipment', 'Equipment'),
            ('overhead', 'Overheads')], string="Category")
    annotation = fields.Text(string="Annotation")
    date = fields.Date(string="Date Order", store=True, compute="_get_po_date")
    state = fields.Selection([
            ('draft', 'RFQ'),
            ('sent', 'RFQ Sent'),
            ('to approve', 'To Approve'),
            ('purchase', 'Purchase Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled')
        ], string='Status', store=True, compute='_get_po_status')
    invoices = fields.Text(string="Invoices", compute="_get_invoices")

    def _get_invoices(self):
        for i in self:
            invoices = ''
            for line in i.invoice_lines:
                invoices += '%s (%s)\n'%(line.invoice_id.number, (line.invoice_id.state).title())

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

    @api.depends('date_order')
    def _get_po_date(self):
        for i in self:
            if i.date_order:
                i.date = i.date_order.strftime(DT)

    @api.depends('order_id', 'order_id.state')
    def _get_po_status(self):
        for i in self:
            i.state = i.order_id.state

class SprogroupPurchaseRequest(models.Model):
     _inherit = 'sprogroup.purchase.request'

     analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
     project_id = fields.Many2one('project.project', string="Project", domain="[('analytic_account_id', '=', analytic_account_id)]")
     phase_id = fields.Many2one('project.phase', string="Phase", domain="[('project_id', '=', project_id)]")
     task_id = fields.Many2one('project.task', string="Task", domain="[('phase_id', '=', phase_id)]")

     def generate_report(self):
         return self.env.ref('construction_purchase.purchase_requesition_report').report_action(self)


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    project_related = fields.Boolean(string="A Project Related?")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")

class PurchaseRequisitionline(models.Model):
    _inherit = 'purchase.requisition.line'

    project_id = fields.Many2one('project.project', string="Project")
    phase_id = fields.Many2one('project.phase', string="Phase")
    task_id = fields.Many2one('project.task', string="Task")
    project_boq_category = fields.Selection([
                                        ('meterial', 'Material'),
                                        ('subcon', 'Subcontractor'),
                                        # ('labor', 'Labor'),
                                        ('equipment', 'Equipment'),
                                        ('overhead', 'Overheads')], string="Category")

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        res = super(PurchaseRequisitionline, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['phase_id'] = self.phase_id.id
        res['task_id'] = self.task_id.id
        res['project_boq_category'] = self.project_boq_category
        return res
