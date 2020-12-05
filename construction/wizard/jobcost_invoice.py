# -*- coding: utf-8 -*-

import time
from odoo import models,fields, api, _
from odoo.exceptions import ValidationError, UserError


class JobcostInvoice(models.TransientModel):
    _name = 'jobcost.invoice'
    
    partner_id = fields.Many2one('res.partner', readonly=True, required=True, string='Customer')
    project_id = fields.Many2one('project.project', readonly=True, required=True, string='Project')
    boq_id = fields.Many2one('project.boq', readonly=True, required=True, string='Project')
    invoice_date_from = fields.Date('From', default=fields.date.today(), required=True)
    invoice_date_to = fields.Date('To', required=True)
    boq_lines = fields.One2many(related='boq_id.poq_line_ids')
    ded_lines = fields.One2many(related='project_id.project_deduction_line_ids')
    
    @api.model
    def default_get(self, fields):
        rec = super(JobcostInvoice, self).default_get(fields)
        active_id = self.env['project.project'].browse(self._context.get('active_id'))
        partner = active_id.partner_id
        project = active_id.id
        boq = active_id.boq_id
        rec.update({
                'partner_id': partner.id,
                'project_id': project,
                'boq_id': boq.id,
        })
        return rec
    
    def create_jobcost_invoice(self):
        timenow = time.strftime('%Y-%m-%d')
        for rec in self:
            acc = rec.partner_id.property_account_receivable_id
            dacc = rec.partner_id.property_account_payable_id
            journal = 1
            debit_vals = {
                'name': "loan_name",
                'account_id': acc.id,
                'journal_id': journal,
                'date': timenow,
                'debit': 0.0,
                'credit': 0.0,

            }
            credit_vals = {
                'name': 'loan_name',
                'account_id': dacc.id,
                'journal_id': journal,
                'date': timenow,
                'debit': 0.0,
                'credit': 0.0,
            }
            vals = {
                'narration': 'loan_name',
                'ref': 'reference',
                'journal_id': journal,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            # move.post()

#         active_id = self._context.get('active_id')
#         job_costing = self.env['job.costing'].browse(active_id)
#         invoice_obj = self.env['account.move']
#         invoice_line_obj = self.env['account.move.line']
#         invoice_list = []
#         for invoices in job_costing.invoice_ids:
#             invoice_list.append(invoices.id)
#         for rec in self:
#             invoice_ids = []
#             partner_id = rec.partner_id
#             invoice_name = job_costing.name
#             currency_id = job_costing.currency_id
#             material_line_ids = []
#
#             if rec.labour_invoice != True and rec.material_invoice != True and rec.overhead_invoice != True:
#                 raise ValidationError('Invoice not Created.')
#             if rec.material_invoice:
#                 material_ids = job_costing.job_cost_line_ids
#                 for material_id in material_ids:
#                     invoice_lst = []
#                     if job_costing.billable_method == 'based_on_avbq':
#                         quantity = material_id.actual_invoice_quantity - material_id.invoice_qty
#                     elif job_costing.billable_method == 'based_on_apq':
#                         quantity = material_id.actual_quantity - material_id.invoice_qty
#                     else:
#                         quantity = material_id.manual_invoice_qty
#                     if material_id.billable == 'billable' and quantity > 0.0:
#                         for invoice_line_id in material_id.invoice_line_ids:
#                             invoice_lst.append(invoice_line_id.id)
#                         account_id = False
#                         if material_id.product_id.id:
#                             account_id = material_id.product_id.property_account_income_id.id or material_id.product_id.categ_id.property_account_income_categ_id.id
# #                        if not account_id:
# #                            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
# #                            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
#                         if not account_id:
#                             raise UserError(
#                                 _('There is no income account defined for this product: "%s".'
#                                   ' You may have to install a chart of account from Accounting app,'
#                                   ' settings menu.') % (material_id.product_id.name,))
#                         product_id = material_id.product_id
#                         name = material_id.description
#                         amount = material_id.sale_price
# #                        quantity = material_id.actual_invoice_quantity - material_id.invoice_qty
#                         uom_id = material_id.uom_id
#
#                         material_vals_line = {
#                             'name': name,
#                             'account_id': account_id,
#                             'price_unit': amount,
#                             'quantity': quantity,
#                             'uom_id': uom_id.id,
#                             'product_id': product_id.id,
#                         }
#
#                         material_line_id = invoice_line_obj.create(material_vals_line)
#                         material_line_ids.append(material_line_id.id)
#                         invoice_lst.append(material_line_id.id)
#                         material_id.invoice_line_ids = [(6, 0, invoice_lst)]
#
#                 if not material_line_ids:
#                     raise ValidationError('No Material lines found to create invoice.')
#
#             material_vals = {
#                     'account_id': job_costing.partner_id.property_account_receivable_id.id,
#                     'partner_id': partner_id.id,
#                     'invoice_line_ids': [(6, 0, material_line_ids)],
#                     'currency_id': currency_id.id,
#                     'job_cost_id': job_costing.id,
#                     'date_invoice': rec.invoice_date,
#             }
#             invoice_id = invoice_obj.create(material_vals)
#             invoice_ids.append(invoice_id.id)
#             invoice_list.append(invoice_id.id)
#
#             job_costing.invoice_ids = [(6, 0, invoice_list)]
#             action = self.env.ref('account.action_invoice_tree1')
#             action = action.read()[0]
#             action['domain'] = "[('id','in',[" + ','.join(map(str, invoice_ids)) + "])]"
#             return action
