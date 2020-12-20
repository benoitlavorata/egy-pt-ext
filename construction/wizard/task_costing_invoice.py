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
