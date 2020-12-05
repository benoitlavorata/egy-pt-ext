from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payment_subtype = fields.Selection([('issue_check', _('Issued Checks')), ('rece_check', _('Received Checks'))],
                                       string="Payment Subtype")
