
from odoo import models, fields, api, _


# set analytic tag and account  in payment
class AccountPayment(models.Model):
    _inherit = 'account.payment'
     
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Account Analytic Tag')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Account Analytic')
    
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    # manage analytic line in move line
    def create_analytic_lines(self):
        context = self._context
        self.mapped('analytic_line_ids').unlink()
        for obj_line in self:
            if 'custom_payment_id' in context :
                payment_id = self.env['account.payment'].browse(context.get('custom_payment_id'))
                if payment_id.internal_transfer_type != 'journal_to_journal':
                    if payment_id.analytic_tag_ids or payment_id.analytic_account_id:
                        if payment_id.analytic_tag_ids :
                            obj_line.write({'analytic_tag_ids' :[(6, 0, payment_id.analytic_tag_ids.ids)]})
                        if payment_id.analytic_account_id :
                            obj_line.write({'analytic_account_id' :payment_id.analytic_account_id.id})
                            if obj_line.analytic_account_id:
                                vals_line = obj_line._prepare_analytic_line()[0]
                                self.env['account.analytic.line'].create(vals_line)
                    else:
                        return super(AccountMoveLine, self).create_analytic_lines()
                else:
                    return super(AccountMoveLine, self).create_analytic_lines()
            else:
                return super(AccountMoveLine, self).create_analytic_lines()
