# -*- coding: utf-8 -*-
# Odoo, Open Source Itm Petty Cash.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import models, fields, api, _
from datetime import datetime as date
from odoo.exceptions import ValidationError, UserError, Warning
import logging
_logger = logging.getLogger("_name_")


# set journal in employee 
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    journal_id = fields.Many2one('account.journal', string='Account Journal',
                                 domain="[('type','=','general')]")

    #only account manager as custodian list 
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        context = self._context
        if args is None:
            args = []
        if 'set_custodian' in context:
            employee_ids = self.env['hr.employee'].search([])
            employee_list = []
            if employee_ids:
                for employee in employee_ids:
                    if employee.user_id:
                        employee_group = self.env.ref('account.group_account_manager')
                        has_user_id = self.env['res.users'].search([('id', '=', employee.user_id.id)], limit=1)
                        if has_user_id.groups_id:
                            for group in has_user_id.groups_id:
                                if employee_group.id == group.id:
                                    employee_list.append(employee.id)
                args += ([('id', 'in', employee_list)])
        return super(HrEmployee, self).name_search(name=name,
                                                   args=args,
                                                   operator=operator,
                                                   limit=limit)


# set petty cash in move line
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
     
    cash_id = fields.Many2one('petty.cash', string='Petty Cash')


# set petty cash in payment
class AccountPayment(models.Model):
    _inherit = 'account.payment'
     
    cash_id = fields.Many2one('petty.cash', string='Petty Cash')


#  petty cash    
class PettyCash(models.Model):
    _name = 'petty.cash'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']
     
    employee_id = fields.Many2one('hr.employee', string='Custodian', required=True)
    requested_employee_id = fields.Many2one('hr.employee', string='Requested By', required=True)
    petty_journal_id = fields.Many2one('account.journal', string='Petty Cash Journal',
                                       domain="[('type','in',['bank','cash'])]")
    petty_credit_account_id = fields.Many2one('account.account', string='Petty Cash Credit Account', readonly=True)
    petty_debit_account_id = fields.Many2one('account.account', string='Petty Cash Debit Account', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain="[('type','in',['bank','cash'])]", required=True)
    date_received = fields.Date(string='Date Received', default=date.today())
    petty_cash_line_ids = fields.One2many('petty.cash.line', 'cash_id', string='Petty Cash Line')  
    payment_line_ids = fields.One2many('account.payment', 'cash_id', string='Payment Line', readonly=True)  
    move_line_ids = fields.One2many('account.move.line', 'cash_id', string='Move Line', readonly=True)
    paid_amount_total = fields.Float(string='Paid Amount Total', compute='compute_amounttotal')
    petty_cash_balance = fields.Float(string='Petty Cash Balance', compute='compute_amounttotal')
    amount_received = fields.Float(string='Amount Received')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('cash_dispatch', 'Cash Dispatched'),
        ('to_reconcile', 'To Reconcile'),
        ('reconcile', 'Reconciled'),
        ], string='Status', readonly=True, default='draft')

    # create readonly fields into db 
    @api.model
    def create(self, vals):
        if 'requested_employee_id' in vals:
            requested_employee_id = self.env['hr.employee'].browse(vals.get('requested_employee_id'))
            if requested_employee_id:
                if not requested_employee_id.journal_id:
                    raise ValidationError(_('Please Set To Journal For This Requested By!'))
                else:
                    if not requested_employee_id.journal_id.default_debit_account_id:
                        raise ValidationError(_('Please Set To Default Account  For This Petty Cash Journal!'))
                    else:
                        vals.update({'petty_debit_account_id': requested_employee_id.journal_id.default_debit_account_id.id })
        if 'journal_id' in vals:
            journal_id = self.env['account.journal'].browse(vals.get('journal_id'))
            if journal_id:
                if journal_id.default_credit_account_id:
                    vals.update({'petty_credit_account_id': journal_id.default_credit_account_id.id})
                else:
                    raise ValidationError(_('Please Set to Default Account For This Payment Journal!'))
        return super(PettyCash, self).create(vals)
    
    # write readonly fields into db 
    def write(self, vals):
        if 'requested_employee_id' in vals :
            requested_employee_id = self.env['hr.employee'].browse(vals.get('requested_employee_id'))
            if requested_employee_id:
                if not requested_employee_id.journal_id:
                    raise ValidationError(_('Please Set To Journal For This Requested By!'))
                else:
                    if not requested_employee_id.journal_id.default_debit_account_id:
                        raise ValidationError(_('Please Set To Default Account  For This Petty Cash Journal!'))
                    else:
                        vals.update({'petty_debit_account_id': requested_employee_id.journal_id.default_debit_account_id.id })
        if 'journal_id' in vals:
            journal_id = self.env['account.journal'].browse(vals.get('journal_id'))
            if journal_id:
                if journal_id.default_credit_account_id:
                    vals.update({'petty_credit_account_id': journal_id.default_credit_account_id.id  })
                else:
                    raise ValidationError(_('Please Set to Default Account For This Payment Journal!'))     
        return super(PettyCash, self).write(vals)    

    # compute paid total and petty cash balance
    @api.depends('amount_received', 'petty_cash_line_ids.amount')
    def compute_amounttotal(self):
        line_amount = 0.0
        sub_total = 0.0
        for rec in self:
            total_amount = rec.amount_received
            for line in rec.petty_cash_line_ids:
                sub_total += line.amount
                if line.state == 'paid':
                    line_amount += line.amount
            rec.paid_amount_total = line_amount
            rec.petty_cash_balance = total_amount - sub_total
            if rec.state == 'reconcile':
                rec.petty_cash_balance = 0.0
    
    # set default account 
    @api.onchange('journal_id', 'requested_employee_id')
    def onchange_defualt_account(self):
        for rec in self:
            if not rec.journal_id and not rec.requested_employee_id:
                return
            # customer wise set debit account 
            if rec.requested_employee_id:
                if not rec.requested_employee_id.journal_id:
                    raise ValidationError(_('Please Set To Journal For This Requested By!'))
                else:
                    rec.petty_journal_id = rec.requested_employee_id.journal_id.id
                    if not rec.requested_employee_id.journal_id.default_debit_account_id:
                        raise ValidationError(_('Please Set To Default Account  For This Petty Cash Journal!'))
                    else:
                        rec.petty_debit_account_id = rec.requested_employee_id.journal_id.default_debit_account_id.id 
            # journal wise set credit account
            if rec.journal_id:
                if rec.journal_id.default_credit_account_id:
                    rec.petty_credit_account_id = rec.journal_id.default_credit_account_id.id 
                else:
                    raise ValidationError(_('Please Set to Default Account For This Payment Journal!'))     

    # request button method
    def do_request(self):
        for petty in self:
            petty.state = 'request'
            
    # request reconcile button method
    def do_to_reconcile(self):
        for petty in self:
            petty.state = 'to_reconcile'

    # Cash Dispatch button method
    def do_cash_dispatch(self):
        for petty in self:
            petty.state = 'cash_dispatch'
            _logger.info("\n\n\njournal_id {}".format(petty.journal_id))
            payment_methods = petty.journal_id.inbound_payment_method_ids or petty.journal_id.outbound_payment_method_ids
            payment_method_id = payment_methods and payment_methods[0] or False
            payment_id = self.env['account.payment'].create({
                'cash_id' : petty.id,
                'payment_type': 'transfer',
                'payment_date': petty.date_received,
                'company_id': self.requested_employee_id.company_id.id,
                'internal_transfer_type': 'journal_to_journal',
                'journal_id': petty.journal_id.id,
                'destination_journal_id': petty.petty_journal_id.id,
                'payment_method_id': payment_method_id.id,
                'amount':petty.amount_received,
                'communication':  self.env['ir.sequence'].next_by_code('petty.cash') or _('New')
                })
            ctx = dict(self._context)
            ctx.update({'custom_payment_id':payment_id.id})
            payment_id.with_context(ctx).post()
            move_line_id = self.env['account.move.line'].search([('payment_id', '=', payment_id.id)])
            move_line_id.write({'cash_id': petty.id})
        return 


# IrAttachment
class IrAttachment(models.Model):  
    _inherit = 'ir.attachment'

    cash_line_id = fields.Many2one('petty.cash.line', string='Petty Cash Line')


# petty cash line
class PettyCashLine(models.Model):  
    _name = 'petty.cash.line'  

    cash_id = fields.Many2one('petty.cash', string='Petty Cash')
    memo = fields.Char(string='Particulars', required=True)
    account_expense_id = fields.Many2one('account.account', string='Account Expense',
                                         domain="[('user_type_id','in',['Expenses'])]", required=True)
    date_maturity = fields.Date(string='Date', default=date.today())
    amount = fields.Float(string='Amount')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Account Analytic Tag')
    attachment_ids = fields.One2many('ir.attachment', 'cash_line_id', string='Bill Attachment')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Account Analytic')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ], string='Status', readonly=True, default='draft')
    pay_status = fields.Boolean(string='Pay Status', compute='compute_pay_status', default=False)
    
    # invisible pay button when to_reconcile and reconcile
    @api.depends('cash_id.state')
    def compute_pay_status(self):
        for rec in self:
            if rec.cash_id:
                if rec.cash_id.state == 'to_reconcile' or rec.cash_id.state == 'reconcile':
                    rec.pay_status = True
                else :
                    rec.pay_status = False

    # set remaining amount in line
    @api.model
    def default_get(self, vals):
        result = super(PettyCashLine, self).default_get(vals)
        context = self._context
        total_amount = 0.0
        if 'petty_cash_line_ids' in context:
            if 'cash_total_amount' in context:
                total_amount = context.get('cash_total_amount')
            cash_id = context.get('petty_cash_line_ids')
            if len(cash_id) != 0:
                sub_total = 0.0
                for rec in cash_id:
                    if rec[2] != False :
                        sub_total += rec[2]['amount']
                diff_amount = total_amount - sub_total
                result.update({'amount': diff_amount})
                if 'cash_id' in context:
                    get_cash_id = self.env['petty.cash'].browse(context.get('cash_id'))
                    if get_cash_id.petty_cash_line_ids:
                        for cash in get_cash_id.petty_cash_line_ids:
                            sub_total += cash.amount
                        diff_amount = total_amount - sub_total    
                        result.update({'amount': diff_amount})
            else:
                result.update({'amount': total_amount})
        return result
    
    # set validation for amount
    @api.onchange('amount')
    def onchange_amount(self):
        for rec in self:
            if rec.cash_id and rec.amount:
                if rec.amount > rec.cash_id.amount_received:
                    raise UserError(_('You Entered More Then Amount !'))

    #  Post button method
    def do_pay(self):
        for line in self:
            if line.cash_id.paid_amount_total == line.cash_id.amount_received:
                raise UserError(_('You Can Not Pay More Then Received Amount !'))
                
            line.state = 'paid'
            payment_methods = line.cash_id.petty_journal_id.inbound_payment_method_ids or line.cash_id.petty_journal_id.outbound_payment_method_ids
            payment_method_id = payment_methods and payment_methods[0] or False
            payment_id = self.env['account.payment'].create({
                'cash_id': line.cash_id.id,
                'payment_type': 'transfer',
                'payment_date': line.date_maturity,
                'internal_transfer_type': 'journal_to_account',
                'company_id': line.cash_id.requested_employee_id.company_id.id,
                'journal_id': line.cash_id.petty_journal_id.id,
                'destination_account_from_id': line.account_expense_id.id,
                'payment_method_id': payment_method_id.id,
                'amount': line.amount,
                'analytic_account_id': line.analytic_account_id.id or '',
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids) if line.analytic_tag_ids else []],
                'communication':  self.env['ir.sequence'].next_by_code('petty.cash') or _('New')
                })
            ctx = dict(self._context)
            ctx.update({'custom_payment_id': payment_id.id})
            payment_id.with_context(ctx).post()
            move_line_id = self.env['account.move.line'].search([('payment_id', '=', payment_id.id)])
            move_line_id.write({'cash_id': line.cash_id.id})
        return
