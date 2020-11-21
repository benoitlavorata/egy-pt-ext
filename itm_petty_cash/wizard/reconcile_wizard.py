# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime as date
from odoo.exceptions import UserError
import time


class ReconcileWizard(models.TransientModel):
    _name = 'reconcile.wizard'
    
    name = fields.Char(string="Name")
    
    @api.model
    def default_get(self, vals):
        result = super(ReconcileWizard, self).default_get(vals)
        context = self.env.context
        cash_id = self.env['petty.cash'].browse(context.get('active_id'))
        line_amount = 0.0
        total_amount = 0.0
        for rec in cash_id:
            total_amount = rec.amount_received
            for line in rec.petty_cash_line_ids:
                if line.state == 'paid':
                    line_amount += line.amount
        if line_amount == total_amount:
            result.update({'name': "Your petty cash balance and paid amount are equals !"
                                   " Are you sure, you want to reconcile?"})
        else:
            diff_amount = total_amount - line_amount 
            result.update({'name': "Your petty cash balance and paid amount difference is " + str(diff_amount) + " Are you sure, you want to reconcile?"  })
        return result
    
    def accept_reconcile(self):
        context = self.env.context
        cash_id = self.env['petty.cash'].browse(context.get('active_id'))
        line_amount = 0.0
        for rec in cash_id:
            total_amount = rec.amount_received
            for line in rec.petty_cash_line_ids:
                line_amount += line.amount
            if line_amount == total_amount:
                rec.state = 'reconcile'
            else:
                diff_amount = total_amount - line_amount 
                rec.state = 'reconcile'
                payment_methods = rec.petty_journal_id.inbound_payment_method_ids or rec.petty_journal_id.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                payment_id = self.env['account.payment'].create({
                    'cash_id': rec.id,
                    'payment_type': 'transfer',
                    'payment_date': date.today(),
                    'internal_transfer_type': 'journal_to_journal',
                    'journal_id': rec.petty_journal_id.id,
                    'destination_journal_id': rec.journal_id.id,
                    'payment_method_id': payment_method_id.id,
                    'amount': diff_amount,
                    'communication':  self.env['ir.sequence'].next_by_code('petty.cash') or _('New')
                    })
                ctx = dict(self._context)
                ctx.update({'custom_payment_id': rec.id})
                payment_id.with_context(ctx).post()
                move_line_id = self.env['account.move.line'].search([('payment_id', '=', payment_id.id)])
                move_line_id.write({'cash_id': rec.id})
                return {'type': 'ir.actions.act_window_close'}
