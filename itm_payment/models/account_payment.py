# -*- coding: utf-8 -*-

from odoo import models, fields, api , _
from odoo.exceptions import UserError, ValidationError


# set internal transfer type in payment
class AccountPayment(models.Model):
    _inherit = 'account.payment'
     
    internal_transfer_type = fields.Selection(
        selection=[
            ('journal_to_journal', 'Journal to Journal'),
            ('journal_to_account', 'Journal to Account'),
            ('account_to_journal', 'Account to Journal')
        ],
        string="Internal Transfer Type", default='journal_to_journal'
    )
    account_to_id = fields.Many2one('account.account', string='Payment account')
    destination_account_from_id = fields.Many2one('account.account', string='Transfer to ')

    # set  journal as destination journal
    @api.onchange('journal_id', 'destination_journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            payment_methods_list = payment_methods.ids
            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            domain = {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}
            if self.env.context.get('active_model') == 'account.move':
                active_ids = self._context.get('active_ids')
                invoices = self.env['account.move'].browse(active_ids)
                self.amount = abs(
                    self._compute_payment_amount(invoices, self.currency_id, self.journal_id, self.payment_date))
            return {'domain': domain}
        else:
            self.journal_id = self.destination_journal_id
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            payment_methods_list = payment_methods.ids
            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            domain = {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}
            if self.env.context.get('active_model') == 'account.move':
                active_ids = self._context.get('active_ids')
                invoices = self.env['account.move'].browse(active_ids)
                self.amount = abs(
                    self._compute_payment_amount(invoices, self.currency_id, self.journal_id, self.payment_date))
            return {'domain': domain}
        return {}

    # set  journal as destination journal in move line
    def _get_liquidity_move_line_vals(self, amount):
        name = self.name
        if not self.destination_journal_id :
            if self.internal_transfer_type == 'journal_to_account' :
                custom_destination_journal_id = self.destination_account_from_id
        else:
            custom_destination_journal_id = self.destination_journal_id

        if self.payment_type == 'transfer':
            name = _('Transfer to %s') % custom_destination_journal_id.name
        vals = {
            'name': name,
            'account_id': self.payment_type in ('outbound', 'transfer') and self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id,
            'payment_id': self.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }

        # If the journal has a currency specified, the journal item need to be expressed in this currency
        if self.journal_id.currency_id and self.currency_id != self.journal_id.currency_id:
            amount = self.currency_id.with_context(date=self.payment_date).compute(amount, self.journal_id.currency_id)
            debit, credit, amount_currency, dummy = self.env['account.move.line'].with_context(date=self.payment_date).compute_amount_fields(amount, self.journal_id.currency_id, self.company_id.currency_id)
            vals.update({
                'amount_currency': amount_currency,
                'currency_id': self.journal_id.currency_id.id,
            })

        return vals

    # set journals  in move line
    def _create_transfer_entry(self, amount):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        if self.internal_transfer_type == 'journal_to_account' :
            custom_destination_journal_id = self.destination_account_from_id
            custom_journal_id = self.journal_id
        if self.internal_transfer_type == 'account_to_journal' :
            custom_destination_journal_id = self.destination_journal_id
            custom_journal_id = self.destination_journal_id
        if self.internal_transfer_type == 'journal_to_account' or  self.internal_transfer_type == 'account_to_journal':
            amount_currency = custom_destination_journal_id.currency_id and self.currency_id.with_context(date=self.payment_date).compute(amount, self.destination_journal_id.currency_id) or 0
            dst_move = self.env['account.move'].create(self._get_move_vals(custom_journal_id))
            dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)
            dst_liquidity_aml_dict.update({
                'name': _('Transfer from %s') % custom_journal_id.name,
                'account_id': custom_destination_journal_id.id,
                'currency_id': custom_destination_journal_id.currency_id.id,
                'payment_id': self.id,
                'journal_id': custom_journal_id.id})
            aml_obj.create(dst_liquidity_aml_dict)

            transfer_debit_aml_dict = self._get_shared_move_line_vals(credit, debit, 0, dst_move.id)
            transfer_debit_aml_dict.update({
                'name': self.name,
                'payment_id': self.id,
                'account_id': self.company_id.transfer_account_id.id,
                'journal_id': custom_journal_id.id})
            if self.currency_id != self.company_id.currency_id:
                transfer_debit_aml_dict.update({
                    'currency_id': self.currency_id.id,
                    'amount_currency': -self.amount,
                })
            transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
            dst_move.post()
            return transfer_debit_aml
        else:
            return super(AccountPayment, self)._create_transfer_entry(amount)
