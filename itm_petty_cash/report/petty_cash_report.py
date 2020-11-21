# -*- coding: utf-8 -*-
# Odoo, Open Source Itm Petty Cash.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).#

from odoo import api, models


#  sale order reports 
class ReportPettyCash(models.AbstractModel):
    _name = 'report.itm_petty_cash.petty_cash_template'
    
    def get_report_values(self, docids, data=None):
        cash_obj = self.env['petty.cash'].browse(docids[0])
        self.model = self.env.context.get('active_model')
        user = self.env["res.users"].browse(self._uid)
        company_data = user.company_id
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': cash_obj,
            'doc': user,
        }
        return docargs



