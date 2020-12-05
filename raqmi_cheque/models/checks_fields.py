# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class CheckManagement(models.Model):
    _name = 'check.management'
    _description = 'Check'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    check_number = fields.Char(string=_("Check Number"), required=True, default="0")
    check_date = fields.Date(string=_("Check Date"), required=True)
    check_payment = fields.Date(string=_("Check Payment"), required=True)
    check_bank = fields.Many2one('res.bank', string=_('Check Bank'))
    dep_bank = fields.Many2one('res.bank', string=_('Deposit Bank'))
    amount = fields.Float(string=_('Check Amount'), digits=dp.get_precision('Product Price'))
    amount_reg = fields.Float(string=_("Check Regular Amount"), digits=dp.get_precision('Product Price'))
    open_amount_reg = fields.Float(string=_("Check Regular Open Amount"), digits=dp.get_precision('Product Price'))
    open_amount = fields.Float(string=_('Open Amount'), digits=dp.get_precision('Product Price'),
                               track_visibility='onchange')
    investor_id = fields.Many2one('res.partner', string=_("Partner"))
    check_id = fields.Integer(string=_("Check Id"))
    bank_deposit = fields.Many2one('res.bank', string=_("Deposit Bank"))
    type = fields.Selection(string="Type", selection=[('reservation', 'Reservation Installment'),
                                                      ('contracting', 'Contracting Installment'),
                                                      ('regular', 'Regular Installment'),
                                                      ('ser', 'Services Installment'),
                                                      ('garage', 'Garage Installment'),
                                                      ('mod', 'Modification Installment')],
                            required=True, translate=True, default="regular")
    state = fields.Selection(selection=[('holding', 'Holding'), ('deposited', 'Deposited'),
                                        ('approved', 'Approved'), ('rejected', 'Rejected'),
                                        ('returned', 'Returned'), ('handed', 'Handed'),
                                        ('debited', 'Debited'), ('canceled', 'Canceled'),
                                        ('cs_return', 'Customer Returned')],
                             translate=True, track_visibility='onchange')

    notes_rece_id = fields.Many2one('account.account')
    under_collect_id = fields.Many2one('account.account')
    notes_payable_id = fields.Many2one('account.account')
    under_collect_jour = fields.Many2one('account.journal')
    deposited_journal = fields.Many2one('account.journal')
    check_type = fields.Selection(selection=[('rece', 'Notes Receivable'), ('pay', 'Notes Payable')])
    check_state = fields.Selection(selection=[('active', 'Active'), ('suspended', 'Suspended')], default='active')
    check_from_check_man = fields.Boolean(string="Check Management", default=False)
    will_collection = fields.Date(string="Maturity Date", compute="_compute_days")
    will_collection_user = fields.Date(string="Bank Maturity Date", track_visibility='onchange')

    def _compute_days(self):
        d1 = datetime.strptime(str(self.check_date), '%Y-%m-%d')
        self.will_collection = d1 + datetime.timedelta(days=10)

    @api.model
    def create(self, vals):
        check_object = self.env['check.management'].search([('check_number', '=', self.check_number)])
        if 'amount' in vals:
            vals['open_amount'] = vals['amount']
        return super(CheckManagement, self).create(vals)

    def write(self, vals):
        for rec in self:
            if 'amount' in vals:
                rec.open_amount = vals['amount']
        return super(CheckManagement, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CheckManagement, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                           toolbar=toolbar, submenu=submenu)
        if 'fields' in res:
            if 'state' in res['fields']:
                if 'menu_sent' in self.env.context:
                    """if self.env.context['menu_sent'] in ('handed','debited'):
                        res['fields']['state']['selection'] = [('handed', 'Handed'), ('debited', 'Debited')]
                        if self.env.context['lang'] == 'ar_EG':
                            res['fields']['state']['selection'] = [('handed', 'مسلمة'), ('debited', 'محصلة')]
                    else:
                        res['fields']['state']['selection'] = [('holding', 'Holding'), ('deposited', 'Deposited'),
                         ('approved', 'Approved'), ('rejected', 'Rejected'),
                         ('returned', 'Returned'),('canceled', 'Canceled') ,('cs_return','Customer Returned')]
                        if self.env.context['lang'] == 'ar_EG':
                            res['fields']['state']['selection'] = [('holding', 'قابضة'), ('deposited', 'تحت التحصيل'),
                                                                ('approved', 'خالصة'), ('rejected', 'مرفوضة'),
                                                                ('returned', 'مرتجعة'), ('canceled', 'ملغاه'),
                                                                ('cs_return','مرتجع للعميل')]"""
        if 'toolbar' in res:
            if 'menu_sent' in self.env.context:
                if self.env.context['menu_sent'] == 'holding':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposited Checks':
                            del res['toolbar']['action'][j]
                            break
                    for i in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][i]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][i]
                            break
                    for i in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][i]['name'] == 'Company Return':
                            del res['toolbar']['action'][i]
                            break
                    for i in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][i]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][i]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'deposit':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'approved':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'rejected':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'returned':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'handed':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'debited':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'canceled':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
                if self.env.context['menu_sent'] == 'cs_return':
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Approve Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Reject Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Company Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Cancel Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Deposit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Debit Checks':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Customer Return':
                            del res['toolbar']['action'][j]
                            break
                    for j in range(len(res['toolbar']['action'])):
                        if res['toolbar']['action'][j]['name'] == 'Split-Merge':
                            del res['toolbar']['action'][j]
                            break
        return res
